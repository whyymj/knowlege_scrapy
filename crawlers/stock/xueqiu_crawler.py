"""
雪球爬虫
"""
import json
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from ..base import BaseCrawler


class XueqiuCrawler(BaseCrawler):
    """雪球爬虫"""
    
    def __init__(self, config=None):
        super().__init__('stock_xueqiu', config)
        self.base_url = self.crawler_config.get('base_url', 'https://xueqiu.com')
    
    def crawl(self) -> List[Dict[str, Any]]:
        """爬取雪球数据"""
        items = []
        
        # 热门股票代码
        symbols = ['SH000001', 'SZ399001', 'SH600519', 'SZ000858']
        
        for symbol in symbols:
            # 获取股票信息
            quote_url = f'{self.base_url}/S/{symbol}'
            response = self._make_request(quote_url)
            if response:
                item = self._parse_quote(symbol, response)
                if item:
                    items.append(item)
            
            # 获取讨论/情绪数据
            status_url = f'{self.base_url}/statuses/search.json'
            params = {
                'symbol': symbol,
                'count': 20,
                'comment': 0,
                'hl': 0,
                'source': 'all',
                'sort': 'time'
            }
            response = self._make_request(status_url, params=params)
            if response:
                status_items = self._parse_status(symbol, response)
                items.extend(status_items)
        
        return items
    
    def _parse_quote(self, symbol: str, response) -> Dict[str, Any]:
        """解析股票报价"""
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取价格信息（需要根据实际HTML结构调整）
            price_tag = soup.find('div', class_='stock-price')
            price = price_tag.text.strip() if price_tag else ''
            
            item = {
                'url': f'{self.base_url}/S/{symbol}',
                'symbol': symbol,
                'price': price,
                'source': 'xueqiu',
                'category': 'stock',
                'type': 'quote'
            }
            
            return item
            
        except Exception as e:
            self.log_error(f'解析股票报价失败: {symbol}, {str(e)}')
            return None
    
    def _parse_status(self, symbol: str, response) -> List[Dict[str, Any]]:
        """解析讨论/情绪数据"""
        items = []
        try:
            data = response.json()
            statuses = data.get('list', [])
            
            for status in statuses:
                item = {
                    'url': f'{self.base_url}/statuses/{status.get("id", "")}',
                    'title': status.get('title', ''),
                    'text': status.get('text', ''),
                    'symbol': symbol,
                    'created_at': status.get('created_at', ''),
                    'source': 'xueqiu',
                    'category': 'stock',
                    'type': 'social_sentiment'
                }
                items.append(item)
                
        except Exception as e:
            self.log_error(f'解析讨论数据失败: {str(e)}')
        
        return items
    
    def parse(self, response) -> List[Dict[str, Any]]:
        """解析响应"""
        return []
