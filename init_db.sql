-- 创建数据库
CREATE DATABASE IF NOT EXISTS scrapy_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE scrapy_db;

-- 创建网站信息表
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
    INDEX idx_crawl_time (crawl_time),
    INDEX idx_url (url(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
