from typing import Any, Dict, Optional
from copy import deepcopy


class Parameter:
    """封装仿真所需的全部参数，可统一管理和校验"""
    
    def __init__(self, name: str, default_value: Any = None, 
                 validator: callable = None, description: str = ""):
        self.name = name
        self.value = default_value
        self.validator = validator
        self.description = description
        
    def set_value(self, value: Any) -> None:
        """设置参数值，如果有验证器会进行验证"""
        if self.validator and not self.validator(value):
            raise ValueError(f"Parameter '{self.name}' validation failed for value: {value}")
        self.value = value
        
    def get_value(self) -> Any:
        """获取参数值"""
        return self.value


class ParameterSet:
    """参数集合，管理多个相关参数"""
    
    def __init__(self):
        self._parameters: Dict[str, Parameter] = {}
        
    def add(self, parameter: Parameter) -> 'ParameterSet':
        """添加参数到集合"""
        self._parameters[parameter.name] = parameter
        return self
        
    def get(self, name: str) -> Parameter:
        """获取参数对象"""
        if name not in self._parameters:
            raise KeyError(f"Parameter '{name}' not found")
        return self._parameters[name]
    
    def get_value(self, name: str) -> Any:
        """获取参数值"""
        return self.get(name).get_value()
    
    def set_value(self, name: str, value: Any) -> 'ParameterSet':
        """设置参数值"""
        self.get(name).set_value(value)
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """将参数集合转换为字典"""
        return {name: param.get_value() for name, param in self._parameters.items()}
    
    def copy(self) -> 'ParameterSet':
        """创建参数集合的副本"""
        new_set = ParameterSet()
        for name, param in self._parameters.items():
            new_param = Parameter(
                name=param.name,
                default_value=deepcopy(param.get_value()),
                validator=param.validator,
                description=param.description
            )
            new_set.add(new_param)
        return new_set


class ParameterBuilder:
    """使用构建者模式创建复杂参数集合"""
    
    def __init__(self):
        self.parameter_set = ParameterSet()
    
    def add_integer(self, name: str, default_value: int = 0, 
                   min_value: Optional[int] = None, max_value: Optional[int] = None,
                   description: str = "") -> 'ParameterBuilder':
        """添加整数参数"""
        def validator(value):
            if not isinstance(value, int):
                return False
            if min_value is not None and value < min_value:
                return False
            if max_value is not None and value > max_value:
                return False
            return True
            
        param = Parameter(name, default_value, validator, description)
        self.parameter_set.add(param)
        return self
    
    def add_float(self, name: str, default_value: float = 0.0,
                 min_value: Optional[float] = None, max_value: Optional[float] = None,
                 description: str = "") -> 'ParameterBuilder':
        """添加浮点数参数"""
        def validator(value):
            if not isinstance(value, (int, float)):
                return False
            if min_value is not None and value < min_value:
                return False
            if max_value is not None and value > max_value:
                return False
            return True
            
        param = Parameter(name, default_value, validator, description)
        self.parameter_set.add(param)
        return self
    
    def add_string(self, name: str, default_value: str = "",
                  allowed_values: Optional[list] = None,
                  description: str = "") -> 'ParameterBuilder':
        """添加字符串参数"""
        def validator(value):
            if not isinstance(value, str):
                return False
            if allowed_values is not None and value not in allowed_values:
                return False
            return True
            
        param = Parameter(name, default_value, validator, description)
        self.parameter_set.add(param)
        return self
    
    def add_boolean(self, name: str, default_value: bool = False,
                   description: str = "") -> 'ParameterBuilder':
        """添加布尔参数"""
        def validator(value):
            return isinstance(value, bool)
            
        param = Parameter(name, default_value, validator, description)
        self.parameter_set.add(param)
        return self
    
    def add_custom(self, parameter: Parameter) -> 'ParameterBuilder':
        """添加自定义参数"""
        self.parameter_set.add(parameter)
        return self
    
    def build(self) -> ParameterSet:
        """构建并返回参数集合"""
        return self.parameter_set.copy() 