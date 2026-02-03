from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from config.database import Base

class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_type = Column(Integer, default=1, comment="日志类型: 1=访问日志, 2=切换日志, 3=错误日志, 4=测试日志")
    model_id = Column(Integer, comment="关联模型ID")
    log_content = Column(Text, comment="日志内容(脱敏)")
    status = Column(Integer, default=1, comment="状态: 0=失败, 1=成功")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
