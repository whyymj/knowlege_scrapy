"""
新浪财经爬虫
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from ..base import BaseCrawler


class SinaFinanceCrawler(BaseCrawler):
    """新浪财经爬虫"""
    
    def __init__(self, config=None):
        super().__init__('stock_sina_finance', config)
        self.base_url = self.crawler_config.get('base_url', 'https://finance.sina.com.cn')
    
    def crawl(self) -> List[Dict[str, Any]]:
        """爬取新浪财经数据"""
        items = []
        
        # 爬取财经新闻
        news_url = f'{self.base_url}/roll/index.d.html?cid=56592'
        response = self._make_request(news_url)
        if response:
            parsed_items = self.parse(response)
            items.extend(parsed_items)
        
        # 爬取股票新闻
        stock_news_url = f'{self.base_url}/stock'
        response = self._make_request(stock_news_url)
        if response:
            parsed_items = self.parse(response)
            items.extend(parsed_items)
        
        return items
    
    def parse(self, response) -> List[Dict[str, Any]]:
        """解析新浪财经页面"""
        items = []
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找新闻列表
        news_list = soup.find_all('li', class_='news_1') or soup.find_all('div', class_='news-item')
        
        for news in news_list:
            try:
                # 提取标题和链接
                title_tag = news.find('a')
                if not title_tag:
                    continue
                
                title = title_tag.text.strip()
                news_url = title_tag.get('href', '')
                
                # 处理相对URL
                if news_url.startswith('/'):
                    news_url = self.base_url + news_url
                elif not news_url.startswith('http'):
                    news_url = self.base_url + '/' + news_url
                
                # 提取时间
                time_tag = news.find('span', class_='time') or news.find('time')
                publish_time = time_tag.text.strip() if time_tag else ''
                
                item = {
                    'url': news_url,
                    'title': title,
                    'publish_time': publish_time,
                    'source': 'sina_finance',
                    'category': 'stock',
                    'type': 'news'
                }
                
                items.append(item)
                
            except Exception as e:
                self.log_error(f'解析新闻失败: {str(e)}')
                continue
        
        return items
