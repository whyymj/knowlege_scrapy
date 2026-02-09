"""
爬虫工具模块
包含代理池、去重管理器等工具类
"""
import hashlib
import redis
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class ProxyPool:
    """代理池管理"""
    
    def __init__(self, proxies: List[str]):
        """
        初始化代理池
        
        Args:
            proxies: 代理列表，格式: ['http://user:pass@host:port', ...]
        """
        self.proxies = proxies
        self.current_index = 0
        self.failed_proxies = set()  # 记录失败的代理
    
    def get_proxy(self) -> Optional[str]:
        """
        获取一个代理
        
        Returns:
            代理地址，如果没有可用代理返回None
        """
        if not self.proxies:
            return None
        
        # 过滤掉失败的代理
        available_proxies = [p for p in self.proxies if p not in self.failed_proxies]
        
        if not available_proxies:
            # 如果所有代理都失败，重置失败列表
            self.failed_proxies.clear()
            available_proxies = self.proxies
        
        # 轮询获取代理
        proxy = available_proxies[self.current_index % len(available_proxies)]
        self.current_index += 1
        
        return proxy
    
    def mark_failed(self, proxy: str):
        """标记代理为失败"""
        self.failed_proxies.add(proxy)
    
    def mark_success(self, proxy: str):
        """标记代理为成功（从失败列表中移除）"""
        self.failed_proxies.discard(proxy)


class DeduplicationManager:
    """去重管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化去重管理器
        
        Args:
            config: 去重配置
        """
        self.config = config
        self.method = config.get('method', 'url')
        self.storage = config.get('storage', 'memory')
        
        if self.storage == 'redis':
            self.redis_client = redis.Redis(
                host=config.get('redis_host', 'localhost'),
                port=config.get('redis_port', 6379),
                db=config.get('redis_db', 0),
                decode_responses=True
            )
            self._memory_set = None
        else:
            self._memory_set = set()
            self.redis_client = None
    
    def _generate_key(self, item: Dict[str, Any]) -> str:
        """
        生成去重键
        
        Args:
            item: 数据项
            
        Returns:
            去重键
        """
        if self.method == 'url' and 'url' in item:
            return f"url:{item['url']}"
        elif self.method == 'title' and 'title' in item:
            return f"title:{item['title']}"
        elif self.method == 'content_hash' and 'content' in item:
            content = item.get('content', '')
            content_hash = hashlib.md5(content.encode()).hexdigest()
            return f"hash:{content_hash}"
        else:
            # 综合方式：url + title
            url = item.get('url', '')
            title = item.get('title', '')
            combined = f"{url}|{title}"
            return hashlib.md5(combined.encode()).hexdigest()
    
    def is_duplicate(self, item: Dict[str, Any]) -> bool:
        """
        检查是否重复
        
        Args:
            item: 数据项
            
        Returns:
            是否重复
        """
        key = self._generate_key(item)
        
        if self.storage == 'redis' and self.redis_client:
            exists = self.redis_client.exists(key)
            if not exists:
                # 设置过期时间（7天）
                self.redis_client.setex(key, 7 * 24 * 3600, '1')
            return bool(exists)
        else:
            # 内存存储
            if key in self._memory_set:
                return True
            self._memory_set.add(key)
            return False
    
    def add_item(self, item: Dict[str, Any]):
        """添加数据项到去重集合"""
        key = self._generate_key(item)
        
        if self.storage == 'redis' and self.redis_client:
            self.redis_client.setex(key, 7 * 24 * 3600, '1')
        else:
            self._memory_set.add(key)
    
    def clear(self):
        """清空去重集合"""
        if self.storage == 'redis' and self.redis_client:
            # Redis 清空需要指定模式，这里只清空当前数据库
            self.redis_client.flushdb()
        else:
            self._memory_set.clear()
    
    def close(self):
        """关闭连接"""
        if self.redis_client:
            self.redis_client.close()
