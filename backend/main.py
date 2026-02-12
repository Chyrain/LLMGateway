from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import uvicorn
import json
import httpx
import asyncio
from datetime import datetime
import os
from sqlalchemy import text

from config.database import get_db, init_db, SessionLocal

from models.model_config import ModelConfig
from models.quota_stat import QuotaStat
from models.system_config import SystemConfig
from models.operation_log import OperationLog
from models.notification import Notification
from services.gateway_core import GatewayCore
from services.quota_monitor import QuotaMonitor

# 导入路由
from routers.auth import auth_router
from routers.notifications import notification_router
from routers.stats import stats_router
from routers.logs import logs_router
from routers.config import config_router


# 启动事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from config.database import init_default_config

    init_default_config()
    yield


app = FastAPI(
    title="灵模网关 API",
    description="LLM Free Quota Gateway API",
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

# 注册路由
app.include_router(auth_router)
app.include_router(notification_router)
app.include_router(stats_router)
app.include_router(logs_router)
app.include_router(config_router)


# ==================== 根路径健康检查 ====================
@app.get("/")
async def root():
    return {"message": "灵模网关服务运行中", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.on_event("startup")
async def startup_event():
    """数据库迁移：添加新列"""
    db = SessionLocal()
    try:
        # 检查 api_spec 列是否存在
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
    except Exception as e:
        print(f"[WARN] 数据库迁移检查: {e}")
    finally:
        db.close()


# ==================== 模型配置接口 ====================
class AddModelRequest(BaseModel):
    vendor: str
    model_name: str
    api_key: str
    api_base: Optional[str] = None
    api_path: Optional[str] = "/v1/chat/completions"
    api_spec: Optional[str] = "openai"
    params: Optional[Dict[str, Any]] = {}
    priority: Optional[int] = 100


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
    )

    db.add(model)
    db.commit()
    db.refresh(model)

    # 创建额度记录
    quota = QuotaStat(
        model_id=model.id,
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
    """测试模型连通性"""
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()

    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    success = await GatewayCore.test_connectivity(
        model.vendor, model.api_base, model.api_key, model.model_name
    )

    model.connect_status = 1 if success else 0
    db.commit()

    if success:
        return {"code": 200, "msg": "连通测试成功"}
    else:
        raise HTTPException(status_code=400, detail="连通测试失败")


# 获取可用模型列表的请求模型
class FetchModelsRequest(BaseModel):
    vendor: str
    api_key: str
    api_base: Optional[str] = None


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


class UpdateModelRequest(BaseModel):
    vendor: Optional[str] = None
    model_name: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    api_path: Optional[str] = None
    api_spec: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None


@app.put("/api/models/{model_id}")
async def update_model(
    model_id: int, request: UpdateModelRequest, db: SessionLocal = Depends(get_db)
):
    """更新模型配置"""
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()

    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    print(f"[DEBUG] 更新模型 {model_id}, 请求数据: {request.dict()}")
    print(f"[DEBUG] 更新前 priority: {model.priority}")

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
        print(f"[DEBUG] 更新 priority 为: {request.priority}")

    db.commit()
    db.refresh(model)
    print(f"[DEBUG] 更新后 priority: {model.priority}")

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
    """
    获取额度历史记录
    """
    # 返回模拟历史数据（生产环境应使用独立的历史记录表）
    from datetime import datetime, timedelta

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


# ==================== 网关核心接口 (OpenAI兼容) ====================
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None  # 可选，不传时自动使用最高优先级模型
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    model_config = ConfigDict(extra="allow")


@app.get("/v1/models")
async def list_models_v1(authorization: Optional[str] = Header(None)):
    """OpenAI兼容的模型列表接口

    供第三方客户端检测可用的模型列表
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少有效的API Key")

    gateway_api_key = authorization.replace("Bearer ", "")

    # 获取所有启用的模型
    db = SessionLocal()
    try:
        models = (
            db.query(ModelConfig)
            .filter(ModelConfig.status == 1)
            .order_by(ModelConfig.priority)
            .all()
        )

        # 如果没有启用任何模型，返回空列表
        if not models:
            return {"object": "list", "data": []}

        # 转换为 OpenAI 格式
        models_data = []

        # 只有启用了模型才添加 auto 选项
        models_data.append(
            {
                "id": "auto",
                "object": "model",
                "created": 0,
                "owned_by": "gateway",
                "description": "自动根据优先级切换模型",
                "capabilities": {"auto_switch": True, "priority_based": True},
            }
        )

        for model in models:
            models_data.append(
                {
                    "id": model.model_name,
                    "object": "model",
                    "created": int(model.create_time.timestamp())
                    if model.create_time
                    else 0,
                    "owned_by": model.vendor,
                }
            )

        return {"object": "list", "data": models_data}
    finally:
        db.close()


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest, authorization: Optional[str] = Header(None)
):
    """OpenAI兼容的Chat Completions接口，支持自动切换模型"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少有效的API Key")

    gateway_api_key = authorization.replace("Bearer ", "")
    requested_model = request.model
    is_auto_mode = (
        requested_model in ["auto", "Auto", "AUTO", ""] or not requested_model
    )

    # 获取所有可用的模型（按优先级排序）
    db = SessionLocal()
    try:
        available_models = (
            db.query(ModelConfig)
            .filter(ModelConfig.status == 1, ModelConfig.connect_status == 1)
            .order_by(ModelConfig.priority)
            .all()
        )

        if not available_models:
            raise HTTPException(status_code=503, detail="无可用模型，请先配置模型")

        # 如果是 auto 模式，尝试所有可用模型
        # 如果指定了模型，优先试指定的模型，然后尝试其他可用模型
        if is_auto_mode:
            models_to_try = available_models
        else:
            # 找到指定模型的位置，将其移到前面
            target_model = next(
                (m for m in available_models if m.model_name == requested_model), None
            )
            if target_model:
                models_to_try = [target_model] + [
                    m for m in available_models if m.model_name != requested_model
                ]
            else:
                models_to_try = available_models

        last_error = None
        successful_model = None
        response = None

        for model in models_to_try:
            try:
                print(f"[INFO] 尝试模型: {model.vendor} - {model.model_name}")

                request_data = {
                    "model": model.model_name,
                    "messages": [m.model_dump() for m in request.messages],
                    "stream": request.stream,
                }

                if request.temperature is not None:
                    request_data["temperature"] = request.temperature
                if request.max_tokens is not None:
                    request_data["max_tokens"] = request.max_tokens

                if request.stream:
                    return StreamingResponse(
                        GatewayCore.stream_request(
                            model.vendor, model.api_base, model.api_key, request_data
                        ),
                        media_type="text/event-stream",
                    )
                else:
                    response = await GatewayCore.sync_request(
                        model.vendor, model.api_base, model.api_key, request_data
                    )

                # 验证响应是否有效（必须有 choices 且有内容）
                choices = response.get("choices", [])
                if (
                    not choices
                    or not choices[0].get("message", {}).get("content", "").strip()
                ):
                    raise ValueError(f"模型返回空响应")

                # 成功：记录日志并返回
                successful_model = model
                log = OperationLog(
                    log_type=1,
                    model_id=model.id,
                    log_content=json.dumps(
                        {
                            "model": requested_model or "auto",
                            "actual_model": model.model_name,
                            "status": "success",
                            "usage": response.get("usage", {}),
                        }
                    ),
                    status=1,
                )
                db.add(log)
                db.commit()

                print(f"[SUCCESS] 使用模型: {model.vendor} - {model.model_name}")
                return response

            except Exception as e:
                last_error = e
                error_msg = str(e)
                print(
                    f"[ERROR] 模型 {model.vendor} - {model.model_name} 失败: {error_msg}"
                )

                # 记录失败日志
                log = OperationLog(
                    log_type=3,
                    model_id=model.id,
                    log_content=json.dumps(
                        {
                            "model": requested_model or "auto",
                            "attempted_model": model.model_name,
                            "error": error_msg,
                        }
                    ),
                    status=0,
                )
                db.add(log)
                db.commit()

                # 如果不是 auto 模式，且找到了指定模型，失败后尝试其他模型
                # 如果是 auto 模式，继续尝试下一个
                continue

        # 所有模型都失败了
        error_detail = (
            last_error.detail if hasattr(last_error, "detail") else str(last_error)
        )
        raise HTTPException(
            status_code=500, detail=f"所有可用模型均失败: {error_detail}"
        )

    finally:
        db.close()


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
