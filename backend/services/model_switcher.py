import asyncio
import json
from datetime import datetime
from typing import Optional

class ModelSwitcher:
    """模型自动切换服务"""
    
    def __init__(self, threshold: float = 99.0):
        self.threshold = threshold
        self.current_model_id: Optional[int] = None
        self.switch_history = []
    
    def should_switch(self, used_ratio: float, quota_status: int) -> bool:
        """判断是否应该切换模型"""
        # 额度状态为0(已耗尽)时必须切换
        if quota_status == 0:
            return True
        # 超过阈值时切换
        if used_ratio >= self.threshold:
            return True
        return False
    
    def get_next_model(self, models: list, current_id: int) -> Optional[dict]:
        """获取下一个可用模型"""
        # 按优先级排序
        sorted_models = sorted(
            [m for m in models if m["id"] != current_id and m["status"] == 1],
            key=lambda x: x["priority"]
        )
        
        if sorted_models:
            return sorted_models[0]
        return None
    
    async def switch(
        self,
        from_model: dict,
        to_model: dict,
        reason: str
    ) -> bool:
        """执行模型切换"""
        if not to_model:
            return False
        
        # 记录切换日志
        switch_record = {
            "from_model": from_model["name"],
            "to_model": to_model["name"],
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        self.switch_history.append(switch_record)
        self.current_model_id = to_model["id"]
        
        return True
    
    def get_switch_stats(self) -> dict:
        """获取切换统计"""
        return {
            "total_switches": len(self.switch_history),
            "last_switch": self.switch_history[-1] if self.switch_history else None,
            "history": self.switch_history[-10:]  # 最近10次切换
        }
