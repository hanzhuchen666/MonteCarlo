from typing import List, Optional, Dict, Any
import uuid
import random
import abc

from events import Event


class EventGenerator(abc.ABC):
    """
    事件生成器基类（策略模式）
    定义"如何产生新事件"的接口，不同策略可热插拔
    """
    
    def __init__(self, generator_id: Optional[str] = None):
        self.id = generator_id or str(uuid.uuid4())
    
    @abc.abstractmethod
    def generate(self, current_time: float, **kwargs) -> Optional[Event]:
        """
        生成下一个事件
        
        Args:
            current_time: 当前仿真时间
            **kwargs: 额外参数
            
        Returns:
            生成的事件，如果不生成事件则返回None
        """
        pass
    
    @abc.abstractmethod
    def generate_next_time(self, current_time: float, **kwargs) -> Optional[float]:
        """
        生成下一个事件的时间
        
        Args:
            current_time: 当前仿真时间
            **kwargs: 额外参数
            
        Returns:
            下一个事件时间，如果不再生成事件则返回None
        """
        pass


class PoissonEventGenerator(EventGenerator):
    """使用泊松过程生成事件"""
    
    def __init__(self, 
                 event_type: str,
                 rate: float,
                 max_time: Optional[float] = None,
                 payload_factory: Optional[callable] = None,
                 generator_id: Optional[str] = None,
                 priority: int = 0):
        """
        Args:
            event_type: 生成的事件类型
            rate: 事件生成速率 (λ)
            max_time: 最大生成时间，超过后停止生成
            payload_factory: 可选的载荷生成函数，接收当前时间作为参数
            generator_id: 生成器ID
            priority: 生成事件的优先级
        """
        super().__init__(generator_id)
        self.event_type = event_type
        self.rate = rate
        self.max_time = max_time
        self.payload_factory = payload_factory
        self.priority = priority
    
    def generate_next_time(self, current_time: float, **kwargs) -> Optional[float]:
        """使用指数分布生成下一个事件时间"""
        if self.max_time is not None and current_time >= self.max_time:
            return None
        
        if self.rate <= 0:
            return None
            
        # 指数分布的时间间隔
        time_delta = random.expovariate(self.rate)
        next_time = current_time + time_delta
        
        if self.max_time is not None and next_time > self.max_time:
            return None
            
        return next_time
    
    def generate(self, current_time: float, **kwargs) -> Optional[Event]:
        """生成事件"""
        next_time = self.generate_next_time(current_time, **kwargs)
        
        if next_time is None:
            return None
            
        payload = {}
        if self.payload_factory:
            payload = self.payload_factory(next_time)
            
        return Event(
            time=next_time,
            event_type=self.event_type,
            generator_id=self.id,
            payload=payload,
            priority=self.priority
        )


class ScheduledEventGenerator(EventGenerator):
    """在预定义时间生成事件"""
    
    def __init__(self, 
                 event_type: str,
                 schedule: List[float],
                 payload_factory: Optional[callable] = None,
                 generator_id: Optional[str] = None,
                 priority: int = 0):
        """
        Args:
            event_type: 生成的事件类型
            schedule: 事件发生时间列表
            payload_factory: 可选的载荷生成函数，接收当前时间作为参数
            generator_id: 生成器ID
            priority: 生成事件的优先级
        """
        super().__init__(generator_id)
        self.event_type = event_type
        self.schedule = sorted(schedule)  # 确保时间有序
        self.current_index = 0
        self.payload_factory = payload_factory
        self.priority = priority
    
    def generate_next_time(self, current_time: float, **kwargs) -> Optional[float]:
        """从调度列表中获取下一个事件时间"""
        if self.current_index >= len(self.schedule):
            return None
            
        next_time = self.schedule[self.current_index]
        
        # 如果当前时间已经超过下一个事件时间，则跳过
        while next_time <= current_time and self.current_index < len(self.schedule) - 1:
            self.current_index += 1
            next_time = self.schedule[self.current_index]
            
        if next_time <= current_time:  # 已经没有未来事件
            self.current_index = len(self.schedule)  # 标记为已完成
            return None
            
        return next_time
    
    def generate(self, current_time: float, **kwargs) -> Optional[Event]:
        """生成事件"""
        next_time = self.generate_next_time(current_time, **kwargs)
        
        if next_time is None:
            return None
            
        self.current_index += 1  # 移动到下一个事件
        
        payload = {}
        if self.payload_factory:
            payload = self.payload_factory(next_time)
            
        return Event(
            time=next_time,
            event_type=self.event_type,
            generator_id=self.id,
            payload=payload,
            priority=self.priority
        )


class CompositeEventGenerator(EventGenerator):
    """组合多个事件生成器"""
    
    def __init__(self, generators: List[EventGenerator], generator_id: Optional[str] = None):
        """
        Args:
            generators: 事件生成器列表
            generator_id: 生成器ID
        """
        super().__init__(generator_id)
        self.generators = generators
        self._next_events = {}  # 缓存每个生成器的下一个事件
        
    def generate_next_time(self, current_time: float, **kwargs) -> Optional[float]:
        """找出所有生成器中最早的下一个事件时间"""
        min_time = None
        
        for generator in self.generators:
            next_time = generator.generate_next_time(current_time, **kwargs)
            if next_time is not None:
                if min_time is None or next_time < min_time:
                    min_time = next_time
                    
        return min_time
    
    def generate(self, current_time: float, **kwargs) -> Optional[Event]:
        """生成所有生成器中最早的下一个事件"""
        min_time = None
        selected_generator = None
        
        # 找出最早的事件和对应的生成器
        for generator in self.generators:
            next_time = generator.generate_next_time(current_time, **kwargs)
            if next_time is not None:
                if min_time is None or next_time < min_time:
                    min_time = next_time
                    selected_generator = generator
        
        if selected_generator is None:
            return None
            
        # 使用选中的生成器生成事件
        return selected_generator.generate(current_time, **kwargs) 