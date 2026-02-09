"""
缓存层（Redis）
用于热点数据、会话状态
"""
from typing import Dict, List, Optional, Any
import json
import pickle
from datetime import datetime, timedelta
from .base import BaseStorage, StorageType

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisStorage(BaseStorage):
    """Redis 缓存存储"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.storage_type = StorageType.REDIS
        self.client = None
        self.default_ttl = config.get('default_ttl', 3600)  # 默认1小时过期
    
    def connect(self) -> bool:
        """连接 Redis"""
        if not REDIS_AVAILABLE:
            raise ImportError('redis 未安装，请运行: pip install redis')
        
        try:
            self.client = redis.Redis(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 6379),
                db=self.config.get('db', 0),
                password=self.config.get('password'),
                decode_responses=False,  # 保持二进制，支持pickle
                socket_timeout=self.config.get('timeout', 5),
                socket_connect_timeout=self.config.get('timeout', 5)
            )
            
            # 测试连接
            self.client.ping()
            
            self.connected = True
            return True
        except Exception as e:
            print(f'Redis 连接失败: {e}')
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.client:
            self.client.close()
            self.connected = False
    
    def _make_key(self, collection: str, key: str) -> str:
        """生成完整键名"""
        return f"{collection}:{key}"
    
    def insert(self, collection: str, data: Dict[str, Any]) -> bool:
        """插入缓存数据"""
        if not self.connected:
            return False
        
        try:
            key = data.get('key') or data.get('id') or str(hash(str(data)))
            full_key = self._make_key(collection, key)
            
            # 序列化数据
            value = pickle.dumps(data)
            
            # 设置过期时间
            ttl = data.get('ttl', self.default_ttl)
            self.client.setex(full_key, ttl, value)
            
            return True
        except Exception as e:
            print(f'Redis 插入失败: {e}')
            return False
    
    def query(self, collection: str, filters: Optional[Dict] = None, limit: Optional[int] = None) -> List[Dict]:
        """查询缓存数据"""
        if not self.connected:
            return []
        
        try:
            results = []
            
            if filters and 'key' in filters:
                # 精确查询
                full_key = self._make_key(collection, filters['key'])
                value = self.client.get(full_key)
                if value:
                    data = pickle.loads(value)
                    results.append(data)
            else:
                # 模式匹配查询
                pattern = f"{collection}:*"
                keys = self.client.keys(pattern)
                
                if limit:
                    keys = keys[:limit]
                
                for key in keys:
                    value = self.client.get(key)
                    if value:
                        data = pickle.loads(value)
                        # 应用过滤条件
                        if filters:
                            match = True
                            for k, v in filters.items():
                                if k != 'key' and data.get(k) != v:
                                    match = False
                                    break
                            if not match:
                                continue
                        results.append(data)
            
            return results
        except Exception as e:
            print(f'Redis 查询失败: {e}')
            return []
    
    def update(self, collection: str, filters: Dict, data: Dict[str, Any]) -> bool:
        """更新缓存数据"""
        if not self.connected:
            return False
        
        try:
            key = filters.get('key') or filters.get('id')
            if not key:
                return False
            
            full_key = self._make_key(collection, key)
            
            # 获取现有数据
            existing_value = self.client.get(full_key)
            if existing_value:
                existing_data = pickle.loads(existing_value)
                existing_data.update(data)
                
                # 更新数据
                value = pickle.dumps(existing_data)
                ttl = self.client.ttl(full_key)
                if ttl > 0:
                    self.client.setex(full_key, ttl, value)
                else:
                    self.client.setex(full_key, self.default_ttl, value)
                return True
            
            return False
        except Exception as e:
            print(f'Redis 更新失败: {e}')
            return False
    
    def delete(self, collection: str, filters: Dict) -> bool:
        """删除缓存数据"""
        if not self.connected:
            return False
        
        try:
            key = filters.get('key') or filters.get('id')
            if key:
                full_key = self._make_key(collection, key)
                return bool(self.client.delete(full_key))
            return False
        except Exception as e:
            print(f'Redis 删除失败: {e}')
            return False
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置键值对
        
        Args:
            key: 键名
            value: 值
            ttl: 过期时间（秒）
            
        Returns:
            是否成功
        """
        if not self.connected:
            return False
        
        try:
            serialized = pickle.dumps(value)
            if ttl:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)
            return True
        except Exception as e:
            print(f'Redis 设置失败: {e}')
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取键值
        
        Args:
            key: 键名
            
        Returns:
            值
        """
        if not self.connected:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            print(f'Redis 获取失败: {e}')
            return None
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.connected:
            return False
        return bool(self.client.exists(key))
    
    def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        if not self.connected:
            return False
        return bool(self.client.expire(key, ttl))
    
    def clear_collection(self, collection: str) -> int:
        """
        清空集合的所有数据
        
        Args:
            collection: 集合名
            
        Returns:
            删除的数量
        """
        if not self.connected:
            return 0
        
        try:
            pattern = f"{collection}:*"
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f'Redis 清空集合失败: {e}')
            return 0
