"""
GitHub Trending AI Repos 爬虫
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from ..base import BaseCrawler


class GitHubTrendingCrawler(BaseCrawler):
    """GitHub Trending AI Repos 爬虫"""
    
    def __init__(self, config=None):
        super().__init__('ai_github_trending', config)
        self.base_url = self.crawler_config.get('base_url', 'https://github.com/trending')
        self.language = self.crawler_config.get('language', 'python')
    
    def crawl(self) -> List[Dict[str, Any]]:
        """爬取GitHub Trending仓库"""
        items = []
        
        # 爬取不同语言的trending
        languages = ['python', 'javascript', 'go', 'rust', 'java']
        
        for lang in languages:
            url = f'{self.base_url}/{lang}?since=daily'
            response = self._make_request(url)
            if response:
                parsed_items = self.parse(response)
                # 添加语言标签
                for item in parsed_items:
                    item['language'] = lang
                items.extend(parsed_items)
        
        return items
    
    def parse(self, response) -> List[Dict[str, Any]]:
        """解析GitHub Trending页面"""
        items = []
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找仓库列表
        repo_list = soup.find_all('article', class_='Box-row')
        
        for repo in repo_list:
            try:
                # 提取仓库名称和链接
                title_tag = repo.find('h2', class_='h3')
                if not title_tag:
                    continue
                
                link_tag = title_tag.find('a')
                if not link_tag:
                    continue
                
                repo_name = link_tag.get('href', '').strip('/')
                repo_url = 'https://github.com' + link_tag.get('href', '')
                
                # 提取描述
                desc_tag = repo.find('p', class_='col-9')
                description = desc_tag.text.strip() if desc_tag else ''
                
                # 提取stars和forks
                stars_tag = repo.find('a', href=lambda x: x and '/stargazers' in x)
                stars = stars_tag.text.strip() if stars_tag else '0'
                
                forks_tag = repo.find('a', href=lambda x: x and '/network' in x)
                forks = forks_tag.text.strip() if forks_tag else '0'
                
                # 提取今日stars增长
                stars_today_tag = repo.find('span', class_='d-inline-block')
                stars_today = stars_today_tag.text.strip() if stars_today_tag else '0'
                
                item = {
                    'url': repo_url,
                    'title': repo_name,
                    'description': description,
                    'stars': stars,
                    'forks': forks,
                    'stars_today': stars_today,
                    'source': 'github_trending',
                    'category': 'AI',
                    'type': 'github_repo'
                }
                
                items.append(item)
                
            except Exception as e:
                self.log_error(f'解析仓库失败: {str(e)}')
                continue
        
        return items
