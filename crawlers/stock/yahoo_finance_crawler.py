"""
Yahoo Finance 爬虫
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from ..base import BaseCrawler


class YahooFinanceCrawler(BaseCrawler):
    """Yahoo Finance 股票数据爬虫"""
    
    def __init__(self, config=None):
        super().__init__('stock_yahoo_finance', config)
        self.base_url = self.crawler_config.get('base_url', 'https://finance.yahoo.com')
        self.api_key = self.crawler_config.get('api_key', '')
    
    def crawl(self) -> List[Dict[str, Any]]:
        """爬取股票数据"""
        items = []
        
        # 热门股票代码列表（可以配置）
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA']
        
        for symbol in symbols:
            # 获取股票基本信息
            quote_url = f'{self.base_url}/quote/{symbol}'
            response = self._make_request(quote_url)
            if response:
                item = self._parse_quote(symbol, response)
                if item:
                    items.append(item)
            
            # 获取新闻
            news_url = f'{self.base_url}/quote/{symbol}/news'
            response = self._make_request(news_url)
            if response:
                news_items = self._parse_news(symbol, response)
                items.extend(news_items)
        
        return items
    
    def _parse_quote(self, symbol: str, response) -> Dict[str, Any]:
        """解析股票报价信息"""
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取价格信息（需要根据实际HTML结构调整）
            price_tag = soup.find('span', {'data-reactid': '50'}) or soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
            price = price_tag.text.strip() if price_tag else ''
            
            # 提取涨跌幅
            change_tag = soup.find('span', {'data-reactid': '51'}) or soup.find('fin-streamer', {'data-field': 'regularMarketChangePercent'})
            change = change_tag.text.strip() if change_tag else ''
            
            item = {
                'url': f'{self.base_url}/quote/{symbol}',
                'symbol': symbol,
                'price': price,
                'change': change,
                'source': 'yahoo_finance',
                'category': 'stock',
                'type': 'quote'
            }
            
            return item
            
        except Exception as e:
            self.log_error(f'解析股票报价失败: {symbol}, {str(e)}')
            return None
    
    def _parse_news(self, symbol: str, response) -> List[Dict[str, Any]]:
        """解析股票新闻"""
        items = []
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找新闻列表
            news_list = soup.find_all('li', class_='js-stream-content') or soup.find_all('div', class_='news-item')
            
            for news in news_list:
                try:
                    title_tag = news.find('h3') or news.find('a')
                    if not title_tag:
                        continue
                    
                    title = title_tag.text.strip()
                    link_tag = title_tag.find('a') if title_tag.name != 'a' else title_tag
                    news_url = link_tag.get('href', '')
                    
                    if news_url.startswith('/'):
                        news_url = self.base_url + news_url
                    
                    date_tag = news.find('time') or news.find('span', class_='date')
                    date = date_tag.get('datetime', '') if date_tag else ''
                    
                    item = {
                        'url': news_url,
                        'title': title,
                        'symbol': symbol,
                        'publish_date': date,
                        'source': 'yahoo_finance',
                        'category': 'stock',
                        'type': 'news'
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    self.log_error(f'解析新闻失败: {str(e)}')
                    continue
            
        except Exception as e:
            self.log_error(f'解析新闻列表失败: {str(e)}')
        
        return items
    
    def parse(self, response) -> List[Dict[str, Any]]:
        """解析响应"""
        return []
