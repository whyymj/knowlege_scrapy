"""
解析器实现
"""
from typing import Dict, Any
from bs4 import BeautifulSoup
import json
from .base import BaseParser


class HtmlParser(BaseParser):
    """HTML解析器"""
    
    async def parse(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """解析HTML页面"""
        content = page.get('content', '')
        parser_type = self.config.get('parser_type', 'html.parser')
        
        soup = BeautifulSoup(content, parser_type)
        
        return {
            'url': page.get('url'),
            'soup': soup,
            'text': soup.get_text(),
            'html': str(soup)
        }


class JsonParser(BaseParser):
    """JSON解析器"""
    
    async def parse(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """解析JSON数据"""
        data = page.get('data')
        
        if isinstance(data, str):
            data = json.loads(data)
        
        return {
            'url': page.get('url'),
            'data': data
        }
