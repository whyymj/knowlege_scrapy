from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
from datetime import datetime
from functools import wraps
import json
import sys
import os

# 添加项目根目录到路径，以便导入 utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.config_loader import config

app = Flask(__name__)

# 从配置文件读取 CORS 设置
backend_config = config.get_backend_config()
if backend_config.get('cors_enabled', True):
    CORS(app)

# MySQL 数据库配置（从 config.json 读取，支持环境变量覆盖）
db_config = config.get_database_config()
MYSQL_CONFIG = {
    'host': db_config.get('host', 'localhost'),
    'port': db_config.get('port', 3306),
    'db': db_config.get('db', 'scrapy_db'),
    'user': db_config.get('user', 'root'),
    'password': db_config.get('password', ''),
    'charset': db_config.get('charset', 'utf8mb4'),
    'cursorclass': pymysql.cursors.DictCursor
}


def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**MYSQL_CONFIG)


def json_response(func):
    """JSON响应装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': result
            })
        except Exception as e:
            return jsonify({
                'code': 500,
                'message': str(e),
                'data': None
            }), 500
    return wrapper


@app.route('/api/websites', methods=['GET'])
@json_response
def get_websites():
    """获取网站列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        domain = request.args.get('domain', '')
        keyword = request.args.get('keyword', '')
        
        # 构建查询条件
        where_clauses = []
        params = []
        
        if domain:
            where_clauses.append('domain LIKE %s')
            params.append(f'%{domain}%')
        
        if keyword:
            where_clauses.append('(title LIKE %s OR description LIKE %s OR content LIKE %s)')
            params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
        
        where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
        
        # 查询总数
        count_sql = f'SELECT COUNT(*) as total FROM website_info WHERE {where_sql}'
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']
        
        # 查询数据
        offset = (page - 1) * page_size
        query_sql = f'''
            SELECT id, url, title, description, keywords, author, 
                   publish_time, crawl_time, domain, status_code, created_at
            FROM website_info 
            WHERE {where_sql}
            ORDER BY crawl_time DESC
            LIMIT %s OFFSET %s
        '''
        cursor.execute(query_sql, params + [page_size, offset])
        websites = cursor.fetchall()
        
        # 转换日期格式
        for website in websites:
            for key in ['publish_time', 'crawl_time', 'created_at']:
                if website[key] and isinstance(website[key], datetime):
                    website[key] = website[key].strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'list': websites,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    finally:
        cursor.close()
        conn.close()


@app.route('/api/websites/<int:website_id>', methods=['GET'])
@json_response
def get_website_detail(website_id):
    """获取网站详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query_sql = '''
            SELECT * FROM website_info WHERE id = %s
        '''
        cursor.execute(query_sql, [website_id])
        website = cursor.fetchone()
        
        if not website:
            return None
        
        # 转换日期格式
        for key in ['publish_time', 'crawl_time', 'created_at', 'updated_at']:
            if website[key] and isinstance(website[key], datetime):
                website[key] = website[key].strftime('%Y-%m-%d %H:%M:%S')
        
        return website
    finally:
        cursor.close()
        conn.close()


@app.route('/api/websites/<int:website_id>', methods=['DELETE'])
@json_response
def delete_website(website_id):
    """删除网站记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        delete_sql = 'DELETE FROM website_info WHERE id = %s'
        cursor.execute(delete_sql, [website_id])
        conn.commit()
        return {'id': website_id}
    finally:
        cursor.close()
        conn.close()


@app.route('/api/statistics', methods=['GET'])
@json_response
def get_statistics():
    """获取统计信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 总数统计
        cursor.execute('SELECT COUNT(*) as total FROM website_info')
        total = cursor.fetchone()['total']
        
        # 按域名统计
        cursor.execute('''
            SELECT domain, COUNT(*) as count 
            FROM website_info 
            GROUP BY domain 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        domain_stats = cursor.fetchall()
        
        # 按日期统计（最近7天）
        cursor.execute('''
            SELECT DATE(crawl_time) as date, COUNT(*) as count 
            FROM website_info 
            WHERE crawl_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(crawl_time)
            ORDER BY date DESC
        ''')
        date_stats = cursor.fetchall()
        
        # 转换日期格式
        for stat in date_stats:
            if stat['date']:
                stat['date'] = stat['date'].strftime('%Y-%m-%d')
        
        return {
            'total': total,
            'domain_stats': domain_stats,
            'date_stats': date_stats
        }
    finally:
        cursor.close()
        conn.close()


@app.route('/api/crawl', methods=['POST'])
@json_response
def start_crawl():
    """启动爬虫任务"""
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        raise ValueError('URL不能为空')
    
    # 这里可以集成 Scrapy 的调度器或者直接调用爬虫
    # 简化版本：返回成功，实际需要集成 Scrapy
    import subprocess
    import os
    
    # 切换到 scrapy 项目目录
    scrapy_dir = os.path.join(os.path.dirname(__file__), '..', 'scrapy_project')
    
    # 运行爬虫
    cmd = ['scrapy', 'crawl', 'website', '-a', f'start_url={url}']
    result = subprocess.run(cmd, cwd=scrapy_dir, capture_output=True, text=True)
    
    if result.returncode == 0:
        return {'message': '爬虫任务已启动', 'url': url}
    else:
        raise Exception(f'爬虫启动失败: {result.stderr}')


if __name__ == '__main__':
    backend_config = config.get_backend_config()
    app.run(
        debug=backend_config.get('debug', False),
        host=backend_config.get('host', '0.0.0.0'),
        port=backend_config.get('port', 5000)
    )
