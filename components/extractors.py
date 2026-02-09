"""
提取器实现
"""
import re
from typing import Dict, List, Any
from bs4 import BeautifulSoup
from .base import BaseExtractor


class CssExtractor(BaseExtractor):
    """CSS选择器提取器"""
    
    async def extract(self, content: Dict[str, Any], fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """使用CSS选择器提取数据"""
        soup = content.get('soup')
        if not soup:
            return []
        
        items = []
        
        # 获取容器选择器
        container_selector = fields.get('container', 'body')
        containers = soup.select(container_selector)
        
        # 特殊处理：ArXiv列表页面（dt/dd结构）
        # 如果容器选择器是dt，强制使用ArXiv特殊提取逻辑
        dt_elements = soup.select('dt')
        if dt_elements and container_selector == 'dt':
            # 为每个dt找到对应的dd
            for dt in dt_elements:
                item = {}
                # 提取标识符和链接
                identifier_link = dt.select_one('a[href*="arxiv"], a[href*="abs"]')
                if identifier_link:
                    item['url'] = identifier_link.get('href', '')
                    if not item['url'].startswith('http'):
                        item['url'] = 'https://arxiv.org' + item['url']
                    # 优先使用abs链接（论文详情页）
                    if '/abs/' in item['url']:
                        pass  # 使用abs链接
                    elif '/html/' in item['url']:
                        # 将html链接转换为abs链接
                        item['url'] = item['url'].replace('/html/', '/abs/').replace('v1', '').replace('v2', '').replace('v3', '').replace('v4', '')
                
                # 查找对应的dd元素
                dd = dt.find_next_sibling('dd')
                if dd:
                    # ArXiv页面结构：
                    # <div class="list-title">包含标题
                    # <div class="list-authors">包含作者
                    # <div class="list-subjects">包含主题
                    
                    # 提取标题 - 从div.list-title中提取
                    title_div = dd.select_one('div.list-title')
                    if title_div:
                        # 获取标题文本，去除"Title:"前缀
                        title_text = title_div.get_text(strip=True)
                        if title_text.startswith('Title:'):
                            title_text = title_text[6:].strip()
                        item['title'] = title_text
                    
                    # 提取作者 - 从div.list-authors中提取
                    authors_div = dd.select_one('div.list-authors')
                    if authors_div:
                        authors_text = authors_div.get_text(strip=True)
                        # 去除"Authors:"前缀
                        if authors_text.startswith('Authors:'):
                            authors_text = authors_text[8:].strip()
                        item['content'] = f"Authors: {authors_text}"
                    
                    # 提取主题 - 从div.list-subjects或span.primary-subject中提取
                    subjects_div = dd.select_one('div.list-subjects')
                    if not subjects_div:
                        subjects_div = dd.select_one('span.primary-subject')
                    if subjects_div:
                        subjects_text = subjects_div.get_text(strip=True)
                        # 去除"Subjects:"前缀
                        if subjects_text.startswith('Subjects:'):
                            subjects_text = subjects_text[9:].strip()
                        if item.get('content'):
                            item['content'] += f" | Subjects: {subjects_text}"
                        else:
                            item['content'] = f"Subjects: {subjects_text}"
                    
                    # 如果没找到标题，尝试从dd文本中提取
                    if not item.get('title'):
                        dd_text = dd.get_text(separator=' ', strip=True)
                        if 'Title:' in dd_text:
                            title_part = dd_text.split('Title:')[1].split('Authors:')[0].strip()
                            if title_part:
                                item['title'] = title_part
                    
                    # 如果没有提取到标题，使用标识符作为标题
                    if not item.get('title') and identifier_link:
                        item['title'] = identifier_link.get_text(strip=True)
                
                # 如果没有找到标题，尝试从dt中提取
                if not item.get('title') and identifier_link:
                    item['title'] = identifier_link.get_text(strip=True)
                
                if item:
                    items.append(item)
            
            if items:
                return items
        
        # 标准提取流程
        for container in containers:
            item = {}
            for field_name, field_config in fields.get('fields', {}).items():
                selector = field_config.get('selector')
                if selector:
                    element = container.select_one(selector)
                    if element:
                        attr = field_config.get('attr', 'text')
                        if attr == 'text':
                            item[field_name] = element.get_text(strip=True)
                        else:
                            value = element.get(attr, '')
                            # 如果是URL且是相对路径，转换为绝对路径
                            if field_name == 'url' and value and not value.startswith('http'):
                                source_url = content.get('url', '')
                                if source_url:
                                    from urllib.parse import urljoin
                                    item[field_name] = urljoin(source_url, value)
                                else:
                                    item[field_name] = value
                            else:
                                item[field_name] = value
            
            if item:
                items.append(item)
        
        # 如果还是没有提取到数据，尝试从整个页面提取基本信息
        if not items:
            item = {}
            # 提取页面标题
            title_elem = soup.select_one('title')
            if title_elem:
                item['title'] = title_elem.get_text(strip=True)
            
            # 提取meta描述
            meta_desc = soup.select_one('meta[name="description"]')
            if meta_desc:
                item['description'] = meta_desc.get('content', '')
            
            # 提取主要内容
            main_content = soup.select_one('main, article, .content, #content')
            if main_content:
                item['content'] = main_content.get_text(strip=True)[:1000]  # 限制长度
            
            if item:
                items.append(item)
        
        return items


class XPathExtractor(BaseExtractor):
    """XPath提取器"""
    
    async def extract(self, content: Dict[str, Any], fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """使用XPath提取数据"""
        from lxml import etree
        
        html = content.get('html', '')
        if not html:
            return []
        
        tree = etree.HTML(html)
        items = []
        
        # 获取容器XPath
        container_xpath = fields.get('container', '//body')
        containers = tree.xpath(container_xpath)
        
        for container in containers:
            item = {}
            for field_name, field_config in fields.get('fields', {}).items():
                xpath = field_config.get('xpath')
                if xpath:
                    elements = container.xpath(xpath)
                    if elements:
                        attr = field_config.get('attr', 'text')
                        if attr == 'text':
                            item[field_name] = elements[0].text or ''
                        else:
                            item[field_name] = elements[0].get(attr, '')
            
            if item:
                items.append(item)
        
        return items


class RegexExtractor(BaseExtractor):
    """正则表达式提取器"""
    
    async def extract(self, content: Dict[str, Any], fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """使用正则表达式提取数据"""
        text = content.get('text', '')
        if not text:
            return []
        
        items = []
        item = {}
        
        for field_name, field_config in fields.get('fields', {}).items():
            pattern = field_config.get('pattern')
            if pattern:
                match = re.search(pattern, text)
                if match:
                    item[field_name] = match.group(1) if match.groups() else match.group(0)
        
        if item:
            items.append(item)
        
        return items
