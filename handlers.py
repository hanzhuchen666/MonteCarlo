from typing import List, Dict, Optional, Any, Set, Callable
import abc
from events import Event


class EventHandler(abc.ABC):
    """
    事件处理器基类（策略模式和模板方法模式）
    定义"事件发生后如何处理"，解耦处理逻辑
    """
    
    def __init__(self, handler_id: Optional[str] = None):
        self.id = handler_id or f"{self.__class__.__name__}"
        self.event_types: Set[str] = set()  # 处理的事件类型
        
    def can_handle(self, event: Event) -> bool:
        """判断是否可以处理该事件"""
        return len(self.event_types) == 0 or event.event_type in self.event_types
    
    def handle(self, event: Event, timeline, stats) -> List[Event]:
        """
        模板方法：处理事件的通用流程
        
        Args:
            event: 要处理的事件
            timeline: 时间轴对象
            stats: 统计对象
            
        Returns:
            由此事件触发的新事件列表
        """
        if not self.can_handle(event):
            return []
        
        # 前置处理
        self.pre_handle(event, timeline, stats)
        
        # 核心处理逻辑
        new_events = self.process_event(event, timeline, stats)
        
        # 后置处理
        self.post_handle(event, new_events, timeline, stats)
        
        return new_events
    
    def pre_handle(self, event: Event, timeline, stats) -> None:
        """事件处理前的操作"""
        pass
    
    @abc.abstractmethod
    def process_event(self, event: Event, timeline, stats) -> List[Event]:
        """
        处理事件的核心逻辑，需要子类实现
        
        Returns:
            由此事件触发的新事件列表
        """
        pass
    
    def post_handle(self, event: Event, new_events: List[Event], timeline, stats) -> None:
        """事件处理后的操作"""
        pass


class LoggingEventHandler(EventHandler):
    """记录事件处理过程的处理器"""
    
    def __init__(self, handler_id: Optional[str] = None, log_func: Callable = print):
        super().__init__(handler_id)
        self.log_func = log_func
    
    def pre_handle(self, event: Event, timeline, stats) -> None:
        """记录事件开始处理"""
        self.log_func(f"开始处理事件: {event.event_type} 在时间 {event.time}")
    
    def process_event(self, event: Event, timeline, stats) -> List[Event]:
        """简单记录事件，不生成新事件"""
        self.log_func(f"事件详情: {event.payload}")
        return []
    
    def post_handle(self, event: Event, new_events: List[Event], timeline, stats) -> None:
        """记录事件处理结束"""
        if new_events:
            self.log_func(f"处理完成，生成了 {len(new_events)} 个新事件")
        else:
            self.log_func(f"处理完成，没有生成新事件")


class StatsCollectingHandler(EventHandler):
    """收集统计数据的处理器"""
    
    def __init__(self, event_types: Set[str], handler_id: Optional[str] = None):
        super().__init__(handler_id)
        self.event_types = event_types
    
    def process_event(self, event: Event, timeline, stats) -> List[Event]:
        """记录事件统计信息"""
        # 增加事件计数
        stats.increment_count(event.event_type)
        
        # 记录事件特定数据
        for key, value in event.payload.items():
            if isinstance(value, (int, float)):
                stats.add_value(f"{event.event_type}.{key}", value)
                
        return []


class ChainHandler(EventHandler):
    """链式处理器，将多个处理器串联起来"""
    
    def __init__(self, handlers: List[EventHandler], handler_id: Optional[str] = None):
        super().__init__(handler_id)
        self.handlers = handlers
        
        # 汇总所有处理器的事件类型
        for handler in handlers:
            self.event_types.update(handler.event_types)
    
    def process_event(self, event: Event, timeline, stats) -> List[Event]:
        """依次使用各个处理器处理事件"""
        all_new_events = []
        
        for handler in self.handlers:
            if handler.can_handle(event):
                new_events = handler.process_event(event, timeline, stats)
                all_new_events.extend(new_events)
                
        return all_new_events


class ConditionalHandler(EventHandler):
    """条件处理器，根据条件决定使用哪个处理器"""
    
    def __init__(self, 
                 condition_func: Callable[[Event], bool],
                 true_handler: EventHandler,
                 false_handler: Optional[EventHandler] = None,
                 handler_id: Optional[str] = None):
        """
        Args:
            condition_func: 条件函数，接收事件返回布尔值
            true_handler: 条件为真时使用的处理器
            false_handler: 条件为假时使用的处理器，可选
            handler_id: 处理器ID
        """
        super().__init__(handler_id)
        self.condition_func = condition_func
        self.true_handler = true_handler
        self.false_handler = false_handler
        
        # 汇总所有处理器的事件类型
        self.event_types.update(true_handler.event_types)
        if false_handler:
            self.event_types.update(false_handler.event_types)
    
    def process_event(self, event: Event, timeline, stats) -> List[Event]:
        """根据条件选择处理器"""
        if self.condition_func(event):
            if self.true_handler.can_handle(event):
                return self.true_handler.process_event(event, timeline, stats)
        elif self.false_handler and self.false_handler.can_handle(event):
            return self.false_handler.process_event(event, timeline, stats)
            
        return []


class EventDispatcher:
    """事件分发器，根据事件类型将事件分发给对应的处理器"""
    
    def __init__(self):
        self.handlers: Dict[str, List[EventHandler]] = {}  # 按事件类型索引的处理器
        self.default_handlers: List[EventHandler] = []  # 处理所有事件类型的处理器
    
    def register_handler(self, handler: EventHandler) -> None:
        """注册处理器"""
        if not handler.event_types:  # 没有指定事件类型，作为默认处理器
            self.default_handlers.append(handler)
            return
            
        # 根据事件类型注册
        for event_type in handler.event_types:
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            self.handlers[event_type].append(handler)
    
    def dispatch(self, event: Event, timeline, stats) -> List[Event]:
        """分发事件到对应的处理器"""
        all_new_events = []
        
        # 调用特定事件类型的处理器
        if event.event_type in self.handlers:
            for handler in self.handlers[event.event_type]:
                new_events = handler.handle(event, timeline, stats)
                all_new_events.extend(new_events)
        
        # 调用默认处理器
        for handler in self.default_handlers:
            new_events = handler.handle(event, timeline, stats)
            all_new_events.extend(new_events)
            
        return all_new_events 