from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from config.database import Base
from datetime import datetime

class Notification(Base):
    """通知消息表"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment='通知标题')
    content = Column(Text, comment='通知内容')
    type = Column(String(50), default='info', comment='通知类型: info, warning, success, error')
    is_read = Column(Boolean, default=False, comment='是否已读')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    read_at = Column(DateTime, nullable=True, comment='阅读时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'read_at': self.read_at.strftime('%Y-%m-%d %H:%M:%S') if self.read_at else None
        }
