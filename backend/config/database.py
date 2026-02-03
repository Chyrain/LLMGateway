from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
import os
import sqlite3

Base = declarative_base()

# 数据库配置
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB_PATH = os.getenv("DB_PATH", "./data/llmgateway.db")

if DB_TYPE == "sqlite":
    DATABASE_URL = f"sqlite:///{DB_PATH}"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./llmgateway.db")

# 创建引擎
if DB_TYPE == "sqlite":
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)

# 创建会话工厂
session_factory = sessionmaker(bind=engine)
SessionLocal = scoped_session(session_factory)

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库表"""
    # 确保目录存在
    if DB_TYPE == "sqlite":
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)

def init_default_config():
    """初始化默认配置"""
    db = SessionLocal()
    try:
        # 检查是否已存在配置
        existing = db.query(SystemConfig).first()
        if not existing:
            default_configs = [
                {"config_key": "gateway_port", "config_value": "8080", "config_desc": "网关服务端口"},
                {"config_key": "switch_threshold", "config_value": "99", "config_desc": "自动切换阈值(%)"},
                {"config_key": "sync_interval", "config_value": "10", "config_desc": "额度同步间隔(秒)"},
                {"config_key": "log_retention", "config_value": "30", "config_desc": "日志保留天数"},
            ]
            
            for config in default_configs:
                db.add(SystemConfig(**config))
            db.commit()
    finally:
        db.close()
