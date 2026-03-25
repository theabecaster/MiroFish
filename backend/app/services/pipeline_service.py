"""
流水线编排服务
将本体生成 → 图谱构建 → 模拟运行 → 报告生成串联为单一后台任务，
并在每个阶段转换时通过回调URL向Preflight推送状态更新。
"""

import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests as http_client

from ..config import Config
from ..models.project import ProjectManager, ProjectStatus
from ..models.task import TaskManager, TaskStatus
from ..services.graph_builder import GraphBuilderService
from ..services.ontology_generator import OntologyGenerator
from ..services.report_agent import ReportAgent, ReportManager
from ..services.simulation_manager import SimulationManager, SimulationStatus
from ..services.simulation_runner import SimulationRunner, RunnerStatus
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

# 各LLM提供商对应的OpenAI兼容接口基础URL（D-06）
PROVIDER_BASE_URLS: Dict[str, str] = {
    "openai":    "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "gemini":    "https://generativelanguage.googleapis.com/v1beta/openai",
}

# 轮询模拟完成的间隔（秒）和最大等待时长
_SIMULATION_POLL_INTERVAL = 10  # 秒
_SIMULATION_MAX_WAIT = 7200     # 2小时


def _provider_to_base_url(provider: str) -> str:
    """
    将提供商标识符映射为OpenAI兼容的base_url

    Args:
        provider: openai | anthropic | gemini，或直接传入base_url

    Returns:
        base_url字符串
    """
    url = PROVIDER_BASE_URLS.get(provider)
    if not url:
        get_logger('mirofish.pipeline').warning(
            f"未知的LLM提供商: {provider}，将直接使用作为base_url"
        )
        return provider
    return url


class PipelineService:
    """
    流水线编排服务

    将本体生成 → 图谱构建 → 模拟运行 → 报告生成串联为单一后台任务。
    在每个阶段转换时调用 callback_url 向Preflight推送进度（fire-and-forget，D-11）。
    使用用户请求体中携带的LLM API密钥（MFBE-03），而非服务器端 Config.LLM_API_KEY。
    """

    def __init__(
        self,
        task_id: str,
        seed_document: str,
        simulation_requirement: str,
        llm_api_key: str,
        llm_provider: str,
        llm_model: str,
        callback_url: str,
    ):
        """
        初始化流水线服务

        Args:
            task_id:               TaskManager中的任务ID
            seed_document:         Markdown格式的种子文档
            simulation_requirement: 模拟需求描述
            llm_api_key:           用户的LLM API密钥（来自请求体，MFBE-03）
            llm_provider:          openai | anthropic | gemini
            llm_model:             模型标识符，如 gpt-4o-mini
            callback_url:          Preflight回调端点URL
        """
        self.task_id = task_id
        self.seed_document = seed_document
        self.simulation_requirement = simulation_requirement
        self.callback_url = callback_url
        self.task_manager = TaskManager()
        self.logger = get_logger('mirofish.pipeline')

        # 使用用户的LLM密钥（D-06, MFBE-03）
        self.llm_client = LLMClient(
            api_key=llm_api_key,
            base_url=_provider_to_base_url(llm_provider),
            model=llm_model,
        )

        # 中间状态（各步骤产出的ID）
        self.project_id: Optional[str] = None
        self.graph_id: Optional[str] = None
        self.simulation_id: Optional[str] = None
        self.report_id: Optional[str] = None

    # ─────────────────────────────────────────────
    # 主入口
    # ─────────────────────────────────────────────

    def run(self):
        """
        顺序执行流水线的四个阶段。
        任何阶段抛出异常时调用 _fail()。
        """
        try:
            self._step_ontology()
            self._step_graph()
            self._step_simulate()
            self._step_report()
        except Exception as e:
            self.logger.error(
                f"[{self.task_id}] 流水线执行失败: {str(e)}\n{traceback.format_exc()}"
            )
            self._fail(str(e))

    # ─────────────────────────────────────────────
    # 回调辅助方法
    # ─────────────────────────────────────────────

    def _send_callback(
        self,
        stage: str,
        progress: int,
        sub_step: Optional[str] = None,
        estimated_time_remaining: Optional[int] = None,
        report: Optional[Any] = None,
        error: Optional[str] = None,
    ):
        """
        向 callback_url POST状态更新（D-10 payload schema，fire-and-forget per D-11）。

        回调失败时仅记录日志，不中断流水线。
        """
        payload = {
            "task_id":                   self.task_id,
            "stage":                     stage,
            "progress":                  progress,
            "estimated_time_remaining":  estimated_time_remaining,
            "sub_step":                  sub_step,
            "timestamp":                 datetime.now(timezone.utc).isoformat(),
            "report":                    report,
            "error":                     error,
        }
        try:
            resp = http_client.post(self.callback_url, json=payload, timeout=5)
            self.logger.debug(
                f"[{self.task_id}] 回调成功: stage={stage}, status={resp.status_code}"
            )
        except Exception as exc:
            # 回调失败不中断流水线（D-11 fire-and-forget）
            self.logger.warning(
                f"[{self.task_id}] 回调失败（已忽略）: stage={stage}, error={exc}"
            )

    def _update_and_notify(
        self,
        stage: str,
        progress: int,
        message: str,
        sub_step: Optional[str] = None,
        etr: Optional[int] = None,
        report: Optional[Any] = None,
        error: Optional[str] = None,
    ):
        """
        同时更新TaskManager状态并发送回调的辅助方法。
        """
        self.task_manager.update_task(
            self.task_id,
            status=TaskStatus.PROCESSING,
            progress=progress,
            message=message,
            progress_detail={"stage": stage, "sub_step": sub_step},
        )
        self._send_callback(stage, progress, sub_step, etr, report, error)

    # ─────────────────────────────────────────────
    # 步骤1：本体生成（0-25%）
    # ─────────────────────────────────────────────

    def _step_ontology(self):
        """
        步骤1：从 seed_document 生成知识图谱本体定义（0-25%）

        1. 通知阶段开始
        2. 创建项目，保存提取文本
        3. 调用 OntologyGenerator
        4. 将本体保存到项目
        5. 通知进度达到25%
        """
        self._update_and_notify(
            stage="generating_ontology",
            progress=5,
            message="开始生成本体定义...",
        )

        # 创建项目（名称包含task_id前8位，方便追踪）
        project = ProjectManager.create_project(
            name=f"pipeline_{self.task_id[:8]}"
        )
        self.project_id = project.project_id
        self.logger.info(f"[{self.task_id}] 创建项目: {self.project_id}")

        # 保存种子文档为提取文本（GraphBuilderService通过ProjectManager读取文本，研究Pitfall-2）
        project.simulation_requirement = self.simulation_requirement
        ProjectManager.save_project(project)
        ProjectManager.save_extracted_text(self.project_id, self.seed_document)

        # 生成本体（研究Pitfall-1：document_texts 必须是列表）
        self._update_and_notify(
            stage="generating_ontology",
            progress=10,
            message="调用LLM生成本体定义...",
        )

        generator = OntologyGenerator(llm_client=self.llm_client)
        ontology_result = generator.generate(
            document_texts=[self.seed_document],
            simulation_requirement=self.simulation_requirement,
        )

        # 保存本体到项目
        project.ontology = {
            "entity_types": ontology_result.get("entity_types", []),
            "edge_types":   ontology_result.get("edge_types", []),
        }
        project.analysis_summary = ontology_result.get("analysis_summary", "")
        project.status = ProjectStatus.ONTOLOGY_GENERATED
        ProjectManager.save_project(project)

        entity_count = len(project.ontology.get("entity_types", []))
        self.logger.info(
            f"[{self.task_id}] 本体生成完成: {entity_count} 个实体类型"
        )

        self._update_and_notify(
            stage="generating_ontology",
            progress=25,
            message=f"本体生成完成，包含 {entity_count} 个实体类型",
        )

    # ─────────────────────────────────────────────
    # 步骤2：图谱构建（25-50%）
    # ─────────────────────────────────────────────

    def _step_graph(self):
        """
        步骤2：在Zep中构建知识图谱（25-50%）

        图谱构建使用Zep API密钥（非用户LLM密钥，D-06）。
        复用与 graph.py build_task 相同的调用约定。
        """
        self._update_and_notify(
            stage="building_graph",
            progress=30,
            message="初始化图谱构建服务...",
        )

        # 获取项目和本体（上一步已保存）
        project = ProjectManager.get_project(self.project_id)
        ontology = project.ontology
        text = ProjectManager.get_extracted_text(self.project_id) or self.seed_document

        graph_name = f"pipeline_{self.task_id[:8]}"

        # 图谱构建使用Zep密钥（D-06，非用户LLM密钥）
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)

        # 分块
        from ..services.text_processor import TextProcessor
        chunks = TextProcessor.split_text(
            text,
            chunk_size=project.chunk_size or Config.DEFAULT_CHUNK_SIZE,
            overlap=project.chunk_overlap or Config.DEFAULT_CHUNK_OVERLAP,
        )

        self._update_and_notify(
            stage="building_graph",
            progress=33,
            message="在Zep中创建图谱...",
        )

        # 创建图谱
        graph_id = builder.create_graph(name=graph_name)
        self.graph_id = graph_id

        # 更新项目中的graph_id
        project.graph_id = graph_id
        project.status = ProjectStatus.GRAPH_BUILDING
        ProjectManager.save_project(project)

        # 设置本体
        builder.set_ontology(graph_id, ontology)

        self._update_and_notify(
            stage="building_graph",
            progress=36,
            message=f"向图谱添加 {len(chunks)} 个文本块...",
        )

        # 添加文本块（回调更新进度 36-45%）
        def add_progress_callback(msg, ratio):
            progress = 36 + int(ratio * 9)  # 36% - 45%
            self.task_manager.update_task(
                self.task_id,
                status=TaskStatus.PROCESSING,
                progress=progress,
                message=msg,
            )

        episode_uuids = builder.add_text_batches(
            graph_id,
            chunks,
            batch_size=3,
            progress_callback=add_progress_callback,
        )

        self._update_and_notify(
            stage="building_graph",
            progress=45,
            message="等待Zep处理数据...",
        )

        # 等待Zep处理完成（45-50%）
        def wait_progress_callback(msg, ratio):
            progress = 45 + int(ratio * 5)  # 45% - 50%
            self.task_manager.update_task(
                self.task_id,
                status=TaskStatus.PROCESSING,
                progress=progress,
                message=msg,
            )

        builder._wait_for_episodes(episode_uuids, wait_progress_callback)

        # 更新项目状态
        project.status = ProjectStatus.GRAPH_COMPLETED
        ProjectManager.save_project(project)

        self.logger.info(f"[{self.task_id}] 图谱构建完成: graph_id={graph_id}")

        self._update_and_notify(
            stage="building_graph",
            progress=50,
            message=f"图谱构建完成: {graph_id}",
        )

    # ─────────────────────────────────────────────
    # 步骤3：模拟运行（50-75%）
    # ─────────────────────────────────────────────

    def _step_simulate(self):
        """
        步骤3：准备并运行OASIS多智能体模拟（50-75%）

        研究Pitfall-3：必须完整执行 prepare_simulation + start_simulation + 轮询完成。
        OasisProfileGenerator 和 SimulationConfigGenerator 在 prepare_simulation 内部被调用。
        """
        self._update_and_notify(
            stage="simulating",
            progress=55,
            message="准备模拟环境...",
        )

        project = ProjectManager.get_project(self.project_id)

        # 创建模拟状态对象
        sim_manager = SimulationManager()
        sim_state = sim_manager.create_simulation(
            project_id=self.project_id,
            graph_id=self.graph_id,
            enable_twitter=True,
            enable_reddit=True,
        )
        self.simulation_id = sim_state.simulation_id
        self.logger.info(f"[{self.task_id}] 创建模拟: {self.simulation_id}")

        # 准备模拟（读取Zep实体 → 生成Agent人设 → 生成配置）
        def sim_progress_callback(stage, progress, message, **kwargs):
            # 映射 prepare 阶段进度到流水线 55-70%
            overall = 55 + int(progress * 0.15)
            self.task_manager.update_task(
                self.task_id,
                status=TaskStatus.PROCESSING,
                progress=overall,
                message=f"[模拟准备] {message}",
            )

        document_text = ProjectManager.get_extracted_text(self.project_id) or self.seed_document

        sim_manager.prepare_simulation(
            simulation_id=self.simulation_id,
            simulation_requirement=self.simulation_requirement,
            document_text=document_text,
            use_llm_for_profiles=True,
            progress_callback=sim_progress_callback,
        )

        self._update_and_notify(
            stage="simulating",
            progress=70,
            message="模拟环境准备完成，启动模拟...",
        )

        # 启动模拟进程
        SimulationRunner.start_simulation(
            simulation_id=self.simulation_id,
            platform="parallel",
        )
        self.logger.info(f"[{self.task_id}] 模拟进程已启动: {self.simulation_id}")

        # 轮询等待模拟完成（70-75%）
        elapsed = 0
        while elapsed < _SIMULATION_MAX_WAIT:
            run_state = SimulationRunner.get_run_state(self.simulation_id)
            if run_state is None:
                time.sleep(_SIMULATION_POLL_INTERVAL)
                elapsed += _SIMULATION_POLL_INTERVAL
                continue

            status = run_state.runner_status

            if status == RunnerStatus.COMPLETED:
                self.logger.info(f"[{self.task_id}] 模拟已完成")
                break

            if status == RunnerStatus.FAILED:
                error_msg = run_state.error or "模拟运行失败"
                raise RuntimeError(f"模拟失败: {error_msg}")

            if status in (RunnerStatus.STOPPED,):
                raise RuntimeError("模拟被手动停止")

            # 更新进度（保持在 70-74%，留一格给完成通知）
            progress = min(74, 70 + int(elapsed / _SIMULATION_MAX_WAIT * 4))
            self.task_manager.update_task(
                self.task_id,
                status=TaskStatus.PROCESSING,
                progress=progress,
                message=f"模拟运行中... 已用时 {elapsed // 60} 分钟",
            )

            time.sleep(_SIMULATION_POLL_INTERVAL)
            elapsed += _SIMULATION_POLL_INTERVAL
        else:
            raise TimeoutError(f"模拟超时（最大等待时长 {_SIMULATION_MAX_WAIT // 3600} 小时）")

        self._update_and_notify(
            stage="simulating",
            progress=75,
            message="模拟运行完成",
        )

    # ─────────────────────────────────────────────
    # 步骤4：报告生成（75-100%）
    # ─────────────────────────────────────────────

    def _step_report(self):
        """
        步骤4：使用 ReportAgent 生成分析报告（75-100%）

        ReportAgent 支持传入自定义 llm_client（使用用户密钥）。
        """
        self._update_and_notify(
            stage="generating_report",
            progress=80,
            message="初始化报告生成Agent...",
        )

        # 预生成 report_id（与 report.py 相同的模式）
        self.report_id = f"report_{uuid.uuid4().hex[:12]}"

        agent = ReportAgent(
            graph_id=self.graph_id,
            simulation_id=self.simulation_id,
            simulation_requirement=self.simulation_requirement,
            llm_client=self.llm_client,
        )

        def report_progress_callback(stage, progress, message):
            # 映射报告阶段进度到流水线 80-99%
            overall = 80 + int(progress * 0.19)
            self.task_manager.update_task(
                self.task_id,
                status=TaskStatus.PROCESSING,
                progress=overall,
                message=f"[报告生成] {message}",
            )

        report = agent.generate_report(
            progress_callback=report_progress_callback,
            report_id=self.report_id,
        )

        # 保存报告
        ReportManager.save_report(report)

        report_data = report.to_dict()
        self.logger.info(
            f"[{self.task_id}] 报告生成完成: report_id={self.report_id}"
        )

        # 发送完成回调（D-10：stage=complete，progress=100，report=report_data）
        self._send_callback(
            stage="complete",
            progress=100,
            report=report_data,
        )

        # 将任务标记为已完成
        self.task_manager.complete_task(
            self.task_id,
            result={
                "report_id":  self.report_id,
                "report":     report_data,
            },
        )

    # ─────────────────────────────────────────────
    # 失败处理
    # ─────────────────────────────────────────────

    def _fail(self, error_msg: str):
        """
        将任务标记为失败，并发送失败回调。
        """
        self.task_manager.fail_task(self.task_id, error_msg)

        # 获取最后已知进度用于回调
        task = self.task_manager.get_task(self.task_id)
        last_progress = task.progress if task else 0

        self._send_callback(
            stage="failed",
            progress=last_progress,
            error=error_msg,
        )
