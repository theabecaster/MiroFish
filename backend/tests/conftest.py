"""
测试配置和通用fixture
"""

import pytest

from app import create_app
from app.config import Config


class TestConfig(Config):
    """测试配置类 — 使用固定API密钥和测试模式"""
    TESTING = True
    DEBUG = False
    PREFLIGHT_API_KEY = "test-api-key-12345"
    # 覆盖Zep和LLM密钥以避免测试中的验证错误
    LLM_API_KEY = "test-llm-key"
    ZEP_API_KEY = "test-zep-key"


@pytest.fixture
def app():
    """创建Flask测试应用"""
    application = create_app(TestConfig)
    return application


@pytest.fixture
def client(app):
    """创建Flask测试客户端"""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """有效的Bearer令牌认证头"""
    return {"Authorization": "Bearer test-api-key-12345"}
