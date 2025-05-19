"""
示例：M/M/3 排队系统仿真

本示例模拟一个简单的队列系统（如银行柜台服务），包含：
1. 客户到达（泊松过程）
2. 服务时间（指数分布）
3. 等待队列
4. 服务完成后客户离开

统计指标：
- 平均等待时间
- 平均队列长度
- 服务台利用率
"""

import random
from typing import List, Set, Dict, Any

from MC.parameters import ParameterBuilder
from MC.events import Event
from MC.generators import PoissonEventGenerator
from MC.handlers import EventHandler
from MC.timeline import TimeLine
from MC.stats import Stats
from MC.simulator import Simulator

import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文显示
plt.rcParams['axes.unicode_minus'] = False  # 设置负号显示


# 定义事件类型
EVENT_ARRIVAL = "customer_arrival"
EVENT_SERVICE_START = "service_start"
EVENT_SERVICE_END = "service_end"


class QueueSystem:
    """队列系统状态"""
    
    def __init__(self, num_servers: int = 1):
        self.queue: List[Event] = []  # 等待队列
        self.servers_busy: int = 0    # 繁忙服务台数量
        self.num_servers = num_servers
        
    @property
    def queue_length(self) -> int:
        """队列长度"""
        return len(self.queue)
    
    @property
    def servers_available(self) -> int:
        """可用服务台数量"""
        return self.num_servers - self.servers_busy
    
    @property
    def is_server_available(self) -> bool:
        """是否有可用服务台"""
        return self.servers_available > 0
    
    def add_to_queue(self, event: Event) -> None:
        """添加客户到队列"""
        self.queue.append(event)
    
    def next_from_queue(self) -> Event:
        """从队列获取下一个客户"""
        if not self.queue:
            raise ValueError("队列为空")
        return self.queue.pop(0)


class ArrivalHandler(EventHandler):
    """处理客户到达事件"""
    
    def __init__(self, queue_system: QueueSystem, service_time_generator, arrival_generator: PoissonEventGenerator, handler_id: str = None):
        super().__init__(handler_id)
        self.event_types = {EVENT_ARRIVAL}
        self.queue_system = queue_system
        self.service_time_generator = service_time_generator
        self.arrival_generator = arrival_generator
    
    def process_event(self, event: Event, timeline, stats) -> List[Event]:
        """处理客户到达"""
        stats.increment_count("total_arrivals")
        stats.add_time_point("queue_length", timeline.current_time, self.queue_system.queue_length)
        
        # 记录到达时间
        arrival_time = event.time
        event.add_payload("arrival_time", arrival_time)
        
        new_events = []
        
        # 生成下一个到达事件
        next_arrival = self.arrival_generator.generate(timeline.current_time)
        if next_arrival:
            new_events.append(next_arrival)
        
        # 如果有空闲服务台，直接开始服务
        if self.queue_system.is_server_available:
            self.queue_system.servers_busy += 1
            
            # 生成服务结束事件
            service_time = self.service_time_generator()
            service_end_time = timeline.current_time + service_time
            
            service_event = Event(
                time=service_end_time,
                event_type=EVENT_SERVICE_END,
                priority=0,
                payload={
                    "customer_id": event.payload.get("customer_id"),
                    "arrival_time": arrival_time,
                    "service_start_time": timeline.current_time,
                    "service_time": service_time
                }
            )
            new_events.append(service_event)
            
            # 记录服务开始
            stats.increment_count("services_started")
            stats.add_time_point("servers_busy", timeline.current_time, self.queue_system.servers_busy)
            
            # 计算等待时间
            wait_time = timeline.current_time - arrival_time
            stats.add_value("wait_time", wait_time)
        else:
            # 如果没有空闲服务台，加入队列
            self.queue_system.add_to_queue(event)
        
        return new_events


class ServiceEndHandler(EventHandler):
    """处理服务结束事件"""
    
    def __init__(self, queue_system: QueueSystem, service_time_generator, handler_id: str = None):
        super().__init__(handler_id)
        self.event_types = {EVENT_SERVICE_END}
        self.queue_system = queue_system
        self.service_time_generator = service_time_generator
    
    def process_event(self, event: Event, timeline, stats) -> List[Event]:
        """处理服务结束"""
        stats.increment_count("services_completed")
        
        # 计算系统时间（从到达到离开）
        arrival_time = event.payload.get("arrival_time")
        system_time = timeline.current_time - arrival_time
        stats.add_value("system_time", system_time)
        
        # 记录服务时间
        service_time = event.payload.get("service_time")
        stats.add_value("service_time", service_time)
        
        new_events = []
        
        # 检查队列是否有等待的客户
        if self.queue_system.queue_length > 0:
            # 获取下一个客户
            next_event = self.queue_system.next_from_queue()
            
            # 生成服务结束事件
            service_time = self.service_time_generator()
            service_end_time = timeline.current_time + service_time
            
            service_event = Event(
                time=service_end_time,
                event_type=EVENT_SERVICE_END,
                priority=0,
                payload={
                    "customer_id": next_event.payload.get("customer_id"),
                    "arrival_time": next_event.payload.get("arrival_time"),
                    "service_start_time": timeline.current_time,
                    "service_time": service_time
                }
            )
            new_events.append(service_event)
            
            # 记录服务开始
            stats.increment_count("services_started")
            
            # 计算等待时间
            wait_time = timeline.current_time - next_event.payload.get("arrival_time")
            stats.add_value("wait_time", wait_time)
        else:
            # 如果没有等待的客户，释放服务台
            self.queue_system.servers_busy -= 1
        
        # 更新统计信息
        stats.add_time_point("queue_length", timeline.current_time, self.queue_system.queue_length)
        stats.add_time_point("servers_busy", timeline.current_time, self.queue_system.servers_busy)
        
        return new_events


def customer_payload_factory(time):
    """创建客户负载"""
    return {
        "customer_id": f"C-{int(time*100):06d}"
    }


def run_queue_simulation(arrival_rate: float, service_rate: float, 
                        num_servers: int, simulation_time: float):
    """
    运行队列系统仿真
    
    Args:
        arrival_rate: 客户到达率（每单位时间）
        service_rate: 服务率（每单位时间）
        num_servers: 服务台数量
        simulation_time: 仿真总时间
    """
    # 创建参数集
    params = (ParameterBuilder()
        .add_float("arrival_rate", arrival_rate, min_value=0.0, 
                  description="客户到达率（泊松过程参数λ）")
        .add_float("service_rate", service_rate, min_value=0.0,
                  description="服务率（指数分布参数μ）")
        .add_integer("num_servers", num_servers, min_value=1,
                    description="服务台数量")
        .add_float("simulation_time", simulation_time, min_value=0.0,
                  description="仿真总时间")
        .build())
    
    # 创建队列系统
    queue_system = QueueSystem(num_servers=num_servers)
    
    # 创建服务时间生成器（指数分布）
    def generate_service_time():
        return random.expovariate(service_rate)
    
    # 创建事件生成器
    arrival_generator = PoissonEventGenerator(
        event_type=EVENT_ARRIVAL,
        rate=arrival_rate,
        max_time=simulation_time,
        payload_factory=customer_payload_factory
    )
    
    # 创建事件处理器
    arrival_handler = ArrivalHandler(queue_system, generate_service_time, arrival_generator)
    service_end_handler = ServiceEndHandler(queue_system, generate_service_time)
    
    # 创建并配置模拟器
    simulator = Simulator(params)
    simulator.add_generator(arrival_generator)
    simulator.add_handler(arrival_handler)
    simulator.add_handler(service_end_handler)
    simulator.set_max_time(simulation_time)
    simulator.set_verbose(True)
    
    # 运行模拟
    stats = simulator.run()
    
    # 计算最终指标
    arrivals = stats.get_count("total_arrivals")
    completions = stats.get_count("services_completed")
    avg_wait_time = stats.get_average("wait_time") or 0
    avg_service_time = stats.get_average("service_time") or 0
    avg_system_time = stats.get_average("system_time") or 0
    
    # 计算利用率
    utilization = stats.get_sum("service_time") / (num_servers * simulation_time)
    stats.set_custom_stat("server_utilization", utilization)
    
    # 打印结果
    print("\n===== 队列系统仿真结果 =====")
    print(f"模拟时间: {simulation_time}")
    print(f"到达率: {arrival_rate} 客户/单位时间")
    print(f"服务率: {service_rate} 客户/单位时间")
    print(f"服务台数: {num_servers}")
    print(f"总到达客户: {arrivals}")
    print(f"完成服务客户: {completions}")
    print(f"平均等待时间: {avg_wait_time:.4f}")
    print(f"平均服务时间: {avg_service_time:.4f}")
    print(f"平均系统时间: {avg_system_time:.4f}")
    print(f"服务台利用率: {utilization:.4f}")
    print("============================")
    
    # 导出结果
    simulator.export_results(json_path="queue_results.json", csv_path="queue_results.csv")
    
    # 绘制时间序列图表
    stats.plot_time_series("queue_length", title="队列长度变化", 
                         ylabel="队列长度", save_path="queue_length.png")
    stats.plot_time_series("servers_busy", title="繁忙服务台数量变化", 
                         ylabel="繁忙服务台数", save_path="servers_busy.png")
    
    return stats


if __name__ == "__main__":
    # 示例参数
    arrival_rate = 5.0   # 平均每单位时间到达5个客户
    service_rate = 2.0   # 平均每单位时间服务2个客户（平均服务时间为0.5单位时间）
    num_servers = 3      # 3个服务台
    simulation_time = 100.0  # 模拟100个单位时间
    
    # 运行模拟
    run_queue_simulation(arrival_rate, service_rate, num_servers, simulation_time) 