-- 创建数据库
CREATE DATABASE IF NOT EXISTS scrapy_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE scrapy_db;

-- 抓取任务表
CREATE TABLE IF NOT EXISTS crawl_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL UNIQUE COMMENT '任务ID',
    task_name VARCHAR(200) NOT NULL COMMENT '任务名称',
    task_config JSON NOT NULL COMMENT '任务配置（JSON格式）',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态：pending/running/completed/failed',
    items_count INT DEFAULT 0 COMMENT '提取的数据条数',
    errors_count INT DEFAULT 0 COMMENT '错误数量',
    started_at DATETIME COMMENT '开始时间',
    completed_at DATETIME COMMENT '完成时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_task_id (task_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='抓取任务表';

-- 抓取数据表（通用结构）
CREATE TABLE IF NOT EXISTS crawl_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL COMMENT '任务ID',
    source_url VARCHAR(500) NOT NULL COMMENT '源URL',
    data_type VARCHAR(50) NOT NULL DEFAULT 'general' COMMENT '数据类型：general/ai/stock/news等',
    title VARCHAR(500) COMMENT '标题',
    content LONGTEXT COMMENT '内容',
    metadata JSON COMMENT '元数据（JSON格式，存储额外字段）',
    extracted_at DATETIME NOT NULL COMMENT '提取时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_data_type (data_type),
    INDEX idx_source_url (source_url(255)),
    INDEX idx_extracted_at (extracted_at),
    INDEX idx_title (title(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='抓取数据表';

-- 任务执行日志表
CREATE TABLE IF NOT EXISTS task_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL COMMENT '任务ID',
    stage VARCHAR(50) NOT NULL COMMENT '执行阶段',
    level VARCHAR(20) NOT NULL COMMENT '日志级别：INFO/WARNING/ERROR',
    message TEXT NOT NULL COMMENT '日志消息',
    error_type VARCHAR(100) COMMENT '错误类型',
    error_message TEXT COMMENT '错误消息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_stage (stage),
    INDEX idx_level (level),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务执行日志表';

-- 任务指标表
CREATE TABLE IF NOT EXISTS task_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL COMMENT '任务ID',
    metric_name VARCHAR(100) NOT NULL COMMENT '指标名称',
    metric_value DECIMAL(20, 4) COMMENT '指标值（数值）',
    metric_data JSON COMMENT '指标数据（JSON格式）',
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_metric_name (metric_name),
    INDEX idx_recorded_at (recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务指标表';
