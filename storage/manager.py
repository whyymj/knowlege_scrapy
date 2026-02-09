"""
统一存储管理器
管理多种数据库连接
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from .base import BaseStorage, StorageType
from .timeseries import InfluxDBStorage, TimescaleDBStorage
from .vector import QdrantStorage, PineconeStorage
from .document import MongoDBStorage, ElasticsearchStorage
from .cache import RedisStorage


class StorageManager:
    """统一存储管理器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化存储管理器
        
        Args:
            config: 配置对象或字典
        """
        if config is None:
            # 从全局配置读取
            try:
                from utils.config_loader import config as global_config
                storage_config = global_config._config.get('storage', {})
            except:
                storage_config = {}
        else:
            storage_config = config
        
        self.storages: Dict[StorageType, BaseStorage] = {}
        self.config = storage_config
    
    def get_storage(self, storage_type: StorageType) -> Optional[BaseStorage]:
        """
        获取存储实例
        
        Args:
            storage_type: 存储类型
            
        Returns:
            存储实例
        """
        if storage_type in self.storages:
            return self.storages[storage_type]
        
        # 创建存储实例
        storage = self._create_storage(storage_type)
        if storage:
            self.storages[storage_type] = storage
            if not storage.connected:
                storage.connect()
        
        return storage
    
    def _create_storage(self, storage_type: StorageType) -> Optional[BaseStorage]:
        """
        创建存储实例
        
        Args:
            storage_type: 存储类型
            
        Returns:
            存储实例
        """
        config_key = storage_type.value
        config = self.config.get(config_key, {})
        
        if not config.get('enabled', False):
            return None
        
        try:
            if storage_type == StorageType.INFLUXDB:
                return InfluxDBStorage(config)
            elif storage_type == StorageType.TIMESCALEDB:
                return TimescaleDBStorage(config)
            elif storage_type == StorageType.QDRANT:
                return QdrantStorage(config)
            elif storage_type == StorageType.PINECONE:
                return PineconeStorage(config)
            elif storage_type == StorageType.MONGODB:
                return MongoDBStorage(config)
            elif storage_type == StorageType.ELASTICSEARCH:
                return ElasticsearchStorage(config)
            elif storage_type == StorageType.REDIS:
                return RedisStorage(config)
            else:
                print(f'不支持的存储类型: {storage_type}')
                return None
        except Exception as e:
            print(f'创建存储实例失败 ({storage_type}): {e}')
            return None
    
    def store_timeseries(self, collection: str, data: Dict[str, Any], 
                        use_timescaledb: bool = False) -> bool:
        """
        存储时序数据
        
        Args:
            collection: 集合名
            data: 数据
            use_timescaledb: 是否使用TimescaleDB（否则使用InfluxDB）
            
        Returns:
            是否成功
        """
        storage_type = StorageType.TIMESCALEDB if use_timescaledb else StorageType.INFLUXDB
        storage = self.get_storage(storage_type)
        
        if storage:
            return storage.insert(collection, data)
        return False
    
    def store_vector(self, collection: str, data: Dict[str, Any], 
                    use_pinecone: bool = False) -> bool:
        """
        存储向量数据
        
        Args:
            collection: 集合名
            data: 数据（必须包含vector字段）
            use_pinecone: 是否使用Pinecone（否则使用Qdrant）
            
        Returns:
            是否成功
        """
        storage_type = StorageType.PINECONE if use_pinecone else StorageType.QDRANT
        storage = self.get_storage(storage_type)
        
        if storage:
            return storage.insert(collection, data)
        return False
    
    def store_document(self, collection: str, data: Dict[str, Any],
                      use_elasticsearch: bool = False) -> bool:
        """
        存储文档数据
        
        Args:
            collection: 集合名
            data: 数据
            use_elasticsearch: 是否使用Elasticsearch（否则使用MongoDB）
            
        Returns:
            是否成功
        """
        storage_type = StorageType.ELASTICSEARCH if use_elasticsearch else StorageType.MONGODB
        storage = self.get_storage(storage_type)
        
        if storage:
            return storage.insert(collection, data)
        return False
    
    def store_cache(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        存储缓存数据
        
        Args:
            key: 键名
            value: 值
            ttl: 过期时间（秒）
            
        Returns:
            是否成功
        """
        storage = self.get_storage(StorageType.REDIS)
        
        if storage and isinstance(storage, RedisStorage):
            return storage.set(key, value, ttl)
        return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            key: 键名
            
        Returns:
            值
        """
        storage = self.get_storage(StorageType.REDIS)
        
        if storage and isinstance(storage, RedisStorage):
            return storage.get(key)
        return None
    
    def search_similar(self, collection: str, query_vector: List[float], 
                      limit: int = 10, use_pinecone: bool = False) -> List[Dict]:
        """
        向量相似度搜索
        
        Args:
            collection: 集合名
            query_vector: 查询向量
            limit: 返回数量
            use_pinecone: 是否使用Pinecone
            
        Returns:
            相似结果列表
        """
        storage_type = StorageType.PINECONE if use_pinecone else StorageType.QDRANT
        storage = self.get_storage(storage_type)
        
        if storage:
            if isinstance(storage, QdrantStorage):
                return storage.search_similar(collection, query_vector, limit)
            else:
                return storage.query(collection, {'vector': query_vector}, limit)
        return []
    
    def search_text(self, collection: str, query_text: str, 
                   limit: int = 10, use_elasticsearch: bool = True) -> List[Dict]:
        """
        全文搜索
        
        Args:
            collection: 集合名
            query_text: 搜索文本
            limit: 返回数量
            use_elasticsearch: 是否使用Elasticsearch
            
        Returns:
            搜索结果列表
        """
        if use_elasticsearch:
            storage = self.get_storage(StorageType.ELASTICSEARCH)
            if storage and isinstance(storage, ElasticsearchStorage):
                return storage.search_text(collection, query_text, limit=limit)
        else:
            # MongoDB 文本搜索
            storage = self.get_storage(StorageType.MONGODB)
            if storage:
                return storage.query(collection, {'$text': {'$search': query_text}}, limit)
        
        return []
    
    def query_timeseries(self, collection: str, start_time: datetime, end_time: datetime,
                        tags: Optional[Dict] = None, use_timescaledb: bool = False) -> List[Dict]:
        """
        查询时间序列数据
        
        Args:
            collection: 集合名
            start_time: 开始时间
            end_time: 结束时间
            tags: 标签过滤
            use_timescaledb: 是否使用TimescaleDB
            
        Returns:
            数据列表
        """
        storage_type = StorageType.TIMESCALEDB if use_timescaledb else StorageType.INFLUXDB
        storage = self.get_storage(storage_type)
        
        if storage:
            if isinstance(storage, InfluxDBStorage):
                return storage.query_time_range(collection, start_time, end_time, tags)
            else:
                # TimescaleDB 时间范围查询
                filters = {
                    'time': {'$gte': start_time, '$lte': end_time}
                }
                if tags:
                    filters.update(tags)
                return storage.query(collection, filters)
        return []
    
    def close_all(self):
        """关闭所有存储连接"""
        for storage in self.storages.values():
            if storage and storage.connected:
                storage.disconnect()
        self.storages.clear()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close_all()
