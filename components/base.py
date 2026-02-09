"""
组件基类
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseAdapter(ABC):
    """源适配器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化适配器
        
        Args:
            config: 配置
        """
        self.config = config
    
    @abstractmethod
    async def generate_requests(self, task_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成请求
        
        Args:
            task_config: 任务配置
            
        Returns:
            请求列表
        """
        pass
    
    @abstractmethod
    async def fetch(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取页面
        
        Args:
            request: 请求
            
        Returns:
            页面数据
        """
        pass


class BaseParser(ABC):
    """解析器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化解析器
        
        Args:
            config: 配置
        """
        self.config = config
    
    @abstractmethod
    async def parse(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析页面
        
        Args:
            page: 页面数据
            
        Returns:
            解析后的内容
        """
        pass


class BaseExtractor(ABC):
    """提取器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化提取器
        
        Args:
            config: 配置
        """
        self.config = config
    
    @abstractmethod
    async def extract(self, content: Dict[str, Any], fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        提取数据
        
        Args:
            content: 解析后的内容
            fields: 字段定义
            
        Returns:
            提取的数据列表
        """
        pass


class BaseTransformer(ABC):
    """转换器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化转换器
        
        Args:
            config: 配置
        """
        self.config = config
    
    @abstractmethod
    def transform(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换数据
        
        Args:
            item: 数据项
            
        Returns:
            转换后的数据
        """
        pass


class BaseOutput(ABC):
    """输出器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化输出器
        
        Args:
            config: 配置
        """
        self.config = config
    
    @abstractmethod
    async def output(self, items: List[Dict[str, Any]]):
        """
        输出数据
        
        Args:
            items: 数据列表
        """
        pass


class BaseValidator(ABC):
    """验证器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化验证器
        
        Args:
            config: 配置
        """
        self.config = config
    
    @abstractmethod
    def validate(self, item: Dict[str, Any]) -> bool:
        """
        验证数据
        
        Args:
            item: 数据项
            
        Returns:
            是否有效
        """
        pass


class BaseFilter(ABC):
    """筛选器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化筛选器
        
        Args:
            config: 配置
        """
        self.config = config
    
    @abstractmethod
    async def filter(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        筛选数据
        
        Args:
            items: 数据项列表
            
        Returns:
            筛选后的数据项列表
        """
        pass
