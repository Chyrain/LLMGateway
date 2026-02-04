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

from config.database import get_db, init_db, SessionLocal
from config.encryption import encrypt_api_key, decrypt_api_key
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

# 启动事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="灵模网关 API",
    description="LLM Free Quota Gateway API",
    version="1.0.0",
    lifespan=lifespan
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

# ==================== 根路径健康检查 ====================
@app.get("/")
async def root():
    return {"message": "灵模网关服务运行中", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ==================== 模型配置接口 ====================
class AddModelRequest(BaseModel):
    vendor: str
    model_name: str
    api_key: str
    api_base: Optional[str] = None
    api_path: Optional[str] = "/v1/chat/completions"
    params: Optional[Dict[str, Any]] = {}
    priority: Optional[int] = 100

@app.get("/api/model/list")
async def list_models(
    vendor: Optional[str] = None, 
    status: Optional[int] = None,
    db: SessionLocal = Depends(get_db)
):
    """获取模型配置列表"""
    query = db.query(ModelConfig)
    
    if vendor:
        query = query.filter(ModelConfig.vendor == vendor)
    if status is not None:
        query = query.filter(ModelConfig.status == status)
    
    models = query.order_by(ModelConfig.priority).all()
    
    return {
        "code": 200,
        "msg": "success",
        "data": [{
            "id": m.id,
            "vendor": m.vendor,
            "model_name": m.model_name,
            "api_base": m.api_base,
            "api_path": m.api_path,
            "priority": m.priority,
            "status": m.status,
            "connect_status": m.connect_status,
            "quota_status": m.quota_status,
            "create_time": m.create_time,
            "update_time": m.update_time
        } for m in models]
    }

@app.post("/api/model/add")
async def add_model(request: AddModelRequest, db: SessionLocal = Depends(get_db)):
    """新增模型配置"""
    exist = db.query(ModelConfig).filter(
        ModelConfig.vendor == request.vendor,
        ModelConfig.model_name == request.model_name
    ).first()
    
    if exist:
        raise HTTPException(status_code=400, detail="模型配置已存在")
    
    encrypted_key = encrypt_api_key(request.api_key)
    
    model = ModelConfig(
        vendor=request.vendor,
        model_name=request.model_name,
        api_key=encrypted_key,
        api_base=request.api_base or get_vendor_template(request.vendor).get("api_base"),
        api_path=request.api_path,
        params=request.params or {},
        priority=request.priority
    )
    
    db.add(model)
    db.commit()
    
    return {"code": 200, "msg": "success", "data": {"id": model.id}}

@app.post("/api/model/{model_id}/test")
async def test_model_connectivity(model_id: int, db: SessionLocal = Depends(get_db)):
    """测试模型连通性"""
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    api_key = decrypt_api_key(model.api_key)
    success = await GatewayCore.test_connectivity(model.vendor, model.api_base, api_key)
    
    model.connect_status = 1 if success else 0
    db.commit()
    
    if success:
        return {"code": 200, "msg": "连通测试成功"}
    else:
        raise HTTPException(status_code=400, detail="连通测试失败")

@app.post("/api/model/{model_id}/enable")
async def enable_model(model_id: int, db: SessionLocal = Depends(get_db)):
    """启用模型"""
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    model.status = 1
    db.commit()
    
    return {"code": 200, "msg": "模型已启用"}

@app.post("/api/model/{model_id}/disable")
async def disable_model(model_id: int, db: SessionLocal = Depends(get_db)):
    """禁用模型"""
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    model.status = 0
    db.commit()
    
    return {"code": 200, "msg": "模型已禁用"}

@app.delete("/api/model/{model_id}")
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
async def get_quota_stats(model_id: Optional[int] = None, db: SessionLocal = Depends(get_db)):
    """获取额度统计"""
    query = db.query(QuotaStat)
    
    if model_id:
        query = query.filter(QuotaStat.model_id == model_id)
    
    stats = query.all()
    
    return {
        "code": 200,
        "msg": "success",
        "data": [{
            "model_id": s.model_id,
            "total_quota": s.total_quota,
            "used_quota": s.used_quota,
            "remain_quota": s.remain_quota,
            "used_ratio": s.used_ratio,
            "sync_type": s.sync_type,
            "last_sync_time": s.last_sync_time
        } for s in stats]
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
        raise HTTPException(status_code=400, detail="额度同步失败，该厂商不支持自动同步")

# ==================== 网关核心接口 (OpenAI兼容) ====================
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    model_config = ConfigDict(extra="allow")

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None)
):
    """OpenAI兼容的Chat Completions接口"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少有效的API Key")
    
    gateway_api_key = authorization.replace("Bearer ", "")
    
    # 获取当前模型
    db = SessionLocal()
    try:
        current_model = db.query(ModelConfig).filter(
            ModelConfig.status == 1,
            ModelConfig.connect_status == 1
        ).order_by(ModelConfig.priority).first()
    finally:
        db.close()
    
    if not current_model:
        raise HTTPException(status_code=503, detail="无可用的模型，请先配置模型")
    
    api_key = decrypt_api_key(current_model.api_key)
    
    request_data = {
        "model": current_model.model_name,
        "messages": [m.model_dump() for m in request.messages],
        "stream": request.stream
    }
    
    if request.temperature is not None:
        request_data["temperature"] = request.temperature
    if request.max_tokens is not None:
        request_data["max_tokens"] = request.max_tokens
    
    try:
        if request.stream:
            return StreamingResponse(
                GatewayCore.stream_request(
                    current_model.vendor,
                    current_model.api_base,
                    api_key,
                    request_data
                ),
                media_type="text/event-stream"
            )
        else:
            response = await GatewayCore.sync_request(
                current_model.vendor,
                current_model.api_base,
                api_key,
                request_data
            )
            
            # 记录日志
            db = SessionLocal()
            try:
                log = OperationLog(
                    log_type=1,
                    model_id=current_model.id,
                    log_content=json.dumps({
                        "model": request.model,
                        "status": "success",
                        "usage": response.get("usage", {})
                    }),
                    status=1
                )
                db.add(log)
                db.commit()
            finally:
                db.close()
            
            return response
            
    except Exception as e:
        # 记录错误日志
        db = SessionLocal()
        try:
            log = OperationLog(
                log_type=3,
                model_id=current_model.id,
                log_content=json.dumps({"error": str(e)}),
                status=0
            )
            db.add(log)
            db.commit()
        finally:
            db.close()
        
        raise HTTPException(status_code=500, detail=f"请求失败: {str(e)}")

# ==================== 工具函数 ====================
def get_vendor_template(vendor: str) -> Dict:
    """获取厂商预配置模板"""
    templates = {
        "openai": {"api_base": "https://api.openai.com", "api_path": "/v1/chat/completions"},
        "qwen": {"api_base": "https://dashscope.aliyuncs.com", "api_path": "/api/v1/services/aigc/text-generation/generation"},
        "zhipu": {"api_base": "https://open.bigmodel.cn", "api_path": "/api/llm/v3.5/chatcompletions_pro"},
        "spark": {"api_base": "https://spark-api.xf-yun.com", "api_path": "/v3.1/chat"},
        "doubao": {"api_base": "https://ark.cn-beijing.volces.com", "api_path": "/api/v3/bots/chat_sessions"},
        "claude": {"api_base": "https://api.anthropic.com", "api_path": "/v1/messages"},
        "gemini": {"api_base": "https://generativelanguage.googleapis.com", "api_path": "/v1beta/models/gemini-pro:generateContent"},
        "mistral": {"api_base": "https://api.mistral.ai", "api_path": "/v1/chat/completions"},
        "perplexity": {"api_base": "https://api.perplexity.ai", "api_path": "/chat/completions"},
        "groq": {"api_base": "https://api.groq.com", "api_path": "/openai/v1/chat/completions"}
    }
    return templates.get(vendor.lower(), {"api_base": "", "api_path": "/v1/chat/completions"})

if __name__ == "__main__":
    port = int(os.getenv("GATEWAY_PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
