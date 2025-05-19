from typing import List, Dict, Any, Optional, Callable
import time

from .parameters import ParameterSet
from .events import Event
from .generators import EventGenerator
from .handlers import EventHandler, EventDispatcher
from .timeline import TimeLine
from .stats import Stats, ConsoleStatsObserver


class Simulator:
    """
    将各模块组合起来，提供统一的运行接口（外观模式）
    """
    
    def __init__(self, parameters: Optional[ParameterSet] = None):
        """
        初始化模拟器
        
        Args:
            parameters: 可选的参数集
        """
        self.parameters = parameters or ParameterSet()
        self.timeline = TimeLine()
        self.stats = Stats()
        self.dispatcher = EventDispatcher()
        self.generators: List[EventGenerator] = []
        self.stop_condition: Optional[Callable[[TimeLine, Stats], bool]] = None
        self.max_time: float = float('inf')
        self.max_events: int = float('inf')
        self.verbose: bool = False
        
    def add_generator(self, generator: EventGenerator) -> 'Simulator':
        """添加事件生成器"""
        self.generators.append(generator)
        return self
        
    def add_handler(self, handler: EventHandler) -> 'Simulator':
        """添加事件处理器"""
        self.dispatcher.register_handler(handler)
        return self
        
    def set_stop_condition(self, condition: Callable[[TimeLine, Stats], bool]) -> 'Simulator':
        """设置停止条件"""
        self.stop_condition = condition
        return self
        
    def set_max_time(self, max_time: float) -> 'Simulator':
        """设置最大模拟时间"""
        self.max_time = max_time
        return self
        
    def set_max_events(self, max_events: int) -> 'Simulator':
        """设置最大事件数"""
        self.max_events = max_events
        return self
        
    def set_verbose(self, verbose: bool) -> 'Simulator':
        """设置是否输出详细信息"""
        self.verbose = verbose
        if verbose:
            self.stats.add_observer(ConsoleStatsObserver())
        return self
        
    def initialize(self) -> None:
        """初始化模拟"""
        # 重置时间轴和统计
        self.timeline.reset()
        self.stats.reset()
        
        # 从生成器生成初始事件
        self.generate_initial_events()
        
        if self.verbose:
            print(f"初始化完成，队列中有 {self.timeline.size()} 个事件")
    
    def generate_initial_events(self) -> None:
        """从所有生成器生成初始事件"""
        current_time = self.timeline.current_time
        
        for generator in self.generators:
            event = generator.generate(current_time)
            if event:
                self.timeline.schedule_event(event)
                if self.verbose:
                    print(f"生成初始事件: {event.event_type} 在时间 {event.time}")
    
    def run(self) -> Stats:
        """
        运行模拟
        
        Returns:
            统计对象
        """
        self.initialize()
        
        start_time = time.time()
        processed_events = 0
        
        # 主循环
        while not self.timeline.is_empty:
            # 获取下一个事件
            event = self.timeline.get_next_event()
            processed_events += 1
            
            # 检查是否超过最大时间
            if event.time > self.max_time:
                if self.verbose:
                    print(f"达到最大模拟时间 {self.max_time}")
                break
                
            # 检查是否超过最大事件数
            if processed_events > self.max_events:
                if self.verbose:
                    print(f"达到最大事件数 {self.max_events}")
                break
                
            # 检查自定义停止条件
            if self.stop_condition and self.stop_condition(self.timeline, self.stats):
                if self.verbose:
                    print("满足停止条件，模拟结束")
                break
            
            # 处理事件并获取新事件
            new_events = self.dispatcher.dispatch(event, self.timeline, self.stats)
            
            # 添加新事件到时间轴
            for new_event in new_events:
                if new_event.time >= self.timeline.current_time:
                    self.timeline.schedule_event(new_event)
                else:
                    if self.verbose:
                        print(f"警告: 事件 {new_event.event_type} 被安排在过去的时间 {new_event.time}，当前时间为 {self.timeline.current_time}")
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # 记录模拟统计信息
        self.stats.set_custom_stat("simulation_time", elapsed)
        self.stats.set_custom_stat("processed_events", processed_events)
        self.stats.set_custom_stat("final_simulation_time", self.timeline.current_time)
        
        if self.verbose:
            print(f"模拟完成，处理了 {processed_events} 个事件")
            print(f"模拟时间: {self.timeline.current_time}")
            print(f"实际耗时: {elapsed:.4f} 秒")
        
        return self.stats
    
    def _generate_new_events(self) -> None:
        """从所有生成器生成新事件"""
        current_time = self.timeline.current_time
        
        for generator in self.generators:
            event = generator.generate(current_time)
            if event:
                self.timeline.schedule_event(event)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取模拟结果摘要"""
        return self.stats.get_summary()
    
    def export_results(self, json_path: Optional[str] = None, 
                      csv_path: Optional[str] = None) -> None:
        """导出模拟结果"""
        if json_path:
            self.stats.export_to_json(json_path)
            if self.verbose:
                print(f"结果已导出到 {json_path}")
                
        if csv_path:
            self.stats.export_to_csv(csv_path, include_time_series=True)
            if self.verbose:
                print(f"结果已导出到 {csv_path}")
                
    def reset(self) -> None:
        """重置模拟器状态"""
        self.timeline.reset()
        self.stats.reset() 