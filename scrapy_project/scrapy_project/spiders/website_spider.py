import scrapy
from urllib.parse import urlparse
from datetime import datetime
from scrapy_project.items import WebsiteItem


class WebsiteSpider(scrapy.Spider):
    """网站信息爬虫"""
    name = 'website'
    allowed_domains = []
    start_urls = []
    
    def __init__(self, *args, **kwargs):
        super(WebsiteSpider, self).__init__(*args, **kwargs)
        # 可以通过命令行参数传入起始URL
        if hasattr(self, 'start_url'):
            self.start_urls = [self.start_url]
        elif hasattr(self, 'start_urls_list'):
            self.start_urls = self.start_urls_list.split(',')
    
    def parse(self, response):
        """解析网页内容"""
        item = WebsiteItem()
        
        # 基本信息
        item['url'] = response.url
        item['status_code'] = response.status
        item['crawl_time'] = datetime.now()
        
        # 解析域名
        parsed_url = urlparse(response.url)
        item['domain'] = parsed_url.netloc
        
        # 提取标题
        title = response.css('title::text').get()
        if not title:
            title = response.xpath('//title/text()').get()
        item['title'] = title.strip() if title else None
        
        # 提取描述（meta description）
        description = response.css('meta[name="description"]::attr(content)').get()
        if not description:
            description = response.xpath('//meta[@name="description"]/@content').get()
        item['description'] = description.strip() if description else None
        
        # 提取关键词（meta keywords）
        keywords = response.css('meta[name="keywords"]::attr(content)').get()
        if not keywords:
            keywords = response.xpath('//meta[@name="keywords"]/@content').get()
        item['keywords'] = keywords.strip() if keywords else None
        
        # 提取作者（meta author）
        author = response.css('meta[name="author"]::attr(content)').get()
        if not author:
            author = response.xpath('//meta[@name="author"]/@content').get()
        item['author'] = author.strip() if author else None
        
        # 提取发布时间（尝试多种方式）
        publish_time = None
        # 尝试从 meta 标签获取
        time_selectors = [
            'meta[property="article:published_time"]::attr(content)',
            'meta[name="publishdate"]::attr(content)',
            'meta[name="date"]::attr(content)',
            'time[datetime]::attr(datetime)',
            'time::attr(datetime)'
        ]
        for selector in time_selectors:
            publish_time = response.css(selector).get()
            if publish_time:
                break
        item['publish_time'] = publish_time.strip() if publish_time else None
        
        # 提取主要内容（去除脚本和样式）
        # 优先提取 article、main 标签内容
        content_selectors = [
            'article',
            'main',
            '.content',
            '#content',
            '.post-content',
            '.article-content'
        ]
        
        content = None
        for selector in content_selectors:
            content_elements = response.css(selector)
            if content_elements:
                # 提取文本内容
                texts = content_elements.css('::text').getall()
                content = ' '.join([text.strip() for text in texts if text.strip()])
                if content:
                    break
        
        # 如果没有找到特定内容区域，提取 body 中的文本
        if not content:
            # 移除脚本和样式
            for script in response.css('script'):
                script.extract()
            for style in response.css('style'):
                style.extract()
            
            texts = response.css('body ::text').getall()
            content = ' '.join([text.strip() for text in texts if text.strip()])
        
        # 限制内容长度（避免过长）
        if content and len(content) > 50000:
            content = content[:50000] + '...'
        
        item['content'] = content
        
        self.logger.info(f'爬取完成: {response.url}')
        yield item
        
        # 可选：继续爬取页面内的链接（限制深度）
        if hasattr(self, 'follow_links') and self.follow_links == 'true':
            max_depth = int(getattr(self, 'max_depth', 1))
            current_depth = response.meta.get('depth', 0)
            
            if current_depth < max_depth:
                links = response.css('a::attr(href)').getall()
                for link in links:
                    if link:
                        absolute_url = response.urljoin(link)
                        # 只爬取同域名的链接
                        if urlparse(absolute_url).netloc == item['domain']:
                            yield scrapy.Request(
                                absolute_url,
                                callback=self.parse,
                                meta={'depth': current_depth + 1}
                            )
