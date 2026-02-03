from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from config.database import Base

class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False, comment="配置键")
    config_value = Column(Text, comment="配置值")
    config_desc = Column(String(255), comment="配置描述")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
