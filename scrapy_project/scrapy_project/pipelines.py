import pymysql
from datetime import datetime
from scrapy_project.settings import MYSQL_HOST, MYSQL_PORT, MYSQL_DB, MYSQL_USER, MYSQL_PASSWORD


class MysqlPipeline:
    """MySQL存储管道"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def open_spider(self, spider):
        """爬虫启动时连接数据库"""
        try:
            self.conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                db=MYSQL_DB,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.conn.cursor()
            spider.logger.info('MySQL数据库连接成功')
            
            # 创建表（如果不存在）
            self.create_table()
        except Exception as e:
            spider.logger.error(f'MySQL数据库连接失败: {e}')
            raise
    
    def close_spider(self, spider):
        """爬虫关闭时关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        spider.logger.info('MySQL数据库连接已关闭')
    
    def create_table(self):
        """创建数据表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS website_info (
            id INT AUTO_INCREMENT PRIMARY KEY,
            url VARCHAR(500) NOT NULL UNIQUE,
            title VARCHAR(500),
            description TEXT,
            content LONGTEXT,
            keywords VARCHAR(500),
            author VARCHAR(200),
            publish_time DATETIME,
            crawl_time DATETIME NOT NULL,
            domain VARCHAR(200),
            status_code INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_domain (domain),
            INDEX idx_crawl_time (crawl_time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.cursor.execute(create_table_sql)
        self.conn.commit()
    
    def process_item(self, item, spider):
        """处理爬取的数据项"""
        try:
            # 准备插入数据
            insert_sql = """
            INSERT INTO website_info 
            (url, title, description, content, keywords, author, publish_time, crawl_time, domain, status_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            description = VALUES(description),
            content = VALUES(content),
            keywords = VALUES(keywords),
            author = VALUES(author),
            publish_time = VALUES(publish_time),
            crawl_time = VALUES(crawl_time),
            domain = VALUES(domain),
            status_code = VALUES(status_code)
            """
            
            values = (
                item.get('url'),
                item.get('title'),
                item.get('description'),
                item.get('content'),
                item.get('keywords'),
                item.get('author'),
                item.get('publish_time'),
                item.get('crawl_time') or datetime.now(),
                item.get('domain'),
                item.get('status_code')
            )
            
            self.cursor.execute(insert_sql, values)
            self.conn.commit()
            spider.logger.info(f'数据已保存: {item.get("url")}')
            
        except Exception as e:
            spider.logger.error(f'保存数据失败: {e}')
            self.conn.rollback()
            raise
        
        return item
