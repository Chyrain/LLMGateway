"""
LLMGateway API 单元测试
"""
import pytest
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """健康检查接口测试"""
    
    def test_root(self):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "灵模网关服务运行中"
    
    def test_health_check(self):
        """测试健康检查接口"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestAuthEndpoints:
    """认证接口测试"""
    
    def test_login_success(self):
        """测试登录成功"""
        response = client.post(
            "/api/auth/login",
            auth=("admin", "admin123")
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["username"] == "admin"
    
    def test_login_wrong_password(self):
        """测试密码错误"""
        response = client.post(
            "/api/auth/login",
            auth=("admin", "wrongpassword")
        )
        assert response.status_code == 401
    
    def test_login_wrong_username(self):
        """测试用户名错误"""
        response = client.post(
            "/api/auth/login",
            auth=("wronguser", "admin123")
        )
        assert response.status_code == 401
    
    def test_profile_without_token(self):
        """测试未授权访问"""
        response = client.get("/api/auth/profile")
        assert response.status_code == 401


class TestNotificationEndpoints:
    """通知接口测试"""
    
    def test_create_notification(self):
        """测试创建通知"""
        response = client.post(
            "/api/notifications",
            json={
                "title": "测试通知",
                "content": "这是一条测试通知",
                "type": "info"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["title"] == "测试通知"
    
    def test_list_notifications(self):
        """测试获取通知列表"""
        response = client.get("/api/notifications")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_unread_count(self):
        """测试获取未读数量"""
        response = client.get("/api/notifications/unread-count")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data


class TestStatsEndpoints:
    """统计接口测试"""
    
    def test_dashboard_stats(self):
        """测试仪表盘统计"""
        response = client.get("/api/stats/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "stats" in data
        assert "currentModel" in data
        assert "switchLogs" in data
        assert "alertModels" in data
    
    def test_usage_trend(self):
        """测试使用趋势"""
        response = client.get("/api/stats/usage", params={"days": 7})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "trend" in data
    
    def test_model_ranking(self):
        """测试模型排行"""
        response = client.get("/api/stats/models")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "rankings" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
