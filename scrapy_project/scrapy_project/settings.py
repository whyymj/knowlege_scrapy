# Scrapy settings for scrapy_project project
import os
import json
from pathlib import Path

# 加载统一配置文件
def load_config():
    """加载 config.json 配置文件"""
    # 获取项目根目录（向上两级：scrapy_project/scrapy_project -> scrapy）
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    config_file = project_root / 'config.json'
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# 加载配置
_config = load_config()
_scrapy_config = _config.get('scrapy', {})
_database_config = _config.get('database', {})

BOT_NAME = 'scrapy_project'

SPIDER_MODULES = ['scrapy_project.spiders']
NEWSPIDER_MODULE = 'scrapy_project.spiders'

# Obey robots.txt rules（从配置文件读取，环境变量优先）
ROBOTSTXT_OBEY = os.getenv('ROBOTSTXT_OBEY', str(_scrapy_config.get('obey_robots_txt', False))).lower() == 'true'

# Configure a delay for requests for the same website（从配置文件读取）
DOWNLOAD_DELAY = float(os.getenv('DOWNLOAD_DELAY', _scrapy_config.get('download_delay', 1)))

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = int(os.getenv('CONCURRENT_REQUESTS_PER_DOMAIN', _scrapy_config.get('concurrent_requests', 16)))
CONCURRENT_REQUESTS_PER_IP = CONCURRENT_REQUESTS_PER_DOMAIN

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers（从配置文件读取）
_user_agent = os.getenv('USER_AGENT', _scrapy_config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'))
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'User-Agent': _user_agent
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    'scrapy_project.middlewares.ScrapyProjectSpiderMiddleware': 543,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'scrapy_project.middlewares.ScrapyProjectDownloaderMiddleware': 543,
}

# Configure item pipelines
ITEM_PIPELINES = {
    'scrapy_project.pipelines.MysqlPipeline': 300,
}

# MySQL 数据库配置（从 config.json 读取，环境变量优先）
MYSQL_HOST = os.getenv('MYSQL_HOST', _database_config.get('host', 'localhost'))
MYSQL_PORT = int(os.getenv('MYSQL_PORT', _database_config.get('port', 3308)))
MYSQL_DB = os.getenv('MYSQL_DB', _database_config.get('db', 'scrapy_db'))
MYSQL_USER = os.getenv('MYSQL_USER', _database_config.get('user', 'root'))
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', _database_config.get('password', ''))

# Enable and configure the AutoThrottle extension (disabled by default)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching（从配置文件读取）
HTTPCACHE_ENABLED = os.getenv('HTTPCACHE_ENABLED', str(_scrapy_config.get('httpcache_enabled', True))).lower() == 'true'
HTTPCACHE_EXPIRATION_SECS = int(os.getenv('HTTPCACHE_EXPIRATION_SECS', _scrapy_config.get('httpcache_expiration_secs', 3600)))
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
