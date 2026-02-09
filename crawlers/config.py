"""
爬虫配置管理类
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import timedelta


class CrawlerConfig:
    """爬虫配置管理类"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路径，默认为项目根目录的 config.json
        """
        if config_file is None:
            # 获取项目根目录
            current_dir = Path(__file__).parent
            project_root = current_dir.parent
            config_file = project_root / 'config.json'
        
        self.config_file = Path(config_file)
        self._config = self._load_config()
        self._crawler_config = self._config.get('crawlers', {})
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        if not self.config_file.exists():
            raise FileNotFoundError(f'配置文件不存在: {self.config_file}')
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_crawler_config(self, crawler_name: str) -> Dict:
        """
        获取指定爬虫的配置
        
        Args:
            crawler_name: 爬虫名称
            
        Returns:
            爬虫配置字典
        """
        return self._crawler_config.get(crawler_name, {})
    
    def get_crawl_frequency(self, crawler_name: str) -> timedelta:
        """
        获取爬取频率
        
        Args:
            crawler_name: 爬虫名称
            
        Returns:
            爬取间隔时间
        """
        config = self.get_crawler_config(crawler_name)
        frequency = config.get('frequency', '1h')  # 默认1小时
        
        # 解析时间字符串：1h, 30m, 2d 等
        if frequency.endswith('h'):
            hours = int(frequency[:-1])
            return timedelta(hours=hours)
        elif frequency.endswith('m'):
            minutes = int(frequency[:-1])
            return timedelta(minutes=minutes)
        elif frequency.endswith('d'):
            days = int(frequency[:-1])
            return timedelta(days=days)
        elif frequency.endswith('s'):
            seconds = int(frequency[:-1])
            return timedelta(seconds=seconds)
        else:
            # 默认1小时
            return timedelta(hours=1)
    
    def get_proxy_pool(self) -> List[str]:
        """
        获取代理池配置
        
        Returns:
            代理列表
        """
        proxy_config = self._crawler_config.get('proxy_pool', {})
        enabled = proxy_config.get('enabled', False)
        
        if not enabled:
            return []
        
        proxies = proxy_config.get('proxies', [])
        
        # 支持从环境变量读取代理
        env_proxy = os.getenv('PROXY_LIST')
        if env_proxy:
            proxies.extend(env_proxy.split(','))
        
        return proxies
    
    def get_anti_crawl_strategy(self, crawler_name: str) -> Dict:
        """
        获取反爬策略配置
        
        Args:
            crawler_name: 爬虫名称
            
        Returns:
            反爬策略配置
        """
        config = self.get_crawler_config(crawler_name)
        strategy = config.get('anti_crawl', {})
        
        return {
            'user_agent_rotation': strategy.get('user_agent_rotation', True),
            'request_delay': strategy.get('request_delay', 1.0),
            'random_delay': strategy.get('random_delay', True),
            'retry_times': strategy.get('retry_times', 3),
            'timeout': strategy.get('timeout', 30),
            'use_proxy': strategy.get('use_proxy', False),
            'headers_rotation': strategy.get('headers_rotation', True)
        }
    
    def get_deduplication_config(self) -> Dict:
        """
        获取去重配置
        
        Returns:
            去重配置
        """
        dedup_config = self._crawler_config.get('deduplication', {})
        
        return {
            'enabled': dedup_config.get('enabled', True),
            'method': dedup_config.get('method', 'url'),  # url, content_hash, title
            'storage': dedup_config.get('storage', 'memory'),  # memory, redis, mysql
            'redis_host': dedup_config.get('redis_host', 'localhost'),
            'redis_port': dedup_config.get('redis_port', 6379),
            'redis_db': dedup_config.get('redis_db', 0)
        }
    
    def get_user_agents(self) -> List[str]:
        """获取 User-Agent 列表"""
        return self._crawler_config.get('user_agents', [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ])
    
    def reload(self):
        """重新加载配置"""
        self._config = self._load_config()
        self._crawler_config = self._config.get('crawlers', {})
