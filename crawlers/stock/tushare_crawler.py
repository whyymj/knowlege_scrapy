"""
Tushare 数据爬虫
"""
import json
from typing import List, Dict, Any
from ..base import BaseCrawler


class TushareCrawler(BaseCrawler):
    """Tushare API 爬虫"""
    
    def __init__(self, config=None):
        super().__init__('stock_tushare', config)
        self.api_url = self.crawler_config.get('api_url', 'http://api.tushare.pro')
        self.token = self.crawler_config.get('token', '')
    
    def crawl(self) -> List[Dict[str, Any]]:
        """爬取Tushare数据"""
        items = []
        
        if not self.token:
            self.log_warning('Tushare token未配置，跳过爬取')
            return items
        
        # 获取股票列表
        stock_list = self._get_stock_list()
        
        # 获取每只股票的实时行情
        for stock_code in stock_list[:10]:  # 限制数量
            quote_data = self._get_realtime_quote(stock_code)
            if quote_data:
                items.append(quote_data)
        
        return items
    
    def _call_api(self, api_name: str, params: Dict) -> Dict:
        """调用Tushare API"""
        data = {
            'api_name': api_name,
            'token': self.token,
            'params': json.dumps(params)
        }
        
        response = self._make_request(self.api_url, method='POST', data=data)
        if response:
            try:
                return response.json()
            except:
                return {}
        return {}
    
    def _get_stock_list(self) -> List[str]:
        """获取股票列表"""
        result = self._call_api('stock_basic', {
            'exchange': '',
            'list_status': 'L',
            'fields': 'ts_code,symbol,name'
        })
        
        stock_list = []
        if result.get('code') == 0:
            data = result.get('data', {})
            stock_list = [item[0] for item in data.get('items', [])]
        
        return stock_list
    
    def _get_realtime_quote(self, stock_code: str) -> Dict[str, Any]:
        """获取实时行情"""
        result = self._call_api('realtime_quote', {
            'ts_code': stock_code,
            'fields': 'ts_code,name,price,change,percent,volume,amount'
        })
        
        if result.get('code') == 0:
            data = result.get('data', {})
            items = data.get('items', [])
            if items:
                quote = items[0]
                return {
                    'url': f'https://tushare.pro/stock/{stock_code}',
                    'symbol': quote[0] if len(quote) > 0 else stock_code,
                    'name': quote[1] if len(quote) > 1 else '',
                    'price': quote[2] if len(quote) > 2 else '',
                    'change': quote[3] if len(quote) > 3 else '',
                    'percent': quote[4] if len(quote) > 4 else '',
                    'volume': quote[5] if len(quote) > 5 else '',
                    'amount': quote[6] if len(quote) > 6 else '',
                    'source': 'tushare',
                    'category': 'stock',
                    'type': 'quote'
                }
        
        return None
    
    def parse(self, response) -> List[Dict[str, Any]]:
        """解析响应"""
        return []
