from typing import Dict, List, Any, Optional, Callable, Set
import json
import csv
import abc
import statistics
import matplotlib.pyplot as plt
from collections import defaultdict
from dataclasses import dataclass, field


class Stats:
    """
    收集、汇总、输出仿真过程中的各类统计数据（观察者模式）
    """
    
    def __init__(self):
        # 计数器，记录各类事件发生次数
        self._counters: Dict[str, int] = defaultdict(int)
        
        # 累加器，记录各类数值的累加结果
        self._accumulators: Dict[str, float] = defaultdict(float)
        
        # 值列表，记录各类数值序列
        self._value_lists: Dict[str, List[float]] = defaultdict(list)
        
        # 时间序列，记录各类指标随时间的变化
        self._time_series: Dict[str, List[tuple]] = defaultdict(list)
        
        # 自定义统计指标
        self._custom_stats: Dict[str, Any] = {}
        
        # 观察者列表
        self._observers: List['StatsObserver'] = []
    
    def increment_count(self, key: str, increment: int = 1) -> None:
        """增加计数器值"""
        self._counters[key] += increment
        self._notify_observers(key, 'counter', self._counters[key])
    
    def get_count(self, key: str) -> int:
        """获取计数器值"""
        return self._counters.get(key, 0)
    
    def add_value(self, key: str, value: float) -> None:
        """添加一个值到值列表，并更新累加器"""
        self._value_lists[key].append(value)
        self._accumulators[key] += value
        self._notify_observers(key, 'value', value)
    
    def get_values(self, key: str) -> List[float]:
        """获取值列表"""
        return self._value_lists.get(key, [])
    
    def get_sum(self, key: str) -> float:
        """获取累加器值"""
        return self._accumulators.get(key, 0.0)
    
    def get_average(self, key: str) -> Optional[float]:
        """获取平均值"""
        values = self.get_values(key)
        if not values:
            return None
        return self.get_sum(key) / len(values)
    
    def get_median(self, key: str) -> Optional[float]:
        """获取中位数"""
        values = self.get_values(key)
        if not values:
            return None
        return statistics.median(values)
    
    def get_std_dev(self, key: str) -> Optional[float]:
        """获取标准差"""
        values = self.get_values(key)
        if len(values) < 2:
            return None
        return statistics.stdev(values)
    
    def add_time_point(self, key: str, time: float, value: float) -> None:
        """添加一个时间点的数据"""
        self._time_series[key].append((time, value))
        self._notify_observers(key, 'time_series', (time, value))
    
    def get_time_series(self, key: str) -> List[tuple]:
        """获取时间序列数据"""
        return self._time_series.get(key, [])
    
    def set_custom_stat(self, key: str, value: Any) -> None:
        """设置自定义统计指标"""
        self._custom_stats[key] = value
        self._notify_observers(key, 'custom', value)
    
    def get_custom_stat(self, key: str) -> Any:
        """获取自定义统计指标"""
        return self._custom_stats.get(key)
    
    def reset(self) -> None:
        """重置所有统计数据"""
        self._counters.clear()
        self._accumulators.clear()
        self._value_lists.clear()
        self._time_series.clear()
        self._custom_stats.clear()
        self._notify_observers('all', 'reset', None)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取统计数据摘要"""
        summary = {
            'counters': dict(self._counters),
            'sums': dict(self._accumulators),
            'averages': {k: self.get_average(k) for k in self._value_lists},
            'medians': {k: self.get_median(k) for k in self._value_lists},
            'std_devs': {k: self.get_std_dev(k) for k in self._value_lists},
            'custom': dict(self._custom_stats)
        }
        return summary
    
    def export_to_json(self, file_path: str) -> None:
        """导出统计数据到JSON文件"""
        summary = self.get_summary()
        
        # 将时间序列数据添加到摘要中
        summary['time_series'] = {k: v for k, v in self._time_series.items()}
        
        with open(file_path, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def export_to_csv(self, file_path: str, include_time_series: bool = False) -> None:
        """导出统计数据到CSV文件"""
        summary = self.get_summary()
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # 写入计数器数据
            writer.writerow(['Type', 'Key', 'Value'])
            for key, value in summary['counters'].items():
                writer.writerow(['Counter', key, value])
            
            # 写入累加器数据
            for key, value in summary['sums'].items():
                writer.writerow(['Sum', key, value])
            
            # 写入平均值数据
            for key, value in summary['averages'].items():
                if value is not None:
                    writer.writerow(['Average', key, value])
            
            # 写入中位数数据
            for key, value in summary['medians'].items():
                if value is not None:
                    writer.writerow(['Median', key, value])
            
            # 写入标准差数据
            for key, value in summary['std_devs'].items():
                if value is not None:
                    writer.writerow(['StdDev', key, value])
            
            # 写入自定义数据
            for key, value in summary['custom'].items():
                if isinstance(value, (int, float, str, bool)):
                    writer.writerow(['Custom', key, value])
            
            # 写入时间序列数据
            if include_time_series:
                writer.writerow([])
                writer.writerow(['Time Series Data'])
                for key, series in self._time_series.items():
                    writer.writerow([key])
                    writer.writerow(['Time', 'Value'])
                    for time, value in series:
                        writer.writerow([time, value])
                    writer.writerow([])
    
    def plot_time_series(self, key: str, title: Optional[str] = None, 
                        xlabel: str = 'Time', ylabel: Optional[str] = None,
                        show: bool = True, save_path: Optional[str] = None) -> None:
        """绘制时间序列图表"""
        series = self.get_time_series(key)
        if not series:
            print(f"No time series data for key: {key}")
            return
            
        times, values = zip(*series)
        
        plt.figure(figsize=(10, 6))
        plt.plot(times, values, marker='o', linestyle='-', markersize=3)
        
        if title:
            plt.title(title)
        else:
            plt.title(f'Time Series for {key}')
            
        plt.xlabel(xlabel)
        plt.ylabel(ylabel or key)
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path)
            
        if show:
            plt.show()
        else:
            plt.close()
    
    def add_observer(self, observer: 'StatsObserver') -> None:
        """添加观察者"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: 'StatsObserver') -> None:
        """移除观察者"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, key: str, stat_type: str, value: Any) -> None:
        """通知所有观察者"""
        for observer in self._observers:
            observer.update(self, key, stat_type, value)


class StatsObserver(abc.ABC):
    """统计数据观察者基类"""
    
    @abc.abstractmethod
    def update(self, stats: Stats, key: str, stat_type: str, value: Any) -> None:
        """
        接收统计数据更新通知
        
        Args:
            stats: 统计对象
            key: 统计项键名
            stat_type: 统计类型（counter, value, time_series, custom, reset等）
            value: 新值
        """
        pass


class ConsoleStatsObserver(StatsObserver):
    """将统计数据更新打印到控制台的观察者"""
    
    def __init__(self, watched_keys: Optional[Set[str]] = None, 
                watched_types: Optional[Set[str]] = None):
        self.watched_keys = watched_keys
        self.watched_types = watched_types
    
    def update(self, stats: Stats, key: str, stat_type: str, value: Any) -> None:
        """打印统计数据更新"""
        if (self.watched_keys is not None and key not in self.watched_keys and key != 'all'):
            return
            
        if (self.watched_types is not None and stat_type not in self.watched_types and stat_type != 'reset'):
            return
            
        if stat_type == 'reset':
            print("[Stats] Reset all statistics")
        elif stat_type == 'counter':
            print(f"[Stats] Counter '{key}' = {value}")
        elif stat_type == 'value':
            print(f"[Stats] Added value to '{key}': {value}")
        elif stat_type == 'time_series':
            time, val = value
            print(f"[Stats] Time series '{key}' at {time}: {val}")
        elif stat_type == 'custom':
            print(f"[Stats] Custom stat '{key}' = {value}")


class FileStatsObserver(StatsObserver):
    """将统计数据更新写入文件的观察者"""
    
    def __init__(self, file_path: str, watched_keys: Optional[Set[str]] = None, 
                watched_types: Optional[Set[str]] = None):
        self.file_path = file_path
        self.watched_keys = watched_keys
        self.watched_types = watched_types
        
        # 创建或清空文件
        with open(self.file_path, 'w') as f:
            f.write(f"Time,Key,Type,Value\n")
    
    def update(self, stats: Stats, key: str, stat_type: str, value: Any) -> None:
        """将统计数据更新写入文件"""
        if (self.watched_keys is not None and key not in self.watched_keys and key != 'all'):
            return
            
        if (self.watched_types is not None and stat_type not in self.watched_types and stat_type != 'reset'):
            return
            
        with open(self.file_path, 'a') as f:
            current_time = stats.current_time if hasattr(stats, 'current_time') else 0
            
            if stat_type == 'reset':
                f.write(f"{current_time},all,reset,\n")
            elif stat_type == 'time_series':
                time, val = value
                f.write(f"{current_time},{key},time_series,{time},{val}\n")
            else:
                f.write(f"{current_time},{key},{stat_type},{value}\n") 