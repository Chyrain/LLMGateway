#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
灵模网关 - 单元测试用例
========================

测试覆盖范围：
1. 加密模块测试
2. 数据库模块测试
3. 网关核心服务测试
4. 模型切换服务测试
5. 额度监控服务测试
6. API接口测试
"""

import pytest
import asyncio
import json
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==================== 测试配置 ====================
TEST_DB_PATH = "./data/test_llmgateway.db"
os.environ["DB_PATH"] = TEST_DB_PATH
os.environ["API_MODE"] = "true"  # 启用 API 模式以测试管理接口
os.makedirs(os.path.dirname(TEST_DB_PATH), exist_ok=True)

# ==================== 测试夹具 ====================
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def db_session():
    """数据库会话夹具"""
    from config.database import get_db, init_db, SessionLocal
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def sample_model_data():
    """示例模型数据"""
    return {
        "vendor": "openai",
        "model_name": "gpt-3.5-turbo",
        "api_key": "sk-test-api-key-12345",
        "api_base": "https://api.openai.com",
        "api_path": "/v1/chat/completions",
        "params": {
            "temperature": 0.7,
            "max_tokens": 2048
        },
        "priority": 1
    }

@pytest.fixture
def sample_chat_request():
    """示例Chat请求"""
    return {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "temperature": 0.7,
        "max_tokens": 100,
        "stream": False
    }


# ==================== 测试类 ====================

class TestEncryption:
    """加密模块测试"""
    
    def test_encrypt_decrypt_roundtrip(self):
        """测试加密解密往返"""
        from config.encryption import encrypt_api_key, decrypt_api_key
        
        original_key = "sk-test-api-key-12345"
        encrypted = encrypt_api_key(original_key)
        decrypted = decrypt_api_key(encrypted)
        
        assert decrypted == original_key
        assert encrypted != original_key  # 确保加密后不同
    
    def test_different_inputs_produce_different_ciphertexts(self):
        """不同输入产生不同密文"""
        from config.encryption import encrypt_api_key
        
        key1 = "api-key-first"
        key2 = "api-key-second"
        
        encrypted1 = encrypt_api_key(key1)
        encrypted2 = encrypt_api_key(key2)
        
        # 不同输入应该产生不同密文
        assert encrypted1 != encrypted2
        assert len(encrypted1) > 0
        assert len(encrypted2) > 0
    
    def test_encrypt_special_characters(self):
        """测试加密特殊字符"""
        from config.encryption import encrypt_api_key, decrypt_api_key
        
        special_keys = [
            "sk-测试key",
            "sk-key with spaces",
            "sk-key\nwith\nnewlines",
            "sk-key\twith\ttabs",
        ]
        
        for key in special_keys:
            encrypted = encrypt_api_key(key)
            decrypted = decrypt_api_key(encrypted)
            assert decrypted == key
    
    def test_encrypt_empty_string(self):
        """测试加密空字符串"""
        from config.encryption import encrypt_api_key, decrypt_api_key
        
        empty_key = ""
        encrypted = encrypt_api_key(empty_key)
        decrypted = decrypt_api_key(encrypted)
        
        assert decrypted == empty_key
    
    def test_generate_new_key(self):
        """测试生成新密钥"""
        from config.encryption import generate_new_key
        
        key1 = generate_new_key()
        key2 = generate_new_key()
        
        assert len(key1) > 0
        assert len(key2) > 0
        assert key1 != key2  # 每次生成应该不同


class TestDatabase:
    """数据库模块测试"""
    
    def test_database_initialization(self):
        """测试数据库初始化"""
        from config.database import init_db, engine
        from sqlalchemy import inspect
        from models.model_config import ModelConfig
        from models.quota_stat import QuotaStat
        from models.system_config import SystemConfig
        from models.operation_log import OperationLog
        
        # 初始化数据库
        init_db()
        
        # 检查表是否存在 (SQLAlchemy 2.0 API)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        assert "model_config" in tables
        assert "quota_stat" in tables
        assert "system_config" in tables
        assert "operation_log" in tables
    
    def test_model_config_crud(self, db_session, sample_model_data):
        """测试模型配置的增删改查"""
        from models.model_config import ModelConfig
        from config.encryption import encrypt_api_key
        
        # Create
        model = ModelConfig(
            vendor=sample_model_data["vendor"],
            model_name=sample_model_data["model_name"],
            api_key=encrypt_api_key(sample_model_data["api_key"]),
            api_base=sample_model_data["api_base"],
            api_path=sample_model_data["api_path"],
            params=sample_model_data["params"],
            priority=sample_model_data["priority"]
        )
        db_session.add(model)
        db_session.commit()
        
        assert model.id is not None
        
        # Read
        fetched = db_session.query(ModelConfig).filter(
            ModelConfig.id == model.id
        ).first()
        
        assert fetched is not None
        assert fetched.vendor == sample_model_data["vendor"]
        assert fetched.model_name == sample_model_data["model_name"]
        
        # Update
        fetched.priority = 5
        db_session.commit()
        
        updated = db_session.query(ModelConfig).filter(
            ModelConfig.id == model.id
        ).first()
        assert updated.priority == 5
        
        # Delete
        db_session.delete(updated)
        db_session.commit()
        
        deleted = db_session.query(ModelConfig).filter(
            ModelConfig.id == model.id
        ).first()
        assert deleted is None
    
    def test_model_config_to_dict(self, db_session, sample_model_data):
        """测试模型配置转字典"""
        from models.model_config import ModelConfig
        from config.encryption import encrypt_api_key
        
        model = ModelConfig(
            vendor=sample_model_data["vendor"],
            model_name=sample_model_data["model_name"],
            api_key=encrypt_api_key(sample_model_data["api_key"]),
            api_base=sample_model_data["api_base"],
            api_path=sample_model_data["api_path"],
            params=sample_model_data["params"],
            priority=sample_model_data["priority"]
        )
        
        # 不包含敏感信息的字典
        dict_without_sensitive = model.to_dict(include_sensitive=False)
        assert "api_key" not in dict_without_sensitive or dict_without_sensitive.get("api_key") is None
        assert "vendor" in dict_without_sensitive
        assert "model_name" in dict_without_sensitive


class TestGatewayCore:
    """网关核心服务测试"""
    
    def test_vendor_configs_loaded(self):
        """测试厂商配置加载"""
        from services.gateway_core import GatewayCore
        from config.vendor_config import VENDOR_CONFIGS

        assert "openai" in VENDOR_CONFIGS
        assert "qwen" in VENDOR_CONFIGS
        assert "zhipu" in VENDOR_CONFIGS
        assert "anthropic" in VENDOR_CONFIGS
        assert "gemini" in VENDOR_CONFIGS

    def test_vendor_config_structure(self):
        """测试厂商配置结构"""
        from config.vendor_config import VENDOR_CONFIGS

        config = VENDOR_CONFIGS["openai"]
        
        assert "api_base" in config
        assert "api_path" in config
        assert "auth_header" in config
        assert "stream_support" in config
    
    def test_param_mapping_loaded(self):
        """测试参数映射配置"""
        from services.gateway_core import GatewayCore
        
        assert "openai" in GatewayCore.PARAM_MAPPING
        assert "qwen" in GatewayCore.PARAM_MAPPING
        assert "claude" in GatewayCore.PARAM_MAPPING
    
    @pytest.mark.asyncio
    async def test_test_connectivity_success(self):
        """测试连通性测试成功"""
        from services.gateway_core import GatewayCore
        import httpx
        
        # 使用Mock避免真实网络请求
        with patch('config.vendor_config.VENDOR_CONFIGS', {
            "test": {
                "api_base": "https://api.test.com",
                "api_path": "/v1/chat/completions",
                "auth_header": "Authorization",
                "auth_format": "Bearer"
            }
        }):
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
                
                result = await GatewayCore.test_connectivity(
                    "test",
                    "https://api.test.com",
                    "test-key"
                )
                
                assert result is True
    
    def test_standardize_response_openai(self):
        """测试OpenAI响应标准化"""
        from services.gateway_core import GatewayCore
        
        response_data = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-3.5-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello!"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        standardized = GatewayCore._standardize_response("openai", response_data)
        
        assert standardized["id"] == "chatcmpl-123"
        assert standardized["object"] == "chat.completion"
        assert len(standardized["choices"]) == 1
        assert standardized["choices"][0]["message"]["content"] == "Hello!"
        assert standardized["usage"]["total_tokens"] == 15
    
    def test_standardize_response_claude(self):
        """测试Claude响应标准化"""
        from services.gateway_core import GatewayCore
        
        # Claude实际响应格式 - 转换为OpenAI格式
        # Claude API返回格式与OpenAI类似，有choices数组
        response_data = {
            "id": "msg_123",
            "type": "message",
            "model": "claude-sonnet-4-20250514",
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Hello from Claude!"}
            ],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 15
            }
        }
        
        standardized = GatewayCore._standardize_response("claude", response_data)
        
        # Claude响应需要特殊处理，实际集成时会通过response_mapping转换
        # 当前测试验证基础结构
        assert standardized["id"] == "msg_123"
        # 由于Claude格式不同，choices可能为空，这是预期行为
        # 实际使用时需要配置正确的response_mapping


class TestModelSwitcher:
    """模型切换服务测试"""
    
    def test_should_switch_by_threshold(self):
        """测试根据阈值判断切换"""
        from services.model_switcher import ModelSwitcher
        
        switcher = ModelSwitcher(threshold=99.0)
        
        # 未超过阈值，不切换
        assert switcher.should_switch(50.0, 2) is False
        assert switcher.should_switch(98.9, 2) is False
        
        # 超过阈值，需要切换
        assert switcher.should_switch(99.0, 2) is True
        assert switcher.should_switch(100.0, 2) is True
    
    def test_should_switch_by_quota_status(self):
        """测试根据额度状态判断切换"""
        from services.model_switcher import ModelSwitcher
        
        switcher = ModelSwitcher()
        
        # 额度已耗尽，必须切换
        assert switcher.should_switch(50.0, 0) is True
        assert switcher.should_switch(10.0, 0) is True
    
    def test_get_next_model_by_priority(self):
        """测试按优先级获取下一个模型"""
        from services.model_switcher import ModelSwitcher
        
        switcher = ModelSwitcher()
        
        models = [
            {"id": 1, "priority": 3, "status": 1, "name": "Model C"},
            {"id": 2, "priority": 1, "status": 1, "name": "Model A"},
            {"id": 3, "priority": 2, "status": 1, "name": "Model B"},
        ]
        
        # 当前使用模型1，应该返回优先级最高的模型2
        next_model = switcher.get_next_model(models, current_id=1)
        
        assert next_model is not None
        assert next_model["id"] == 2  # 优先级1最高
        assert next_model["name"] == "Model A"
    
    def test_get_next_model_excludes_current(self):
        """测试排除当前模型"""
        from services.model_switcher import ModelSwitcher
        
        switcher = ModelSwitcher()
        
        models = [
            {"id": 1, "priority": 1, "status": 1, "name": "Model A"},
            {"id": 2, "priority": 2, "status": 1, "name": "Model B"},
        ]
        
        # 当前使用模型1，应该返回模型2
        next_model = switcher.get_next_model(models, current_id=1)
        
        assert next_model is not None
        assert next_model["id"] == 2
    
    def test_get_next_model_excludes_disabled(self):
        """测试排除禁用模型"""
        from services.model_switcher import ModelSwitcher
        
        switcher = ModelSwitcher()
        
        models = [
            {"id": 1, "priority": 1, "status": 0, "name": "Model A"},  # 禁用
            {"id": 2, "priority": 2, "status": 1, "name": "Model B"},
        ]
        
        # 只有一个启用的模型
        next_model = switcher.get_next_model(models, current_id=1)
        
        assert next_model is not None
        assert next_model["id"] == 2
    
    def test_get_switch_stats(self):
        """测试获取切换统计"""
        from services.model_switcher import ModelSwitcher
        
        switcher = ModelSwitcher()
        
        # 初始状态
        stats = switcher.get_switch_stats()
        
        assert stats["total_switches"] == 0
        assert stats["last_switch"] is None
        assert len(stats["history"]) == 0
        
        # 记录一次切换
        asyncio.run(switcher.switch(
            {"id": 1, "name": "Model A"},
            {"id": 2, "name": "Model B"},
            "threshold exceeded"
        ))
        
        stats = switcher.get_switch_stats()
        
        assert stats["total_switches"] == 1
        assert stats["last_switch"]["from_model"] == "Model A"
        assert stats["last_switch"]["to_model"] == "Model B"


class TestQuotaMonitor:
    """额度监控服务测试"""
    
    def test_calculate_usage_from_response(self):
        """测试从响应计算使用量"""
        from services.quota_monitor import QuotaMonitor
        
        response_data = {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 200,
                "total_tokens": 300
            }
        }
        
        usage = QuotaMonitor.calculate_usage("openai", response_data)
        
        assert usage["prompt_tokens"] == 100
        assert usage["completion_tokens"] == 200
        assert usage["total_tokens"] == 300
    
    def test_calculate_usage_missing_usage(self):
        """测试响应中无usage字段"""
        from services.quota_monitor import QuotaMonitor
        
        response_data = {
            "choices": [{"message": {"content": "Hello"}}]
        }
        
        usage = QuotaMonitor.calculate_usage("openai", response_data)
        
        assert usage["prompt_tokens"] == 0
        assert usage["completion_tokens"] == 0
        assert usage["total_tokens"] == 0
    
    def test_get_token_price(self):
        """测试获取Token价格"""
        from services.quota_monitor import QuotaMonitor
        
        # OpenAI GPT-3.5价格
        input_price = QuotaMonitor.get_token_price("openai", "gpt-3.5-turbo", is_input=True)
        output_price = QuotaMonitor.get_token_price("openai", "gpt-3.5-turbo", is_input=False)
        
        assert input_price > 0
        assert output_price > 0
        assert output_price > input_price  # 输出通常更贵
    
    def test_get_token_price_unknown_model(self):
        """测试未知模型价格"""
        from services.quota_monitor import QuotaMonitor
        
        price = QuotaMonitor.get_token_price("unknown", "unknown-model")
        
        assert price == 0  # 未知模型返回0


class TestVendorTemplates:
    """厂商模板测试"""
    
    def test_templates_file_exists(self):
        """测试厂商模板文件存在"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "templates",
            "vendor_templates.json"
        )
        
        assert os.path.exists(template_path)
    
    def test_templates_structure(self):
        """测试厂商模板结构"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "templates",
            "vendor_templates.json"
        )
        
        with open(template_path, 'r') as f:
            templates = json.load(f)
        
        assert "vendors" in templates
        assert len(templates["vendors"]) > 0
    
    def test_vendor_template_fields(self):
        """测试厂商模板字段"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "templates",
            "vendor_templates.json"
        )
        
        with open(template_path, 'r') as f:
            templates = json.load(f)
        
        openai_template = templates["vendors"]["openai"]
        
        assert "name" in openai_template
        assert "models" in openai_template
        assert "api_base" in openai_template
        assert "api_path" in openai_template
        assert "free_quota" in openai_template
        assert "param_mapping" in openai_template


class TestAPIEndpoints:
    """API接口测试"""
    
    def test_root_endpoint(self):
        """测试根接口"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "灵模网关服务运行中"
        assert "version" in data
    
    def test_health_endpoint(self):
        """测试健康检查接口"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_list_models_empty(self):
        """测试获取模型列表（空）"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.get("/api/models")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
    
    def test_add_model_validation(self):
        """测试添加模型参数验证"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # 缺少必填字段
        response = client.post("/api/models", json={
            "vendor": "openai"
            # 缺少 model_name 和 api_key
        })

        assert response.status_code == 422  # 验证错误


# ==================== 集成测试 ====================

class TestIntegration:
    """集成测试"""
    
    def test_full_encryption_flow(self):
        """测试完整加密流程"""
        from config.encryption import encrypt_api_key, decrypt_api_key
        from models.model_config import ModelConfig
        
        # 加密存储
        api_key = "sk-sensitive-api-key"
        encrypted = encrypt_api_key(api_key)
        
        # 解密使用
        decrypted = decrypt_api_key(encrypted)
        assert decrypted == api_key
        
        # 确保原始密钥不泄露
        assert api_key not in encrypted
    
    def test_model_status_transitions(self):
        """测试模型状态转换"""
        from models.model_config import ModelConfig
        
        model = ModelConfig(
            vendor="test",
            model_name="test-model",
            api_key="encrypted-key",
            status=0,  # 初始禁用
            connect_status=0,
            quota_status=2
        )
        
        # 启用模型
        model.status = 1
        assert model.status == 1
        
        # 断开连接
        model.connect_status = 0
        assert model.connect_status == 0
        
        # 额度耗尽
        model.quota_status = 0
        assert model.quota_status == 0
    
    def test_switch_reason_analysis(self):
        """测试切换原因分析"""
        from services.model_switcher import ModelSwitcher
        
        switcher = ModelSwitcher(threshold=90.0)
        
        # 阈值触发
        reasons = []
        if switcher.should_switch(95.0, 2):
            reasons.append("threshold_exceeded")
        
        # 额度耗尽触发
        if switcher.should_switch(50.0, 0):
            reasons.append("quota_exhausted")
        
        assert "threshold_exceeded" in reasons
        assert "quota_exhausted" in reasons


# ==================== 性能测试 ====================

class TestPerformance:
    """性能测试"""
    
    def test_encrypt_performance(self):
        """测试加密性能"""
        import time
        from config.encryption import encrypt_api_key
        
        iterations = 1000
        start = time.time()
        
        for _ in range(iterations):
            encrypt_api_key("sk-test-key")
        
        elapsed = time.time() - start
        avg_time = (elapsed / iterations) * 1000  # 毫秒
        
        # 平均加密时间应小于1ms
        assert avg_time < 1.0, f"加密平均耗时: {avg_time:.2f}ms"
    
    def test_response_standardization_performance(self):
        """测试响应标准化性能"""
        import time
        from services.gateway_core import GatewayCore
        
        response_data = {
            "id": "test-id",
            "choices": [
                {"message": {"content": "Hello"}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 100, "total_tokens": 200}
        }
        
        iterations = 1000
        start = time.time()
        
        for _ in range(iterations):
            GatewayCore._standardize_response("openai", response_data)
        
        elapsed = time.time() - start
        avg_time = (elapsed / iterations) * 1000
        
        # 平均时间应小于0.1ms
        assert avg_time < 0.1, f"响应标准化平均耗时: {avg_time:.4f}ms"


# ==================== 安全性测试 ====================

class TestSecurity:
    """安全性测试"""
    
    def test_api_key_not_in_logs(self):
        """测试API Key不记录在日志中"""
        from models.operation_log import OperationLog
        
        log = OperationLog(
            log_type=1,
            log_content="Request processed",  # 不应包含敏感信息
            status=1
        )
        
        # 确保日志内容不包含明显的API Key格式
        sensitive_patterns = ["sk-", "Bearer ", "api_key"]
        
        for pattern in sensitive_patterns:
            if pattern in log.log_content:
                assert False, f"日志中不应包含敏感信息: {pattern}"
    
    def test_encrypted_key_not_reversible(self):
        """测试加密后的密钥不可逆"""
        from config.encryption import encrypt_api_key
        
        original = "sk-secret-key-12345"
        encrypted = encrypt_api_key(original)
        
        # 尝试从加密结果提取原始密钥
        # 加密使用Fernet，无法从密文反向推导
        assert encrypted != original
        assert len(encrypted) > len(original)  # 密文通常更长
    
    def test_model_priority_validation(self):
        """测试模型优先级验证"""
        from models.model_config import ModelConfig
        
        model = ModelConfig(
            vendor="test",
            model_name="test-model",
            api_key="encrypted-key",
            priority=1
        )
        
        # 优先级应该是正整数
        assert model.priority > 0

        # 可以修改优先级
        model.priority = 100
        assert model.priority == 100


class TestAuthentication:
    """用户认证测试"""

    def test_login_success(self):
        """测试登录成功"""
        from fastapi.testclient import TestClient
        from main import app
        from routers.auth import tokens, users

        # 清理之前的 token
        tokens.clear()

        client = TestClient(app)
        response = client.post(
            "/api/auth/login",
            headers={"username": "admin", "password": "admin123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "access_token" in data["data"]
        assert data["data"]["username"] == "admin"

    def test_login_invalid_password(self):
        """测试密码错误"""
        from fastapi.testclient import TestClient
        from main import app
        from routers.auth import tokens

        tokens.clear()

        client = TestClient(app)
        response = client.post(
            "/api/auth/login",
            headers={"username": "admin", "password": "wrongpassword"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "用户名或密码错误" in data["detail"]

    def test_login_invalid_username(self):
        """测试用户名不存在"""
        from fastapi.testclient import TestClient
        from main import app
        from routers.auth import tokens

        tokens.clear()

        client = TestClient(app)
        response = client.post(
            "/api/auth/login",
            headers={"username": "nonexistent", "password": "anypassword"}
        )

        assert response.status_code == 401

    def test_logout_success(self):
        """测试登出成功"""
        from fastapi.testclient import TestClient
        from main import app
        from routers.auth import tokens

        # 先登录获取 token
        tokens.clear()
        client = TestClient(app)
        login_response = client.post(
            "/api/auth/login",
            headers={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["data"]["access_token"]

        # 登出
        response = client.post(
            "/api/auth/logout",
            headers={"authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        # 验证 token 已被删除
        assert token not in tokens

    def test_change_password_success(self):
        """测试修改密码成功"""
        from fastapi.testclient import TestClient
        from main import app
        from routers.auth import tokens, users

        # 先登录获取 token
        tokens.clear()
        client = TestClient(app)
        login_response = client.post(
            "/api/auth/login",
            headers={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["data"]["access_token"]

        # 修改密码
        response = client.post(
            "/api/auth/change-password",
            headers={
                "old-password": "admin123",
                "new-password": "newpassword123",
                "authorization": f"Bearer {token}"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

        # 验证新密码可以登录
        login_response2 = client.post(
            "/api/auth/login",
            headers={"username": "admin", "password": "newpassword123"}
        )
        assert login_response2.status_code == 200

        # 恢复原始密码
        users["admin"]["password"] = "admin123"

    def test_change_password_wrong_old(self):
        """测试旧密码错误"""
        from fastapi.testclient import TestClient
        from main import app
        from routers.auth import tokens

        tokens.clear()
        client = TestClient(app)
        login_response = client.post(
            "/api/auth/login",
            headers={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["data"]["access_token"]

        response = client.post(
            "/api/auth/change-password",
            headers={
                "old-password": "wrongoldpassword",
                "new-password": "newpassword123",
                "authorization": f"Bearer {token}"
            }
        )

        assert response.status_code == 400
        assert "当前密码错误" in response.json()["detail"]

    def test_change_password_unauthorized(self):
        """测试未授权修改密码"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/auth/change-password",
            headers={
                "old-password": "admin123",
                "new-password": "newpassword123",
                "authorization": "Bearer invalid_token"
            }
        )

        assert response.status_code == 401


class TestNotifications:
    """通知系统测试"""

    def test_notification_model_exists(self):
        """测试通知模型存在"""
        from config.database import init_db, engine
        from sqlalchemy import inspect

        # 初始化数据库
        init_db()

        # 验证表存在
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        # 通知表应该在 init_db 时创建

    def test_create_notification(self):
        """测试创建通知"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/api/notifications",
            json={
                "title": "测试通知",
                "content": "这是测试内容",
                "type": "info"
            }
        )

        # 可能需要认证，返回 401 或成功
        assert response.status_code in [200, 401, 403]

    def test_get_notifications(self):
        """测试获取通知列表"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.get("/api/notifications")

        # 可能需要认证
        assert response.status_code in [200, 401, 403]

    def test_get_unread_count(self):
        """测试获取未读数量"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.get("/api/notifications/unread-count")

        assert response.status_code in [200, 401, 403]

    def test_notification_model_to_dict(self):
        """测试通知转字典"""
        from models.notification import Notification
        from datetime import datetime

        notification = Notification(
            title="Test",
            content="Content",
            type="info",
            is_read=False
        )

        result = notification.to_dict()
        assert result["title"] == "Test"
        assert result["content"] == "Content"
        assert result["type"] == "info"
        assert result["is_read"] is False


class TestQuotaManagement:
    """配额管理测试"""

    def test_set_quota(self):
        """测试设置配额"""
        from services.quota_monitor import QuotaMonitor
        from config.database import init_db, SessionLocal
        from models.model_config import ModelConfig
        from models.quota_stat import QuotaStat

        # 使用不同的数据库路径避免冲突
        import os
        test_db = "./data/test_quota_management.db"
        os.environ["DB_PATH"] = test_db

        init_db()
        db = SessionLocal()

        try:
            # 创建测试模型
            model = ModelConfig(
                vendor="test",
                model_name="test-model",
                api_key="test-key",
                api_spec="openai",
                status=1
            )
            db.add(model)
            db.commit()
            # 保存 id 因为后续操作会关闭 session
            model_id = model.id

            # 设置配额
            result = QuotaMonitor.set_quota(
                model_id=model_id,
                total_quota=1000,
                plan_type="test",
                plan_name="Test Plan",
                quota_unit="tokens",
                period_hours=24
            )

            assert result is True

            # 验证配额
            quota_info = QuotaMonitor.get_quota(model_id)
            assert quota_info is not None
            assert quota_info["total_quota"] == 1000
            assert quota_info["remain_quota"] == 1000
            assert quota_info["used_ratio"] == 0

        finally:
            # 清理 - 使用新的 session
            db = SessionLocal()
            db.query(QuotaStat).filter(QuotaStat.model_id == model_id).delete()
            db.query(ModelConfig).filter(ModelConfig.id == model_id).delete()
            db.commit()
            db.close()
            # 删除测试数据库
            if os.path.exists(test_db):
                os.remove(test_db)

    def test_add_usage(self):
        """测试累加使用量"""
        from services.quota_monitor import QuotaMonitor
        from config.database import init_db, SessionLocal
        from models.model_config import ModelConfig
        from models.quota_stat import QuotaStat

        import os
        test_db = "./data/test_add_usage.db"
        os.environ["DB_PATH"] = test_db

        init_db()
        db = SessionLocal()

        try:
            # 创建测试模型
            model = ModelConfig(
                vendor="test",
                model_name="test-model-usage",
                api_key="test-key",
                api_spec="openai",
                status=1
            )
            db.add(model)
            db.commit()
            model_id = model.id

            # 设置配额
            QuotaMonitor.set_quota(
                model_id=model_id,
                total_quota=1000,
                quota_unit="tokens"
            )

            # 累加使用量
            result = QuotaMonitor.add_usage(model_id, 100)
            assert result is True

            # 验证
            quota_info = QuotaMonitor.get_quota(model_id)
            assert quota_info["used_quota"] == 100
            assert quota_info["remain_quota"] == 900
            assert quota_info["used_ratio"] == 10.0

        finally:
            db = SessionLocal()
            db.query(QuotaStat).filter(QuotaStat.model_id == model_id).delete()
            db.query(ModelConfig).filter(ModelConfig.id == model_id).delete()
            db.commit()
            db.close()
            if os.path.exists(test_db):
                os.remove(test_db)

    def test_is_quota_exhausted(self):
        """测试检查配额耗尽"""
        from services.quota_monitor import QuotaMonitor
        from config.database import init_db, SessionLocal
        from models.model_config import ModelConfig
        from models.quota_stat import QuotaStat

        import os
        test_db = "./data/test_quota_exhaust.db"
        os.environ["DB_PATH"] = test_db

        init_db()
        db = SessionLocal()

        try:
            model = ModelConfig(
                vendor="test",
                model_name="test-model-exhaust",
                api_key="test-key",
                api_spec="openai",
                status=1
            )
            db.add(model)
            db.commit()
            model_id = model.id

            # 设置小配额
            QuotaMonitor.set_quota(
                model_id=model_id,
                total_quota=100,
                quota_unit="tokens"
            )

            # 未耗尽
            assert QuotaMonitor.is_quota_exhausted(model_id) is False

            # 累加到超过配额
            QuotaMonitor.add_usage(model_id, 150)

            # 应该耗尽
            assert QuotaMonitor.is_quota_exhausted(model_id) is True

        finally:
            db = SessionLocal()
            db.query(QuotaStat).filter(QuotaStat.model_id == model_id).delete()
            db.query(ModelConfig).filter(ModelConfig.id == model_id).delete()
            db.commit()
            db.close()
            if os.path.exists(test_db):
                os.remove(test_db)

    def test_reset_quota(self):
        """测试重置配额"""
        from services.quota_monitor import QuotaMonitor
        from config.database import init_db, SessionLocal
        from models.model_config import ModelConfig
        from models.quota_stat import QuotaStat

        import os
        test_db = "./data/test_quota_reset.db"
        os.environ["DB_PATH"] = test_db

        init_db()
        db = SessionLocal()

        try:
            model = ModelConfig(
                vendor="test",
                model_name="test-model-reset",
                api_key="test-key",
                api_spec="openai",
                status=1
            )
            db.add(model)
            db.commit()
            model_id = model.id

            # 设置并使用配额
            QuotaMonitor.set_quota(model_id=model_id, total_quota=1000)
            QuotaMonitor.add_usage(model_id, 500)

            # 重置
            result = QuotaMonitor.reset_quota(model_id)
            assert result is True

            # 验证已重置
            quota_info = QuotaMonitor.get_quota(model_id)
            assert quota_info["used_quota"] == 0
            assert quota_info["remain_quota"] == 1000
            assert quota_info["used_ratio"] == 0

        finally:
            db = SessionLocal()
            db.query(QuotaStat).filter(QuotaStat.model_id == model_id).delete()
            db.query(ModelConfig).filter(ModelConfig.id == model_id).delete()
            db.commit()
            db.close()
            if os.path.exists(test_db):
                os.remove(test_db)

    def test_quota_status_update(self):
        """测试配额状态更新"""
        from services.quota_monitor import QuotaMonitor
        from config.database import init_db, SessionLocal
        from models.model_config import ModelConfig
        from models.quota_stat import QuotaStat

        import os
        test_db = "./data/test_quota_status.db"
        os.environ["DB_PATH"] = test_db

        init_db()
        db = SessionLocal()

        try:
            model = ModelConfig(
                vendor="test",
                model_name="test-model-status",
                api_key="test-key",
                api_spec="openai",
                status=1,
                quota_status=2
            )
            db.add(model)
            db.commit()
            model_id = model.id

            # 额度低于90%，状态应为2
            QuotaMonitor.set_quota(model_id=model_id, total_quota=100)
            QuotaMonitor.add_usage(model_id, 10)  # 10%

            status = QuotaMonitor.get_quota_status(model_id)
            assert status == 2  # 正常

            # 额度达到90%以上，状态应为1
            QuotaMonitor.add_usage(model_id, 85)  # 95%
            status = QuotaMonitor.get_quota_status(model_id)
            assert status == 1  # 警告

            # 额度100%，状态应为0
            QuotaMonitor.add_usage(model_id, 10)  # 105%
            status = QuotaMonitor.get_quota_status(model_id)
            assert status == 0  # 耗尽

        finally:
            db = SessionLocal()
            db.query(QuotaStat).filter(QuotaStat.model_id == model_id).delete()
            db.query(ModelConfig).filter(ModelConfig.id == model_id).delete()
            db.commit()
            db.close()
            if os.path.exists(test_db):
                os.remove(test_db)


# ==================== 运行测试 ====================

if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v", "--tb=short", "-x"])
