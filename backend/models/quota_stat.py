from sqlalchemy import Column, Integer, Float, DateTime
from datetime import datetime
from config.database import Base

class QuotaStat(Base):
    """额度统计表"""
    __tablename__ = "quota_stat"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, nullable=False, comment="关联模型ID")
    total_quota = Column(Float, default=0, comment="总免费额度(Tokens)")
    used_quota = Column(Float, default=0, comment="已用额度")
    remain_quota = Column(Float, default=0, comment="剩余额度")
    used_ratio = Column(Float, default=0, comment="消耗占比(%)")
    sync_type = Column(Integer, default=0, comment="同步类型: 0=手动, 1=自动")
    last_sync_time = Column(DateTime, comment="最后同步时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
