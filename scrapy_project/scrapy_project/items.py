import scrapy


class WebsiteItem(scrapy.Item):
    """网站信息项"""
    url = scrapy.Field()  # 网站URL
    title = scrapy.Field()  # 网站标题
    description = scrapy.Field()  # 网站描述
    content = scrapy.Field()  # 网站主要内容
    keywords = scrapy.Field()  # 关键词
    author = scrapy.Field()  # 作者
    publish_time = scrapy.Field()  # 发布时间
    crawl_time = scrapy.Field()  # 爬取时间
    domain = scrapy.Field()  # 域名
    status_code = scrapy.Field()  # HTTP状态码
