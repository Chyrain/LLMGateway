"""
通知 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from config.database import get_db
from models.notification import Notification

notification_router = APIRouter()

class CreateNotificationRequest(BaseModel):
    title: str
    content: str
    type: str = "info"  # info, warning, success, error

class NotificationResponse(BaseModel):
    id: int
    title: str
    content: str
    type: str
    is_read: bool
    created_at: Optional[str]
    read_at: Optional[str]

@notification_router.post("/api/notifications")
async def create_notification(
    request: CreateNotificationRequest,
    db: Session = Depends(get_db)
):
    """
    创建新通知
    """
    notification = Notification(
        title=request.title,
        content=request.content,
        type=request.type,
        is_read=False
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    return {
        "code": 200,
        "msg": "创建成功",
        "data": notification.to_dict()
    }

@notification_router.get("/api/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取通知列表
    """
    query = db.query(Notification)
    
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    if notification_type:
        query = query.filter(Notification.type == notification_type)
    
    total = query.count()
    notifications = query.order_by(
        desc(Notification.created_at)
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return notifications

@notification_router.put("/api/notifications/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """
    标记通知为已读
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    notification.is_read = True
    notification.read_at = datetime.now()
    db.commit()
    
    return {"code": 200, "msg": "已标记为已读"}

@notification_router.put("/api/notifications/read-all")
async def mark_all_as_read(
    db: Session = Depends(get_db)
):
    """
    标记所有通知为已读
    """
    db.query(Notification).filter(
        Notification.is_read == False
    ).update({
        "is_read": True,
        "read_at": datetime.now()
    })
    db.commit()
    
    return {"code": 200, "msg": "已全部标记为已读"}

@notification_router.delete("/api/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """
    删除通知
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    db.delete(notification)
    db.commit()
    
    return {"code": 200, "msg": "删除成功"}

@notification_router.get("/api/notifications/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db)
):
    """
    获取未读通知数量
    """
    count = db.query(Notification).filter(
        Notification.is_read == False
    ).count()
    
    return {"code": 200, "msg": "success", "data": {"count": count}}

@notification_router.delete("/api/notifications/clear-read")
async def clear_read_notifications(
    db: Session = Depends(get_db)
):
    """
    清除所有已读通知
    """
    db.query(Notification).filter(
        Notification.is_read == True
    ).delete()
    db.commit()
    
    return {"code": 200, "msg": "清除成功"}
