from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from datetime import datetime
from config.database import Base


class OperationLog(Base):
    """操作日志表"""

    __tablename__ = "operation_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_type = Column(
        Integer,
        default=1,
        comment="日志类型: 1=访问日志, 2=切换日志, 3=错误日志, 4=测试日志",
    )
    model_id = Column(Integer, comment="关联模型ID")
    log_content = Column(Text, comment="日志内容(脱敏)")
    status = Column(Integer, default=1, comment="状态: 0=失败, 1=成功")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")

    # 新增字段 - 详细日志信息
    request_time = Column(DateTime, comment="请求开始时间")
    response_time = Column(DateTime, comment="响应完成时间")
    duration_ms = Column(Float, comment="请求耗时(毫秒)")
    client_ip = Column(String(50), comment="客户端IP")
    user_agent = Column(String(500), comment="客户端User-Agent")
    request_model = Column(String(100), comment="请求的模型名称")
    actual_model = Column(String(100), comment="实际使用的模型名称")
    vendor = Column(String(50), comment="厂商名称")
    request_content = Column(Text, comment="请求内容(JSON格式)")
    response_content = Column(Text, comment="响应内容(JSON格式)")
    tokens_prompt = Column(Integer, comment="输入token数")
    tokens_completion = Column(Integer, comment="输出token数")
    tokens_total = Column(Integer, comment="总token数")
    error_message = Column(Text, comment="错误信息")
