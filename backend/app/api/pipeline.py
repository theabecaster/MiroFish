"""
流水线API路由
Preflight单次调用接口 — 将完整pipeline作为后台任务执行并通过回调上报进度
"""

import threading
import traceback
from flask import request, jsonify

from . import pipeline_bp
from ..models.task import TaskManager, TaskStatus
from ..services.pipeline_service import PipelineService
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.pipeline')

# 流水线请求必填字段
REQUIRED_FIELDS = [
    'seed_document',
    'simulation_requirement',
    'llm_api_key',
    'llm_provider',
    'llm_model',
    'callback_url',
]


# ============== 流水线启动接口 ==============

@pipeline_bp.route('', methods=['POST'])
def start_pipeline():
    """
    启动完整流水线（异步任务）

    接口立即返回task_id，后台依次执行：
    本体生成 → 图谱构建 → 模拟运行 → 报告生成

    每个阶段完成时通过 callback_url POST状态更新。

    请求（JSON）：
        {
            "seed_document":          "markdown格式的文档内容",
            "simulation_requirement": "模拟需求描述",
            "llm_api_key":            "用户的LLM API密钥",
            "llm_provider":           "openai|anthropic|gemini",
            "llm_model":              "gpt-4o-mini",
            "callback_url":           "http://preflight.app/api/callback"
        }

    返回：
        202 {
            "success": true,
            "data": { "task_id": "task_xxxx" }
        }
    """
    try:
        data = request.get_json() or {}

        # 验证必填字段
        missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
        if missing:
            return jsonify({
                "success": False,
                "error": f"缺少必需字段: {', '.join(missing)}"
            }), 400

        # 创建任务追踪条目
        task_manager = TaskManager()
        task_id = task_manager.create_task("pipeline")

        logger.info(f"[{task_id}] 流水线任务已创建，准备在后台执行")

        # 在后台线程中运行完整流水线
        def run_pipeline():
            service = PipelineService(
                task_id=task_id,
                seed_document=data['seed_document'],
                simulation_requirement=data['simulation_requirement'],
                llm_api_key=data['llm_api_key'],
                llm_provider=data['llm_provider'],
                llm_model=data['llm_model'],
                callback_url=data['callback_url'],
            )
            service.run()

        thread = threading.Thread(target=run_pipeline, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "data": {"task_id": task_id}
        }), 202

    except Exception as e:
        logger.error(f"启动流水线失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 流水线状态查询接口 ==============

@pipeline_bp.route('/status/<task_id>', methods=['GET'])
def get_pipeline_status(task_id: str):
    """
    查询流水线任务状态

    返回：
        {
            "success": true,
            "data": { ...task dict... }
        }
    """
    task = TaskManager().get_task(task_id)

    if not task:
        return jsonify({
            "success": False,
            "error": f"任务不存在: {task_id}"
        }), 404

    return jsonify({
        "success": True,
        "data": task.to_dict()
    }), 200
