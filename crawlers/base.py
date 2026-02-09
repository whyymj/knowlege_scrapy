"""
基础爬虫类
"""
import time
import random
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
from .config import CrawlerConfig
from .utils import ProxyPool, DeduplicationManager

# 导入数据处理管道
try:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from pipeline import DataProcessor
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False
    DataProcessor = None
except ImportError:
    # 处理相对导入问题
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from crawlers.config import CrawlerConfig
    from crawlers.utils import ProxyPool, DeduplicationManager


class BaseCrawler(ABC):
    """爬虫基类"""
    
    def __init__(self, name: str, config: Optional[CrawlerConfig] = None):
        """
        初始化爬虫
        
        Args:
            name: 爬虫名称
            config: 爬虫配置对象
        """
        self.name = name
        self.config = config or CrawlerConfig()
        self.crawler_config = self.config.get_crawler_config(name)
        self.anti_crawl = self.config.get_anti_crawl_strategy(name)
        
        # 初始化代理池
        proxy_list = self.config.get_proxy_pool()
        self.proxy_pool = ProxyPool(proxy_list) if proxy_list else None
        
        # 初始化去重管理器
        dedup_config = self.config.get_deduplication_config()
        self.dedup_manager = DeduplicationManager(dedup_config) if dedup_config.get('enabled') else None
        
        # 初始化数据处理管道
        if PIPELINE_AVAILABLE:
            pipeline_config = self.config._config.get('pipeline', {}).get('quality_monitor', {})
            self.data_processor = DataProcessor(pipeline_config)
        else:
            self.data_processor = None
        
        # 初始化请求会话
        self.session = self._create_session()
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'success_requests': 0,
            'failed_requests': 0,
            'duplicate_items': 0,
            'start_time': datetime.now()
        }
    
    def _create_session(self) -> requests.Session:
        """创建请求会话"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=self.anti_crawl.get('retry_times', 3),
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # User-Agent 轮换
        if self.anti_crawl.get('user_agent_rotation', True):
            user_agents = self.config.get_user_agents()
            headers['User-Agent'] = random.choice(user_agents)
        else:
            headers['User-Agent'] = self.config.get_user_agents()[0]
        
        return headers
    
    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """获取代理"""
        if not self.anti_crawl.get('use_proxy', False) or not self.proxy_pool:
            return None
        
        proxy = self.proxy_pool.get_proxy()
        if proxy:
            return {
                'http': proxy,
                'https': proxy
            }
        return None
    
    def _delay(self):
        """请求延迟"""
        delay = self.anti_crawl.get('request_delay', 1.0)
        
        if self.anti_crawl.get('random_delay', True):
            # 随机延迟：基础延迟 ± 50%
            delay = delay * (0.5 + random.random())
        
        time.sleep(delay)
    
    def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """
        发起HTTP请求
        
        Args:
            url: 请求URL
            method: 请求方法
            **kwargs: 其他请求参数
            
        Returns:
            响应对象，失败返回None
        """
        self.stats['total_requests'] += 1
        
        try:
            headers = kwargs.pop('headers', {})
            headers.update(self._get_headers())
            
            proxy = self._get_proxy()
            if proxy:
                kwargs['proxies'] = proxy
            
            timeout = kwargs.pop('timeout', self.anti_crawl.get('timeout', 30))
            
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=timeout,
                **kwargs
            )
            
            response.raise_for_status()
            self.stats['success_requests'] += 1
            
            # 延迟
            self._delay()
            
            return response
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            self.log_error(f'请求失败: {url}, 错误: {str(e)}')
            return None
    
    def _is_duplicate(self, item: Dict[str, Any]) -> bool:
        """
        检查是否重复
        
        Args:
            item: 数据项
            
        Returns:
            是否重复
        """
        if not self.dedup_manager:
            return False
        
        is_dup = self.dedup_manager.is_duplicate(item)
        if is_dup:
            self.stats['duplicate_items'] += 1
        
        return is_dup
    
    def _generate_item_id(self, item: Dict[str, Any]) -> str:
        """
        生成数据项唯一ID
        
        Args:
            item: 数据项
            
        Returns:
            唯一ID
        """
        # 优先使用URL
        if 'url' in item:
            return hashlib.md5(item['url'].encode()).hexdigest()
        
        # 使用标题
        if 'title' in item:
            return hashlib.md5(item['title'].encode()).hexdigest()
        
        # 使用内容哈希
        if 'content' in item:
            return hashlib.md5(item['content'].encode()).hexdigest()
        
        # 使用时间戳
        return hashlib.md5(str(datetime.now()).encode()).hexdigest()
    
    @abstractmethod
    def crawl(self) -> List[Dict[str, Any]]:
        """
        执行爬取
        
        Returns:
            爬取的数据列表
        """
        pass
    
    @abstractmethod
    def parse(self, response: requests.Response) -> List[Dict[str, Any]]:
        """
        解析响应数据
        
        Args:
            response: HTTP响应对象
            
        Returns:
            解析后的数据列表
        """
        pass
    
    def run(self) -> List[Dict[str, Any]]:
        """
        运行爬虫
        
        Returns:
            爬取的数据列表
        """
        self.log_info(f'开始运行爬虫: {self.name}')
        
        try:
            items = self.crawl()
            
            # 去重
            if self.dedup_manager:
                items = [item for item in items if not self._is_duplicate(item)]
            
            # 数据处理管道
            if self.data_processor:
                self.log_info('进行数据标准化和质量检查...')
                processed_items = []
                for item in items:
                    try:
                        processed_item, quality_report = self.data_processor.process(item, check_quality=True)
                        
                        # 如果质量检查未通过，记录警告
                        if not processed_item.get('quality_passed', True):
                            self.log_warning(f'数据质量未通过: {item.get("url", "unknown")}, 分数: {processed_item.get("quality_score", 0):.1f}')
                        
                        processed_items.append(processed_item)
                    except Exception as e:
                        self.log_error(f'数据处理失败: {str(e)}')
                        # 如果处理失败，使用原始数据
                        processed_items.append(item)
                
                items = processed_items
            
            # 添加爬取时间
            for item in items:
                item['crawl_time'] = datetime.now()
                item['crawler_name'] = self.name
                item['item_id'] = self._generate_item_id(item)
            
            self.log_info(f'爬取完成: {self.name}, 获取 {len(items)} 条数据')
            self._log_stats()
            
            return items
            
        except Exception as e:
            self.log_error(f'爬虫运行失败: {self.name}, 错误: {str(e)}')
            return []
    
    def log_info(self, message: str):
        """记录信息日志"""
        print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [INFO] [{self.name}] {message}')
    
    def log_error(self, message: str):
        """记录错误日志"""
        print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [ERROR] [{self.name}] {message}')
    
    def log_warning(self, message: str):
        """记录警告日志"""
        print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] [WARN] [{self.name}] {message}')
    
    def _log_stats(self):
        """记录统计信息"""
        stats = self.stats
        duration = (datetime.now() - stats['start_time']).total_seconds()
        
        self.log_info(f'统计信息: 总请求={stats["total_requests"]}, '
                      f'成功={stats["success_requests"]}, '
                      f'失败={stats["failed_requests"]}, '
                      f'重复={stats["duplicate_items"]}, '
                      f'耗时={duration:.2f}秒')
    
    def close(self):
        """关闭爬虫，释放资源"""
        if self.session:
            self.session.close()
        if self.dedup_manager:
            self.dedup_manager.close()
