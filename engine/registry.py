"""
组件注册表
"""
from typing import Dict, Type, Optional, Any
import logging


class ComponentRegistry:
    """组件注册表"""
    
    def __init__(self):
        """初始化注册表"""
        self.adapters: Dict[str, Type] = {}
        self.parsers: Dict[str, Type] = {}
        self.extractors: Dict[str, Type] = {}
        self.transformers: Dict[str, Type] = {}
        self.outputs: Dict[str, Type] = {}
        self.validators: Dict[str, Type] = {}
        self.filters: Dict[str, Type] = {}
        
        self.logger = logging.getLogger(__name__)
    
    def register_adapter(self, name: str, adapter_class: Type):
        """注册源适配器"""
        self.adapters[name] = adapter_class
        self.logger.debug(f"注册适配器: {name}")
    
    def register_parser(self, name: str, parser_class: Type):
        """注册解析器"""
        self.parsers[name] = parser_class
        self.logger.debug(f"注册解析器: {name}")
    
    def register_extractor(self, name: str, extractor_class: Type):
        """注册提取器"""
        self.extractors[name] = extractor_class
        self.logger.debug(f"注册提取器: {name}")
    
    def register_transformer(self, name: str, transformer_class: Type):
        """注册转换器"""
        self.transformers[name] = transformer_class
        self.logger.debug(f"注册转换器: {name}")
    
    def register_output(self, name: str, output_class: Type):
        """注册输出器"""
        self.outputs[name] = output_class
        self.logger.debug(f"注册输出器: {name}")
    
    def register_validator(self, name: str, validator_class: Type):
        """注册验证器"""
        self.validators[name] = validator_class
        self.logger.debug(f"注册验证器: {name}")
    
    def register_filter(self, name: str, filter_class: Type):
        """注册筛选器"""
        self.filters[name] = filter_class
        self.logger.debug(f"注册筛选器: {name}")
    
    def get_adapter(self, name: str) -> Optional[Type]:
        """获取适配器类"""
        return self.adapters.get(name)
    
    def get_parser(self, name: str) -> Optional[Type]:
        """获取解析器类"""
        return self.parsers.get(name)
    
    def get_extractor(self, name: str) -> Optional[Type]:
        """获取提取器类"""
        return self.extractors.get(name)
    
    def get_transformer(self, name: str) -> Optional[Type]:
        """获取转换器类"""
        return self.transformers.get(name)
    
    def get_output(self, name: str) -> Optional[Type]:
        """获取输出器类"""
        return self.outputs.get(name)
    
    def get_validator(self, name: str) -> Optional[Type]:
        """获取验证器类"""
        return self.validators.get(name)
    
    def get_filter(self, name: str) -> Optional[Type]:
        """获取筛选器类"""
        return self.filters.get(name)
    
    def get_all_components(self) -> Dict[str, Dict[str, Type]]:
        """获取所有组件"""
        return {
            'adapters': self.adapters,
            'parsers': self.parsers,
            'extractors': self.extractors,
            'transformers': self.transformers,
            'outputs': self.outputs,
            'validators': self.validators,
            'filters': self.filters
        }
