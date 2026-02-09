"""
存储层基类和接口定义
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


class StorageType(Enum):
    """存储类型枚举"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    ELASTICSEARCH = "elasticsearch"
    INFLUXDB = "influxdb"
    TIMESCALEDB = "timescaledb"
    QDRANT = "qdrant"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    REDIS = "redis"


class BaseStorage(ABC):
    """存储基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化存储
        
        Args:
            config: 存储配置
        """
        self.config = config
        self.storage_type = None
        self.connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """
        连接数据库
        
        Returns:
            是否连接成功
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    def insert(self, collection: str, data: Dict[str, Any]) -> bool:
        """
        插入数据
        
        Args:
            collection: 集合/表名
            data: 数据字典
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def query(self, collection: str, filters: Optional[Dict] = None, limit: Optional[int] = None) -> List[Dict]:
        """
        查询数据
        
        Args:
            collection: 集合/表名
            filters: 过滤条件
            limit: 限制数量
            
        Returns:
            数据列表
        """
        pass
    
    @abstractmethod
    def update(self, collection: str, filters: Dict, data: Dict[str, Any]) -> bool:
        """
        更新数据
        
        Args:
            collection: 集合/表名
            filters: 过滤条件
            data: 更新数据
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def delete(self, collection: str, filters: Dict) -> bool:
        """
        删除数据
        
        Args:
            collection: 集合/表名
            filters: 过滤条件
            
        Returns:
            是否成功
        """
        pass
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
