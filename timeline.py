from typing import List, Optional, Dict, Any, Callable
import heapq
from events import Event


class TimeLine:
    """
    维护一个按时间排序的事件队列
    """
    
    def __init__(self):
        self._event_queue = []  # 使用堆来维护事件优先级
        self._current_time = 0.0  # 当前仿真时间
        self._event_id_counter = 0  # 用于确保具有相同时间的事件保持插入顺序
        
    @property
    def current_time(self) -> float:
        """获取当前仿真时间"""
        return self._current_time
    
    @property
    def is_empty(self) -> bool:
        """检查事件队列是否为空"""
        return len(self._event_queue) == 0
    
    def size(self) -> int:
        """获取队列中的事件数量"""
        return len(self._event_queue)
        
    def schedule_event(self, event: Event) -> None:
        """
        将事件添加到时间轴
        
        Args:
            event: 要添加的事件
        """
        # 确保事件时间不早于当前时间
        if event.time < self._current_time:
            raise ValueError(f"Cannot schedule event in the past. Current time: {self._current_time}, Event time: {event.time}")
        
        # 使用heapq保持事件队列有序
        # 使用元组(事件时间, 插入顺序, 事件对象)作为堆元素，以确保稳定排序
        self._event_id_counter += 1
        heapq.heappush(self._event_queue, (event.time, -event.priority, self._event_id_counter, event))
    
    def schedule_events(self, events: List[Event]) -> None:
        """
        将多个事件添加到时间轴
        
        Args:
            events: 要添加的事件列表
        """
        for event in events:
            self.schedule_event(event)
            
    def peek_next_event(self) -> Optional[Event]:
        """
        查看下一个事件，但不从队列中移除
        
        Returns:
            下一个事件，如果队列为空则返回None
        """
        if self.is_empty:
            return None
        return self._event_queue[0][3]  # 返回堆顶元素中的事件对象
    
    def peek_next_time(self) -> Optional[float]:
        """
        查看下一个事件的时间，但不从队列中移除事件
        
        Returns:
            下一个事件的时间，如果队列为空则返回None
        """
        if self.is_empty:
            return None
        return self._event_queue[0][0]  # 返回堆顶元素中的时间
        
    def get_next_event(self) -> Optional[Event]:
        """
        获取并移除下一个事件
        
        Returns:
            下一个事件，如果队列为空则返回None
        """
        if self.is_empty:
            return None
            
        _, _, _, event = heapq.heappop(self._event_queue)
        self._current_time = event.time  # 更新当前时间
        return event
    
    def clear(self) -> None:
        """清空事件队列"""
        self._event_queue = []
    
    def reset(self) -> None:
        """重置时间轴状态"""
        self.clear()
        self._current_time = 0.0
        self._event_id_counter = 0 