from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import uuid


@dataclass
class Event:
    """
    表示仿真中"发生"的一次事件，包含触发时间、生成源、负载等信息
    """
    # 事件发生的时间
    time: float
    
    # 事件类型
    event_type: str
    
    # 事件产生器ID（可选）
    generator_id: Optional[str] = None
    
    # 事件载荷，可以包含任何信息
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # 唯一标识符
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # 优先级（同一时间点，高优先级事件先处理）
    priority: int = 0
    
    def __lt__(self, other):
        """用于事件比较和排序，先按时间，再按优先级"""
        if self.time != other.time:
            return self.time < other.time
        return self.priority > other.priority  # 高优先级值排在前面
    
    def __eq__(self, other):
        """判断两个事件是否相同"""
        if not isinstance(other, Event):
            return False
        return self.id == other.id
    
    def copy_with_new_time(self, new_time: float) -> 'Event':
        """创建一个时间点不同的事件副本"""
        return Event(
            time=new_time,
            event_type=self.event_type,
            generator_id=self.generator_id,
            payload=self.payload.copy(),
            priority=self.priority
        )
    
    def add_payload(self, key: str, value: Any) -> 'Event':
        """添加负载数据"""
        self.payload[key] = value
        return self 