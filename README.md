# 事件驱动的通用 Monte Carlo 模拟器

这是一个基于事件驱动模型的通用蒙特卡洛模拟器框架，设计符合多种设计模式，使用户可以通过修改事件生成器和事件处理器快速适应各种模拟场景。

## 设计概述

模拟器包含以下主要模块，每个模块都有特定的职责和设计模式：

| 模块 | 主要类 | 职责 | 设计模式 |
|-----|-------|-----|---------|
| parameters | Parameter | 封装仿真所需的全部参数，可统一管理和校验 | Builder（用于复杂参数构造） |
| events | Event | 表示仿真中"发生"的一次事件，包含触发时间、生成源、负载等信息 | — |
| generators | EventGenerator | 定义"如何产生新事件"，不同策略可热插拔 | Strategy |
| handlers | EventHandler | 定义"事件发生后如何处理"，解耦处理逻辑 | Strategy, Template Method |
| timeline | TimeLine | 维护一个按时间排序的事件队列 | — |
| stats | Stats | 收集、汇总、输出仿真过程中的各类统计数据 | Observer |
| simulator | Simulator | 将上述模块组合起来，提供统一的运行接口 | Facade |

## 快速开始

### 安装

1. 克隆仓库:
```bash
git clone https://github.com/yourusername/monte-carlo-simulator.git
cd monte-carlo-simulator
```

2. 安装依赖:
```bash
pip install -r requirements.txt
```

### 运行示例

项目包含一个队列系统的模拟示例，可以通过以下命令运行：

```bash
python demo.py
```

这将模拟一个有3个服务台的排队系统，客户到达遵循泊松过程，服务时间遵循指数分布。

## 如何使用框架

### 1. 定义参数

使用 `ParameterBuilder` 创建参数集：

```python
from parameters import ParameterBuilder

params = (ParameterBuilder()
    .add_float("arrival_rate", 5.0, min_value=0.0)
    .add_integer("max_customers", 1000, min_value=1)
    .add_float("simulation_time", 100.0, min_value=0.0)
    .build())
```

### 2. 创建事件生成器

继承 `EventGenerator` 创建自定义事件生成器，或使用内置的生成器：

```python
from generators import PoissonEventGenerator

arrival_generator = PoissonEventGenerator(
    event_type="customer_arrival",
    rate=5.0,  # 平均每单位时间5个客户
    max_time=100.0
)
```

### 3. 创建事件处理器

继承 `EventHandler` 创建自定义事件处理器：

```python
from handlers import EventHandler
from events import Event
from typing import List

class MyEventHandler(EventHandler):
    def __init__(self):
        super().__init__()
        self.event_types = {"customer_arrival"}  # 处理的事件类型
    
    def process_event(self, event: Event, timeline, stats) -> List[Event]:
        # 处理事件
        stats.increment_count("arrivals")
        
        # 返回由此事件触发的新事件
        return []
```

### 4. 配置和运行模拟器

```python
from simulator import Simulator

# 创建模拟器
simulator = Simulator(params)
simulator.add_generator(arrival_generator)
simulator.add_handler(my_handler)
simulator.set_max_time(100.0)
simulator.set_verbose(True)  # 打印详细信息

# 运行模拟
stats = simulator.run()

# 导出结果
simulator.export_results(json_path="results.json", csv_path="results.csv")

# 访问统计数据
avg_wait_time = stats.get_average("wait_time")
print(f"平均等待时间: {avg_wait_time}")

# 绘制结果
stats.plot_time_series("queue_length", title="队列长度变化")
```

## 扩展和定制

### 创建自定义事件生成器

继承 `EventGenerator` 并实现 `generate` 和 `generate_next_time` 方法：

```python
from generators import EventGenerator
from events import Event

class MyCustomGenerator(EventGenerator):
    def generate_next_time(self, current_time: float, **kwargs) -> float:
        # 实现生成下一个事件时间的逻辑
        return current_time + 1.0  # 简单示例
    
    def generate(self, current_time: float, **kwargs) -> Event:
        # 实现生成事件的逻辑
        next_time = self.generate_next_time(current_time)
        return Event(time=next_time, event_type="my_event")
```

### 创建自定义事件处理器

继承 `EventHandler` 并实现 `process_event` 方法：

```python
from handlers import EventHandler
from events import Event

class MyCustomHandler(EventHandler):
    def process_event(self, event: Event, timeline, stats) -> List[Event]:
        # 实现事件处理逻辑
        print(f"处理事件: {event.event_type} 在时间 {event.time}")
        
        # 可以生成新事件
        new_event = Event(time=event.time + 1.0, event_type="new_event")
        return [new_event]
```

## 高级功能

### 条件事件处理

使用 `ConditionalHandler` 根据条件选择处理器：

```python
from handlers import ConditionalHandler

# 条件函数
def is_vip_customer(event):
    return event.payload.get("is_vip", False)

# 创建条件处理器
conditional_handler = ConditionalHandler(
    condition_func=is_vip_customer,
    true_handler=vip_handler,
    false_handler=regular_handler
)
```

### 统计数据观察者

使用 `StatsObserver` 实时监控统计数据：

```python
from stats import StatsObserver, ConsoleStatsObserver

# 创建观察者
observer = ConsoleStatsObserver(
    watched_keys={"wait_time", "queue_length"},
    watched_types={"value", "time_series"}
)

# 注册观察者
stats.add_observer(observer)
```

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。请遵循以下步骤：

1. Fork 仓库
2. 创建新分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

[MIT License](LICENSE) 

# 文档

## Events

标识仿真中的一次事件
- time: float
- event_type: str

## Generator

### EventGenerator(ABC)

- generate
- generate_next_time

## Handler

### EventHandler(ABC)

- can_handle
- handle (pre_handle->process_event->post_handle)->new_events
- pre_handle
- process_event @abc.abstractmethod
- post_handle

### EventDispatcher

- self.handlers: Dict[str, List[EventHandler]] = {}  # 按事件类型索引的处理器
- self.default_handlers: List[EventHandler] = []  # 处理所有事件类型的处理器
- register_handler
- dispatch

### LoggingEventHandler
### StatsCollectingHandler
### ChainHandler
### ConditionalHandler

## Parameters

### Parameter
- name:str
- value:Any
- validator:callable=None
- description:str=""
- set_value
- get_value
### ParameterSet
### ParameterBulder