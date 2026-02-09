"""
arXiv AI论文爬虫
"""
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup

try:
    from ..base import BaseCrawler
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from crawlers.base import BaseCrawler


class ArxivCrawler(BaseCrawler):
    """arXiv AI论文爬虫"""
    
    def __init__(self, config=None):
        super().__init__('ai_arxiv', config)
        self.base_url = self.crawler_config.get('base_url', 'https://arxiv.org/list/cs.AI/recent')
    
    def crawl(self) -> List[Dict[str, Any]]:
        """爬取arXiv论文列表"""
        items = []
        
        # 爬取最近论文列表
        response = self._make_request(self.base_url)
        if response:
            parsed_items = self.parse(response)
            items.extend(parsed_items)
        
        # 可以扩展爬取其他分类
        categories = ['cs.AI', 'cs.LG', 'cs.CV', 'cs.CL', 'cs.NE']
        for category in categories:
            url = f'https://arxiv.org/list/{category}/recent'
            response = self._make_request(url)
            if response:
                parsed_items = self.parse(response)
                items.extend(parsed_items)
        
        return items
    
    def parse(self, response) -> List[Dict[str, Any]]:
        """解析arXiv页面"""
        items = []
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找论文列表
        dl_list = soup.find_all('dl')
        
        for dl in dl_list:
            try:
                # 提取论文信息
                dt = dl.find('dt')
                dd = dl.find('dd')
                
                if not dt or not dd:
                    continue
                
                # 提取arXiv ID和链接
                link_tag = dt.find('a', {'title': 'Abstract'})
                if not link_tag:
                    continue
                
                arxiv_id = link_tag.text.strip()
                paper_url = 'https://arxiv.org' + link_tag.get('href', '')
                
                # 提取标题
                title_tag = dd.find('div', class_='list-title')
                title = title_tag.text.replace('Title:', '').strip() if title_tag else ''
                
                # 提取作者
                authors_tag = dd.find('div', class_='list-authors')
                authors = []
                if authors_tag:
                    author_links = authors_tag.find_all('a')
                    authors = [a.text.strip() for a in author_links]
                
                # 提取摘要
                abstract_tag = dd.find('p', class_='mathjax')
                abstract = abstract_tag.text.strip() if abstract_tag else ''
                
                # 提取提交日期
                date_tag = dd.find('div', class_='list-date')
                date_text = date_tag.text.replace('Submitted', '').strip() if date_tag else ''
                
                item = {
                    'url': paper_url,
                    'title': title,
                    'authors': ', '.join(authors),
                    'abstract': abstract,
                    'arxiv_id': arxiv_id,
                    'date': date_text,
                    'source': 'arxiv',
                    'category': 'AI',
                    'type': 'research_paper'
                }
                
                items.append(item)
                
            except Exception as e:
                self.log_error(f'解析论文失败: {str(e)}')
                continue
        
        return items
