"""
流水线端点和服务测试 — 验证MFBE-02、MFBE-03、MFBE-04需求
测试覆盖：202响应、缺少字段400、未认证401、LLM密钥来源、回调发送、回调失败容错、状态查询
"""

import json
import unittest.mock as mock
from unittest.mock import MagicMock, patch

import pytest


# ─────────────────────────────────────────────
# 测试数据
# ─────────────────────────────────────────────

VALID_PIPELINE_BODY = {
    "seed_document":          "# 测试文档\n这是一个测试种子文档。",
    "simulation_requirement": "测试模拟需求",
    "llm_api_key":            "test-llm-key",
    "llm_provider":           "openai",
    "llm_model":              "gpt-4o-mini",
    "callback_url":           "http://localhost:3000/api/callback",
}


# ─────────────────────────────────────────────
# 端点集成测试
# ─────────────────────────────────────────────

def test_pipeline_returns_202(client, auth_headers):
    """
    测试：POST /api/pipeline 提供全部6个必填字段及有效Bearer令牌时返回202并包含task_id
    验证MFBE-02：单次调用流水线
    """
    with patch('app.api.pipeline.PipelineService') as mock_service_cls:
        # 模拟PipelineService.run() 为无操作（不实际执行流水线）
        mock_instance = MagicMock()
        mock_instance.run = MagicMock()
        mock_service_cls.return_value = mock_instance

        response = client.post(
            '/api/pipeline',
            json=VALID_PIPELINE_BODY,
            headers=auth_headers,
        )

    assert response.status_code == 202, f"期望202，实际 {response.status_code}"
    data = response.get_json()
    assert data is not None
    assert data["success"] is True
    assert "task_id" in data["data"]
    assert data["data"]["task_id"]  # 非空


def test_pipeline_missing_field_returns_400(client, auth_headers):
    """
    测试：POST /api/pipeline 缺少 seed_document 时返回400并包含字段名
    """
    body = dict(VALID_PIPELINE_BODY)
    del body["seed_document"]

    response = client.post(
        '/api/pipeline',
        json=body,
        headers=auth_headers,
    )

    assert response.status_code == 400, f"期望400，实际 {response.status_code}"
    data = response.get_json()
    assert data["success"] is False
    assert "seed_document" in data["error"]


def test_pipeline_no_auth_returns_401(client):
    """
    测试：POST /api/pipeline 不提供Bearer令牌时返回401
    """
    response = client.post(
        '/api/pipeline',
        json=VALID_PIPELINE_BODY,
    )
    assert response.status_code == 401


def test_pipeline_uses_request_llm_key(client, auth_headers):
    """
    测试：PipelineService初始化时使用请求体中的 llm_api_key，而非 Config.LLM_API_KEY
    验证MFBE-03：用户自带LLM密钥
    """
    captured_kwargs = {}

    def capture_init(self, **kwargs):
        captured_kwargs.update(kwargs)
        # 需要初始化足够的属性以使 route 可以创建实例
        self.task_id = kwargs.get('task_id', '')
        self.seed_document = kwargs.get('seed_document', '')
        self.simulation_requirement = kwargs.get('simulation_requirement', '')
        self.callback_url = kwargs.get('callback_url', '')
        self.llm_client = MagicMock()
        self.task_manager = MagicMock()
        self.logger = MagicMock()
        self.project_id = None
        self.graph_id = None
        self.simulation_id = None
        self.report_id = None

    with patch('app.api.pipeline.PipelineService') as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run = MagicMock()
        mock_cls.return_value = mock_instance

        client.post(
            '/api/pipeline',
            json=VALID_PIPELINE_BODY,
            headers=auth_headers,
        )

        # 验证 PipelineService 被以正确的 llm_api_key 实例化
        assert mock_cls.called, "PipelineService 应该被调用"
        call_kwargs = mock_cls.call_args[1] if mock_cls.call_args[1] else {}
        call_args = mock_cls.call_args[0] if mock_cls.call_args[0] else ()

        # 统一处理位置参数和关键字参数
        all_kwargs = {
            **{k: v for k, v in zip(
                ['task_id', 'seed_document', 'simulation_requirement',
                 'llm_api_key', 'llm_provider', 'llm_model', 'callback_url'],
                call_args
            )},
            **call_kwargs,
        }

        assert all_kwargs.get('llm_api_key') == "test-llm-key", (
            f"PipelineService 应使用请求体中的 llm_api_key，实际参数: {all_kwargs}"
        )


def test_pipeline_status_endpoint(client, auth_headers):
    """
    测试：创建任务后 GET /api/pipeline/status/<task_id> 返回任务数据
    """
    from app.models.task import TaskManager

    # 先创建一个任务
    task_manager = TaskManager()
    task_id = task_manager.create_task("pipeline_test")

    response = client.get(
        f'/api/pipeline/status/{task_id}',
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "task_id" in data["data"] or data["data"] is not None


def test_pipeline_status_not_found(client, auth_headers):
    """
    测试：GET /api/pipeline/status/nonexistent 返回404
    """
    response = client.get(
        '/api/pipeline/status/nonexistent-task-id-xyz',
        headers=auth_headers,
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False


# ─────────────────────────────────────────────
# PipelineService 单元测试
# ─────────────────────────────────────────────

def _make_service(**overrides):
    """
    创建一个用于单元测试的 PipelineService 实例（不实际执行外部调用）
    """
    from app.services.pipeline_service import PipelineService

    kwargs = dict(
        task_id="task_unit_test_001",
        seed_document="# 测试",
        simulation_requirement="测试需求",
        llm_api_key="test-key",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        callback_url="http://localhost:3000/api/callback",
    )
    kwargs.update(overrides)

    with patch('app.services.pipeline_service.LLMClient'):
        with patch('app.services.pipeline_service.TaskManager'):
            service = PipelineService(**kwargs)
            # 覆盖 task_manager 为 mock
            service.task_manager = MagicMock()
            service.logger = MagicMock()
            return service


def test_callback_sent_on_stage():
    """
    测试：_send_callback 发送包含 task_id、stage、progress、timestamp 字段的载荷
    验证MFBE-04：每个阶段转换时发送回调
    """
    service = _make_service()

    with patch('app.services.pipeline_service.http_client') as mock_http:
        mock_http.post = MagicMock()
        service._send_callback(stage="generating_ontology", progress=5)

    # 验证 http_client.post 被调用
    assert mock_http.post.called, "应调用 http_client.post"

    call_kwargs = mock_http.post.call_args
    payload = call_kwargs[1]['json'] if call_kwargs[1] else call_kwargs[0][1]

    assert payload["task_id"] == "task_unit_test_001"
    assert payload["stage"] == "generating_ontology"
    assert payload["progress"] == 5
    assert "timestamp" in payload


def test_callback_failure_is_ignored():
    """
    测试：当 http_client.post 抛出 ConnectionError 时，_send_callback 不向外传播异常
    验证MFBE-04：回调失败不中断流水线（D-11 fire-and-forget）
    """
    service = _make_service()

    with patch('app.services.pipeline_service.http_client') as mock_http:
        mock_http.post = MagicMock(side_effect=ConnectionError("连接失败"))
        # 不应抛出异常
        try:
            service._send_callback(stage="simulating", progress=55)
        except Exception as exc:
            pytest.fail(f"_send_callback 不应抛出异常，但抛出了: {exc}")
