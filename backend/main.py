"""
灵模网关 - 主入口文件

根据环境变量决定运行模式：
- API_MODE=true: 管理后台模式（8000端口），暴露管理接口
- GATEWAY_MODE=true: 网关模式（8080端口），只暴露 LLM 转发接口
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime
import os
from sqlalchemy import text

from config.database import get_db, init_db, SessionLocal
from models.model_config import ModelConfig
from models.quota_stat import QuotaStat
from services.gateway_core import GatewayCore
from services.quota_monitor import QuotaMonitor

# 导入路由
from routers.auth import auth_router
from routers.notifications import notification_router
from routers.stats import stats_router
from routers.logs import logs_router
from routers.config import config_router
from routers.quota import quota_router


# 判断运行模式
API_MODE = os.getenv("API_MODE", "false").lower() == "true"
GATEWAY_MODE = os.getenv("GATEWAY_MODE", "false").lower() == "true"

# 根据模式设置应用标题
if API_MODE:
    app_title = "灵模网关 - 管理后台 API"
    app_description = "模型配置、额度管理、日志查询"
elif GATEWAY_MODE:
    app_title = "灵模网关 - LLM 转发服务"
    app_description = "OpenAI 兼容接口"
else:
    app_title = "灵模网关 API"
    app_description = "LLM Free Quota Gateway API"


# 启动事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from config.database import init_default_config
    init_default_config()
    yield


app = FastAPI(
    title=app_title,
    description=app_description,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 根据运行模式注册路由 ====================
# API 模式（8000端口）：注册管理接口
if API_MODE:
    # 认证接口
    app.include_router(auth_router)
    # 通知接口
    app.include_router(notification_router)
    # 统计接口
    app.include_router(stats_router)
    # 日志接口
    app.include_router(logs_router)
    # 配置接口（模型配置、额度配置等）
    app.include_router(config_router)
    # 配额管理接口
    app.include_router(quota_router)

    # API 模式下也注册网关接口，供前端测试使用
    from routers.gateway import gateway_router
    app.include_router(gateway_router)

# GATEWAY 模式（8080端口）：只注册网关接口
if GATEWAY_MODE:
    from routers.gateway import gateway_router
    app.include_router(gateway_router)


# ==================== 根路径和健康检查 ====================
@app.get("/")
async def root():
    if API_MODE:
        return {"message": "灵模网关管理后台", "version": "1.0.0", "mode": "api"}
    elif GATEWAY_MODE:
        return {"message": "灵模网关服务运行中", "version": "1.0.0", "mode": "gateway"}
    else:
        return {"message": "灵模网关服务运行中", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.on_event("startup")
async def startup_event():
    """数据库迁移：添加新列"""
    db = SessionLocal()
    try:
        # 迁移 model_config 表
        result = db.execute(text("PRAGMA table_info(model_config)"))
        columns = [row[1] for row in result.fetchall()]

        if "api_spec" not in columns:
            db.execute(
                text(
                    "ALTER TABLE model_config ADD COLUMN api_spec VARCHAR(50) DEFAULT 'openai'"
                )
            )
            db.commit()
            print("[INFO] 已添加 api_spec 列到 model_config 表")

        # 添加 plan_type 和 is_coding_model 列
        if "plan_type" not in columns:
            db.execute(
                text(
                    "ALTER TABLE model_config ADD COLUMN plan_type VARCHAR(20) DEFAULT 'default'"
                )
            )
            db.commit()
            print("[INFO] 已添加 plan_type 列到 model_config 表")

        if "is_coding_model" not in columns:
            db.execute(
                text(
                    "ALTER TABLE model_config ADD COLUMN is_coding_model INTEGER DEFAULT 0"
                )
            )
            db.commit()
            print("[INFO] 已添加 is_coding_model 列到 model_config 表")

        # 迁移 quota_stat 表
        result = db.execute(text("PRAGMA table_info(quota_stat)"))
        quota_columns = [row[1] for row in result.fetchall()]

        if "plan_type" not in quota_columns:
            db.execute(
                text(
                    "ALTER TABLE quota_stat ADD COLUMN plan_type VARCHAR(20) DEFAULT 'default'"
                )
            )
            db.commit()
            print("[INFO] 已添加 plan_type 列到 quota_stat 表")

        if "plan_name" not in quota_columns:
            db.execute(
                text(
                    "ALTER TABLE quota_stat ADD COLUMN plan_name VARCHAR(100) DEFAULT ''"
                )
            )
            db.commit()
            print("[INFO] 已添加 plan_name 列到 quota_stat 表")

    except Exception as e:
        print(f"[WARN] 数据库迁移检查: {e}")
    finally:
        db.close()


# ==================== 模型配置接口（仅 API 模式）====================
class AddModelRequest(BaseModel):
    vendor: str
    model_name: str
    api_key: str
    api_base: Optional[str] = None
    api_path: Optional[str] = "/v1/chat/completions"
    api_spec: Optional[str] = "openai"
    params: Optional[Dict[str, Any]] = {}
    priority: Optional[int] = 100
    plan_type: Optional[str] = "default"
    is_coding_model: Optional[int] = 0


class FetchModelsRequest(BaseModel):
    vendor: str
    api_key: str
    api_base: Optional[str] = None


class UpdateModelRequest(BaseModel):
    vendor: Optional[str] = None
    model_name: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    api_path: Optional[str] = None
    api_spec: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    plan_type: Optional[str] = None
    is_coding_model: Optional[int] = None


# 仅在 API 模式下注册模型配置接口
if API_MODE:
    @app.get("/api/models/{model_id}")
    async def get_model_detail(model_id: int, db: SessionLocal = Depends(get_db)):
        """获取单个模型详情（包含解密后的API Key）"""
        model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()

        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")

        return {
            "code": 200,
            "msg": "success",
            "data": {
                "id": model.id,
                "vendor": model.vendor,
                "model_name": model.model_name,
                "api_base": model.api_base,
                "api_path": model.api_path,
                "api_spec": model.api_spec,
                "api_key": model.api_key,
                "priority": model.priority,
                "status": model.status,
                "connect_status": model.connect_status,
                "quota_status": model.quota_status,
                "plan_type": model.plan_type,
                "is_coding_model": model.is_coding_model,
                "params": model.params,
                "create_time": model.create_time.strftime("%Y-%m-%d %H:%M:%S")
                if model.create_time
                else None,
                "update_time": model.update_time.strftime("%Y-%m-%d %H:%M:%S")
                if model.update_time
                else None,
            },
        }


    @app.get("/api/models")
    async def list_models(
        vendor: Optional[str] = None,
        status: Optional[int] = None,
        db: SessionLocal = Depends(get_db),
    ):
        """获取模型配置列表"""
        query = db.query(ModelConfig)

        if vendor:
            query = query.filter(ModelConfig.vendor == vendor)
        if status is not None:
            query = query.filter(ModelConfig.status == status)

        models = query.order_by(ModelConfig.priority).all()

        result = []
        for m in models:
            result.append(
                {
                    "id": m.id,
                    "vendor": m.vendor,
                    "model_name": m.model_name,
                    "api_base": m.api_base,
                    "api_path": m.api_path,
                    "api_spec": m.api_spec,
                    "api_key": m.api_key or "",
                    "priority": m.priority,
                    "status": m.status,
                    "connect_status": m.connect_status,
                    "quota_status": m.quota_status,
                    "plan_type": m.plan_type,
                    "is_coding_model": m.is_coding_model,
                    "create_time": m.create_time.strftime("%Y-%m-%d %H:%M:%S")
                    if m.create_time
                    else None,
                    "update_time": m.update_time.strftime("%Y-%m-%d %H:%M:%S")
                    if m.update_time
                    else None,
                }
            )

        return {
            "code": 200,
            "msg": "success",
            "data": result,
        }


    @app.post("/api/models")
    async def add_model(request: AddModelRequest, db: SessionLocal = Depends(get_db)):
        """新增模型配置"""
        exist = (
            db.query(ModelConfig)
            .filter(
                ModelConfig.vendor == request.vendor,
                ModelConfig.model_name == request.model_name,
            )
            .first()
        )

        if exist:
            raise HTTPException(status_code=400, detail="模型配置已存在")

        model = ModelConfig(
            vendor=request.vendor,
            model_name=request.model_name,
            api_key=request.api_key,
            api_base=request.api_base
            or get_vendor_template(request.vendor).get("api_base"),
            api_path=request.api_path,
            api_spec=request.api_spec or "openai",
            params=request.params or {},
            priority=request.priority,
            plan_type=request.plan_type or "default",
            is_coding_model=request.is_coding_model or 0,
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        # 创建额度记录
        quota = QuotaStat(
            model_id=model.id,
            plan_type=request.plan_type or "default",
            plan_name="",
            total_quota=0,
            used_quota=0,
            remain_quota=0,
            used_ratio=0,
            sync_type=0,
        )
        db.add(quota)
        db.commit()

        return {"code": 200, "msg": "success", "data": {"id": model.id}}


    @app.post("/api/models/{model_id}/test")
    async def test_model_connectivity(model_id: int, db: SessionLocal = Depends(get_db)):
        """测试模型连通性 - 发送实际聊天请求"""
        model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()

        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")

        # 构建测试请求 - 发送实际聊天消息
        test_messages = [{"role": "user", "content": "你好"}]
        request_data = {
            "model": model.model_name,
            "messages": test_messages,
            "stream": False,
        }

        try:
            # 调用 GatewayCore 发送实际请求
            response = await GatewayCore.sync_request(
                vendor=model.vendor,
                api_base=model.api_base,
                api_key=model.api_key,
                request_data=request_data,
            )

            # 更新模型状态
            model.connect_status = 1
            db.commit()

            return {
                "code": 200,
                "msg": "连通测试成功",
                "data": {
                    "request": request_data,
                    "response": response
                }
            }
        except Exception as e:
            model.connect_status = 0
            db.commit()
            raise HTTPException(status_code=400, detail=f"连通测试失败: {str(e)}")


    @app.post("/api/models/fetch-available")
    async def fetch_available_models_api(request: FetchModelsRequest):
        """获取厂商可用模型列表"""
        from services.gateway_core import GatewayCore

        api_base = request.api_base or get_vendor_template(request.vendor).get("api_base")

        if not api_base:
            raise HTTPException(status_code=400, detail="无法获取API Base地址")

        result = await GatewayCore.fetch_available_models(
            request.vendor, api_base, request.api_key
        )

        return {
            "code": 200,
            "msg": result.get("message", ""),
            "data": result.get("models", []),
        }


    @app.post("/api/models/{model_id}/enable")
    async def enable_model(model_id: int, db: SessionLocal = Depends(get_db)):
        """启用模型"""
        model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()

        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")

        model.status = 1
        db.commit()

        return {"code": 200, "msg": "模型已启用"}


    @app.post("/api/models/{model_id}/disable")
    async def disable_model(model_id: int, db: SessionLocal = Depends(get_db)):
        """禁用模型"""
        model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()

        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")

        model.status = 0
        db.commit()

        return {"code": 200, "msg": "模型已禁用"}


    @app.put("/api/models/{model_id}")
    async def update_model(
        model_id: int, request: UpdateModelRequest, db: SessionLocal = Depends(get_db)
    ):
        """更新模型配置"""
        model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()

        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")

        # 更新字段（如果提供了新值）
        if request.vendor is not None:
            model.vendor = request.vendor
        if request.model_name is not None:
            model.model_name = request.model_name
        if request.api_base is not None:
            model.api_base = request.api_base
        if request.api_key is not None:
            model.api_key = request.api_key
        if request.api_path is not None:
            model.api_path = request.api_path
        if request.api_spec is not None:
            model.api_spec = request.api_spec
        if request.params is not None:
            model.params = request.params
        if request.priority is not None:
            model.priority = request.priority
        if request.plan_type is not None:
            model.plan_type = request.plan_type
        if request.is_coding_model is not None:
            model.is_coding_model = request.is_coding_model

        db.commit()
        db.refresh(model)

        return {"code": 200, "msg": "success", "data": {"id": model.id}}


    @app.delete("/api/models/{model_id}")
    async def delete_model(model_id: int, db: SessionLocal = Depends(get_db)):
        """删除模型"""
        model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()

        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")

        db.delete(model)
        db.commit()

        return {"code": 200, "msg": "删除成功"}


    # ==================== 额度统计接口 ====================
    @app.get("/api/quota/stat")
    async def get_quota_stats(
        model_id: Optional[int] = None, db: SessionLocal = Depends(get_db)
    ):
        """获取额度统计"""
        query = db.query(QuotaStat)

        if model_id:
            query = query.filter(QuotaStat.model_id == model_id)

        stats = query.all()

        return {
            "code": 200,
            "msg": "success",
            "data": [
                {
                    "model_id": s.model_id,
                    "total_quota": s.total_quota,
                    "used_quota": s.used_quota,
                    "remain_quota": s.remain_quota,
                    "used_ratio": s.used_ratio,
                    "sync_type": s.sync_type,
                    "last_sync_time": s.last_sync_time,
                }
                for s in stats
            ],
        }


    @app.post("/api/quota/sync/{model_id}")
    async def sync_quota(model_id: int, db: SessionLocal = Depends(get_db)):
        """同步模型额度"""
        model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()

        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")

        success = await QuotaMonitor.sync_quota_by_vendor(model.vendor, model_id)

        if success:
            return {"code": 200, "msg": "额度同步成功"}
        else:
            raise HTTPException(
                status_code=400, detail="额度同步失败，该厂商不支持自动同步"
            )


    @app.get("/api/quota/history")
    async def get_quota_history(
        model_id: Optional[int] = None, days: int = 30, db: SessionLocal = Depends(get_db)
    ):
        """获取额度历史记录"""
        from datetime import timedelta

        history = []
        end_date = datetime.now()

        for i in range(days):
            date = end_date - timedelta(days=days - 1 - i)
            history.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "total_quota": 1000000,
                    "used_quota": i * 10000 + 50000,
                    "remain_quota": 1000000 - i * 10000 - 50000,
                    "usage_rate": round((i * 10000 + 50000) / 1000000 * 100, 2),
                }
            )

        return {"code": 200, "msg": "success", "data": history}


# ==================== 工具函数 ====================
def get_vendor_template(vendor: str) -> Dict:
    """获取厂商预配置模板"""
    templates = {
        "openai": {
            "api_base": "https://api.openai.com",
            "api_path": "/v1/chat/completions",
        },
        "qwen": {
            "api_base": "https://dashscope.aliyuncs.com",
            "api_path": "/api/v1/services/aigc/text-generation/generation",
        },
        "zhipu": {
            "api_base": "https://open.bigmodel.cn",
            "api_path": "/api/llm/v3.5/chatcompletions_pro",
        },
        "spark": {"api_base": "https://spark-api.xf-yun.com", "api_path": "/v3.1/chat"},
        "doubao": {
            "api_base": "https://ark.cn-beijing.volces.com",
            "api_path": "/api/v3/bots/chat_sessions",
        },
        "claude": {"api_base": "https://api.anthropic.com", "api_path": "/v1/messages"},
        "gemini": {
            "api_base": "https://generativelanguage.googleapis.com",
            "api_path": "/v1beta/models/gemini-pro:generateContent",
        },
        "mistral": {
            "api_base": "https://api.mistral.ai",
            "api_path": "/v1/chat/completions",
        },
        "perplexity": {
            "api_base": "https://api.perplexity.ai",
            "api_path": "/chat/completions",
        },
        "groq": {
            "api_base": "https://api.groq.com",
            "api_path": "/openai/v1/chat/completions",
        },
    }
    return templates.get(
        vendor.lower(), {"api_base": "", "api_path": "/v1/chat/completions"}
    )


if __name__ == "__main__":
    # 检查运行模式
    api_mode = os.getenv("API_MODE", "false").lower() == "true"
    gateway_mode = os.getenv("GATEWAY_MODE", "false").lower() == "true"

    if api_mode:
        # API 模式，运行在 8000 端口
        port = int(os.getenv("API_PORT", 8000))
    elif gateway_mode:
        # 网关模式，运行在 8080 端口
        port = int(os.getenv("GATEWAY_PORT", 8080))
    else:
        # 默认网关模式
        port = int(os.getenv("GATEWAY_PORT", 8080))

    uvicorn.run(app, host="0.0.0.0", port=port)
