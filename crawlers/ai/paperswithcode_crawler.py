"""
PapersWithCode 爬虫
"""
import json
from typing import List, Dict, Any

try:
    from ..base import BaseCrawler
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from crawlers.base import BaseCrawler


class PapersWithCodeCrawler(BaseCrawler):
    """PapersWithCode 爬虫"""
    
    def __init__(self, config=None):
        super().__init__('ai_paperswithcode', config)
        self.api_url = self.crawler_config.get('api_url', 'https://paperswithcode.com/api/v1/papers/')
        self.base_url = self.crawler_config.get('base_url', 'https://paperswithcode.com')
    
    def crawl(self) -> List[Dict[str, Any]]:
        """爬取PapersWithCode论文"""
        items = []
        
        # 通过API获取热门论文
        params = {
            'ordering': 'added',
            'page': 1,
            'page_size': 50
        }
        
        response = self._make_request(self.api_url, method='GET', params=params)
        if response:
            try:
                data = response.json()
                results = data.get('results', [])
                
                for paper in results:
                    item = self._parse_paper(paper)
                    if item:
                        items.append(item)
            except Exception as e:
                self.log_error(f'解析API响应失败: {str(e)}')
        
        return items
    
    def _parse_paper(self, paper_data: Dict) -> Dict[str, Any]:
        """解析单篇论文数据"""
        try:
            item = {
                'url': f"{self.base_url}{paper_data.get('id', '')}",
                'title': paper_data.get('title', ''),
                'abstract': paper_data.get('abstract', ''),
                'authors': ', '.join([a.get('name', '') for a in paper_data.get('authors', [])]),
                'published_date': paper_data.get('published', ''),
                'paper_id': paper_data.get('id', ''),
                'source': 'paperswithcode',
                'category': 'AI',
                'type': 'research_paper'
            }
            
            # 添加代码链接
            if 'github' in paper_data:
                item['github_url'] = paper_data['github']
            
            return item
            
        except Exception as e:
            self.log_error(f'解析论文数据失败: {str(e)}')
            return None
    
    def parse(self, response) -> List[Dict[str, Any]]:
        """解析响应（用于非API调用）"""
        # 如果直接爬取网页，可以在这里实现HTML解析
        return []
