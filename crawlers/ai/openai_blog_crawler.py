"""
OpenAI Blog 爬虫
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from ..base import BaseCrawler


class OpenAIBlogCrawler(BaseCrawler):
    """OpenAI Blog 爬虫"""
    
    def __init__(self, config=None):
        super().__init__('ai_openai_blog', config)
        self.base_url = self.crawler_config.get('base_url', 'https://openai.com/blog')
    
    def crawl(self) -> List[Dict[str, Any]]:
        """爬取OpenAI Blog文章"""
        items = []
        
        # 爬取博客首页
        response = self._make_request(self.base_url)
        if response:
            parsed_items = self.parse(response)
            items.extend(parsed_items)
        
        return items
    
    def parse(self, response) -> List[Dict[str, Any]]:
        """解析OpenAI Blog页面"""
        items = []
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找文章列表（根据实际HTML结构调整选择器）
        article_list = soup.find_all('article') or soup.find_all('div', class_='post')
        
        for article in article_list:
            try:
                # 提取文章标题和链接
                title_tag = article.find('h2') or article.find('h3') or article.find('a')
                if not title_tag:
                    continue
                
                link_tag = title_tag.find('a') if title_tag.name != 'a' else title_tag
                if not link_tag:
                    continue
                
                title = link_tag.text.strip()
                article_url = link_tag.get('href', '')
                
                # 处理相对URL
                if article_url.startswith('/'):
                    article_url = 'https://openai.com' + article_url
                
                # 提取发布日期
                date_tag = article.find('time') or article.find('span', class_='date')
                date = date_tag.get('datetime', '') if date_tag else ''
                if not date and date_tag:
                    date = date_tag.text.strip()
                
                # 提取摘要
                desc_tag = article.find('p') or article.find('div', class_='excerpt')
                description = desc_tag.text.strip() if desc_tag else ''
                
                item = {
                    'url': article_url,
                    'title': title,
                    'description': description,
                    'publish_date': date,
                    'source': 'openai_blog',
                    'category': 'AI',
                    'type': 'blog_post'
                }
                
                items.append(item)
                
            except Exception as e:
                self.log_error(f'解析文章失败: {str(e)}')
                continue
        
        return items
