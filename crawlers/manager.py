"""
爬虫管理器
统一管理和调度所有爬虫
"""
import time
import threading
from typing import Dict, List
from datetime import datetime, timedelta
from .config import CrawlerConfig
from .ai import (
    ArxivCrawler,
    PapersWithCodeCrawler,
    GitHubTrendingCrawler,
    OpenAIBlogCrawler,
    JQZhixinCrawler
)
from .stock import (
    YahooFinanceCrawler,
    TushareCrawler,
    SinaFinanceCrawler,
    XueqiuCrawler
)


class CrawlerManager:
    """爬虫管理器"""
    
    def __init__(self, config: CrawlerConfig = None):
        """
        初始化爬虫管理器
        
        Args:
            config: 爬虫配置对象
        """
        self.config = config or CrawlerConfig()
        self.crawlers = {}
        self.last_run_time = {}
        self.running = False
        self.threads = []
        
        # 注册所有爬虫
        self._register_crawlers()
    
    def _register_crawlers(self):
        """注册所有爬虫"""
        # AI技术信息爬虫
        self.crawlers['ai_arxiv'] = ArxivCrawler(self.config)
        self.crawlers['ai_paperswithcode'] = PapersWithCodeCrawler(self.config)
        self.crawlers['ai_github_trending'] = GitHubTrendingCrawler(self.config)
        self.crawlers['ai_openai_blog'] = OpenAIBlogCrawler(self.config)
        self.crawlers['ai_jqzhixin'] = JQZhixinCrawler(self.config)
        
        # 股市信息爬虫
        self.crawlers['stock_yahoo_finance'] = YahooFinanceCrawler(self.config)
        self.crawlers['stock_tushare'] = TushareCrawler(self.config)
        self.crawlers['stock_sina_finance'] = SinaFinanceCrawler(self.config)
        self.crawlers['stock_xueqiu'] = XueqiuCrawler(self.config)
    
    def run_crawler(self, crawler_name: str) -> List[Dict]:
        """
        运行指定爬虫
        
        Args:
            crawler_name: 爬虫名称
            
        Returns:
            爬取的数据列表
        """
        if crawler_name not in self.crawlers:
            print(f'爬虫不存在: {crawler_name}')
            return []
        
        crawler = self.crawlers[crawler_name]
        
        # 检查是否启用
        crawler_config = self.config.get_crawler_config(crawler_name)
        if not crawler_config.get('enabled', True):
            print(f'爬虫未启用: {crawler_name}')
            return []
        
        # 检查爬取频率
        if crawler_name in self.last_run_time:
            frequency = self.config.get_crawl_frequency(crawler_name)
            time_since_last = datetime.now() - self.last_run_time[crawler_name]
            if time_since_last < frequency:
                print(f'爬虫 {crawler_name} 距离上次运行时间过短，跳过')
                return []
        
        # 运行爬虫
        print(f'开始运行爬虫: {crawler_name}')
        items = crawler.run()
        self.last_run_time[crawler_name] = datetime.now()
        
        return items
    
    def run_all(self) -> Dict[str, List[Dict]]:
        """
        运行所有启用的爬虫
        
        Returns:
            各爬虫的数据字典
        """
        results = {}
        
        for crawler_name, crawler in self.crawlers.items():
            crawler_config = self.config.get_crawler_config(crawler_name)
            if crawler_config.get('enabled', True):
                items = self.run_crawler(crawler_name)
                results[crawler_name] = items
        
        return results
    
    def run_ai_crawlers(self) -> Dict[str, List[Dict]]:
        """运行所有AI技术信息爬虫"""
        results = {}
        ai_crawlers = [name for name in self.crawlers.keys() if name.startswith('ai_')]
        
        for crawler_name in ai_crawlers:
            items = self.run_crawler(crawler_name)
            results[crawler_name] = items
        
        return results
    
    def run_stock_crawlers(self) -> Dict[str, List[Dict]]:
        """运行所有股市信息爬虫"""
        results = {}
        stock_crawlers = [name for name in self.crawlers.keys() if name.startswith('stock_')]
        
        for crawler_name in stock_crawlers:
            items = self.run_crawler(crawler_name)
            results[crawler_name] = items
        
        return results
    
    def start_scheduler(self, interval: int = 3600):
        """
        启动定时调度器
        
        Args:
            interval: 调度间隔（秒）
        """
        self.running = True
        
        def scheduler_loop():
            while self.running:
                try:
                    # 检查每个爬虫是否需要运行
                    for crawler_name, crawler in self.crawlers.items():
                        crawler_config = self.config.get_crawler_config(crawler_name)
                        if not crawler_config.get('enabled', True):
                            continue
                        
                        # 检查是否到了运行时间
                        if crawler_name not in self.last_run_time:
                            # 首次运行
                            thread = threading.Thread(
                                target=self._run_crawler_thread,
                                args=(crawler_name,)
                            )
                            thread.start()
                            self.threads.append(thread)
                        else:
                            frequency = self.config.get_crawl_frequency(crawler_name)
                            time_since_last = datetime.now() - self.last_run_time[crawler_name]
                            
                            if time_since_last >= frequency:
                                thread = threading.Thread(
                                    target=self._run_crawler_thread,
                                    args=(crawler_name,)
                                )
                                thread.start()
                                self.threads.append(thread)
                    
                    # 等待一段时间后再次检查
                    time.sleep(interval)
                    
                except Exception as e:
                    print(f'调度器错误: {str(e)}')
                    time.sleep(60)
        
        scheduler_thread = threading.Thread(target=scheduler_loop)
        scheduler_thread.daemon = True
        scheduler_thread.start()
    
    def _run_crawler_thread(self, crawler_name: str):
        """在单独线程中运行爬虫"""
        try:
            self.run_crawler(crawler_name)
        except Exception as e:
            print(f'爬虫运行失败: {crawler_name}, 错误: {str(e)}')
    
    def stop(self):
        """停止调度器"""
        self.running = False
        
        # 等待所有线程完成
        for thread in self.threads:
            thread.join(timeout=10)
        
        # 关闭所有爬虫
        for crawler in self.crawlers.values():
            crawler.close()
    
    def get_status(self) -> Dict:
        """获取爬虫状态"""
        status = {}
        
        for crawler_name, crawler in self.crawlers.items():
            crawler_config = self.config.get_crawler_config(crawler_name)
            frequency = self.config.get_crawl_frequency(crawler_name)
            
            status[crawler_name] = {
                'enabled': crawler_config.get('enabled', True),
                'frequency': str(frequency),
                'last_run': self.last_run_time.get(crawler_name),
                'stats': crawler.stats
            }
        
        return status
