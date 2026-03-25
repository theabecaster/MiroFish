"""
认证中间件测试 — 验证MFBE-01和MFBE-05需求
测试覆盖：缺少令牌、无效令牌、有效令牌、健康检查豁免、非API路径豁免
"""


def test_missing_bearer_returns_401(client):
    """测试：缺少Bearer令牌时返回401"""
    response = client.get('/api/graph/tasks')
    assert response.status_code == 401
    data = response.get_json()
    assert data is not None
    assert data["success"] is False
    assert data["error"] == "Missing or invalid Authorization header"


def test_invalid_bearer_returns_401(client):
    """测试：提供无效Bearer令牌时返回401"""
    response = client.get('/api/graph/tasks', headers={"Authorization": "Bearer wrong-key"})
    assert response.status_code == 401
    data = response.get_json()
    assert data is not None
    assert data["success"] is False
    assert data["error"] == "Invalid API key"


def test_valid_bearer_passes(client, auth_headers):
    """测试：提供有效Bearer令牌时不返回401（认证层通过）"""
    response = client.get('/api/graph/tasks', headers=auth_headers)
    # 有效令牌应通过认证层 — 不返回401
    # 可能返回200、404或其他状态码，取决于路由实现
    assert response.status_code != 401


def test_health_exempt_from_auth(client):
    """测试：/health端点无需认证即可访问"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data["status"] == "ok"


def test_non_api_path_exempt(client):
    """测试：非/api/*路径不受Bearer令牌认证限制"""
    response = client.get('/some-other-path')
    # 没有认证头的非API路径不应该返回401
    assert response.status_code != 401


def test_existing_endpoints_with_auth(client, auth_headers):
    """测试：现有/api/graph端点在提供有效Bearer令牌时正常工作（MFBE-05）"""
    response = client.get('/api/graph/tasks', headers=auth_headers)
    # 有效认证后端点应正常响应（不被拒绝）
    assert response.status_code != 401
