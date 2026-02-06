"""
日志 API 路由
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from config.database import get_db
from models.operation_log import OperationLog

logs_router = APIRouter()

class LogListResponse(BaseModel):
    id: int
    log_type: int
    model_id: Optional[int]
    log_content: Optional[str]
    status: int
    create_time: Optional[str]

@logs_router.get("/api/log/list")
async def get_log_list(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    log_type: Optional[int] = None,
    model_id: Optional[int] = None,
    status: Optional[int] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取日志列表
    """
    query = db.query(OperationLog)
    
    if log_type is not None:
        query = query.filter(OperationLog.log_type == log_type)
    if model_id is not None:
        query = query.filter(OperationLog.model_id == model_id)
    if status is not None:
        query = query.filter(OperationLog.status == status)
    if start_time:
        query = query.filter(OperationLog.create_time >= start_time)
    if end_time:
        query = query.filter(OperationLog.create_time <= end_time)
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    logs = query.order_by(
        desc(OperationLog.create_time)
    ).offset((page - 1) * size).limit(size).all()
    
    return {
        "code": 200,
        "msg": "success",
        "data": [{
            "id": log.id,
            "log_type": log.log_type,
            "model_id": log.model_id,
            "log_content": log.log_content,
            "status": log.status,
            "create_time": log.create_time.strftime("%Y-%m-%d %H:%M:%S") if log.create_time else None
        } for log in logs],
        "total": total
    }

@logs_router.post("/api/log/clear")
async def clear_logs(
    log_type: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    清空日志
    """
    query = db.query(OperationLog)
    
    if log_type is not None:
        query = query.filter(OperationLog.log_type == log_type)
    
    deleted_count = query.count()
    query.delete(synchronize_session=False)
    db.commit()
    
    return {
        "code": 200,
        "msg": f"已清空 {deleted_count} 条日志"
    }

@logs_router.get("/api/log/export")
async def export_logs(
    log_type: Optional[int] = None,
    model_id: Optional[int] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    导出日志
    """
    query = db.query(OperationLog)
    
    if log_type is not None:
        query = query.filter(OperationLog.log_type == log_type)
    if model_id is not None:
        query = query.filter(OperationLog.model_id == model_id)
    if start_time:
        query = query.filter(OperationLog.create_time >= start_time)
    if end_time:
        query = query.filter(OperationLog.create_time <= end_time)
    
    logs = query.order_by(desc(OperationLog.create_time)).all()
    
    # 生成 CSV 格式
    csv_lines = ["ID,日志类型,模型ID,状态,创建时间,内容"]
    for log in logs:
        log_type_name = {1: "访问日志", 2: "切换日志", 3: "错误日志", 4: "测试日志"}.get(log.log_type, "未知")
        status_name = "成功" if log.status == 1 else "失败"
        content = (log.log_content or "").replace(",", "，").replace("\n", " ")
        create_time = log.create_time.strftime("%Y-%m-%d %H:%M:%S") if log.create_time else ""
        csv_lines.append(f"{log.id},{log_type_name},{log.model_id or ''},{status_name},{create_time},{content}")
    
    csv_content = "\n".join(csv_lines)
    
    from fastapi.responses import Response
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=logs.csv"}
    )
