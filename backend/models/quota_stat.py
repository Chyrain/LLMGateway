from sqlalchemy import Column, Integer, Float, DateTime, String
from datetime import datetime
from config.database import Base

class QuotaStat(Base):
    """额度统计表"""
    __tablename__ = "quota_stat"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, nullable=False, comment="关联模型ID")
    plan_type = Column(
        String(20),
        default="default",
        comment="计划类型: default=默认, coding=Coding计划, reasoning=推理计划",
    )
    plan_name = Column(
        String(100),
        default="",
        comment="计划名称（如：MiniMax M2.5 Coding Plan）",
    )
    # 配额单位：tokens=Token数, prompts=请求次数
    quota_unit = Column(
        String(20),
        default="tokens",
        comment="配额单位: tokens=Token数, prompts=请求次数",
    )
    # 周期小时数（0表示无周期限制）
    period_hours = Column(
        Integer,
        default=0,
        comment="周期小时数（如5表示5小时周期，0表示无周期）",
    )
    # 周期开始时间
    period_start = Column(
        DateTime,
        comment="当前周期开始时间",
    )
    # 周期内已使用次数
    period_used = Column(
        Integer,
        default=0,
        comment="当前周期内已使用次数",
    )
    total_quota = Column(Float, default=0, comment="总免费额度(Tokens)")
    used_quota = Column(Float, default=0, comment="已用额度")
    remain_quota = Column(Float, default=0, comment="剩余额度")
    used_ratio = Column(Float, default=0, comment="消耗占比(%)")
    sync_type = Column(Integer, default=0, comment="同步类型: 0=手动, 1=自动")
    last_sync_time = Column(DateTime, comment="最后同步时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
