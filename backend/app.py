import os
import asyncio
import json
import sys
import logging
import threading
from typing import Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.config_loader import config

app = Flask(__name__)

# 导入翻译工具
try:
    from utils.translator import translate_item, is_chinese_text
    TRANSLATOR_AVAILABLE = True
except ImportError as e:
    TRANSLATOR_AVAILABLE = False
    app.logger.warning(f"翻译模块未导入，外文内容将不会被翻译: {e}")

# 配置日志
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# 加载配置
MYSQL_CONFIG = config.get_database_config()
BACKEND_CONFIG = config.get_backend_config()

# 启用CORS
if BACKEND_CONFIG.get('cors_enabled', True):
    CORS(app)

def save_crawl_items_to_db(task_id: str, items: list, task_config: dict = None):
    """
    将抓取到的页面信息保存到数据库（自动去重）
    
    Args:
        task_id: 任务ID
        items: 抓取到的数据项列表
        task_config: 任务配置（可选，用于获取默认URL）
    
    Returns:
        成功保存的数量
    """
    if not items:
        return 0
    
    saved_count = 0
    skipped_count = 0
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_data_sql = """
            INSERT INTO crawl_data (task_id, source_url, data_type, title, content, metadata, extracted_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        # 检查重复的SQL（基于source_url）
        check_duplicate_sql = """
            SELECT id FROM crawl_data 
            WHERE source_url = %s 
            LIMIT 1
        """
        
        for item in items:
            try:
                # 获取URL，优先级：item.url > item.source_url > metadata中的url > 任务配置中的第一个URL
                item_url = item.get('url') or item.get('source_url', '')
                if not item_url:
                    # 尝试从metadata中获取
                    if isinstance(item.get('metadata'), dict):
                        item_url = item.get('metadata', {}).get('url') or item.get('metadata', {}).get('source_url', '')
                    if not item_url:
                        if task_config:
                            source_urls = task_config.get('source', {}).get('urls', [])
                            item_url = source_urls[0] if source_urls else ''
                    if not item_url:
                        item_url = ''
                
                # 检查是否已存在（基于source_url去重）
                # 如果没有URL，使用标题+内容的前100字符作为唯一标识
                is_duplicate = False
                if item_url:
                    cursor.execute(check_duplicate_sql, (item_url,))
                    existing = cursor.fetchone()
                    if existing:
                        is_duplicate = True
                else:
                    # 如果没有URL，使用标题+内容hash作为去重标识
                    title = item.get('title', '')
                    content_preview = (item.get('content', '') or '')[:200]
                    if title or content_preview:
                        # 使用标题和内容预览的组合来检查重复
                        check_by_content_sql = """
                            SELECT id FROM crawl_data 
                            WHERE title = %s AND SUBSTRING(content, 1, 200) = %s
                            LIMIT 1
                        """
                        cursor.execute(check_by_content_sql, (title[:500], content_preview))
                        existing = cursor.fetchone()
                        if existing:
                            is_duplicate = True
                
                if is_duplicate:
                    skipped_count += 1
                    title_preview = item.get('title', '')[:50] or item_url[:50] or '未知'
                    app.logger.debug(f"跳过已存在的文章: {title_preview}")
                    continue
                
                # 构建完整的metadata，保存所有额外字段
                metadata = item.get('metadata', {})
                if not isinstance(metadata, dict):
                    metadata = {}
                
                # 保存所有item中的字段到metadata（除了已经在主字段中的）
                main_fields = ['title', 'content', 'data_type', 'url', 'source_url']
                for key, value in item.items():
                    if key not in main_fields and key not in metadata and value is not None:
                        # 处理特殊类型
                        if isinstance(value, (dict, list)):
                            metadata[key] = value
                        elif isinstance(value, str) and len(value) > 0:
                            metadata[key] = value
                        elif not isinstance(value, str):
                            metadata[key] = value
                
                # 确保关键字段在metadata中
                if 'url' not in metadata and item.get('url'):
                    metadata['url'] = item.get('url')
                if 'source_url' not in metadata and item.get('source_url'):
                    metadata['source_url'] = item.get('source_url')
                if 'description' not in metadata and item.get('description'):
                    metadata['description'] = item.get('description')
                
                # 翻译外文内容为中文
                if TRANSLATOR_AVAILABLE:
                    try:
                        # 检查是否需要翻译
                        title = item.get('title', '')
                        content = item.get('content', '')
                        need_translate = False
                        
                        if title and not is_chinese_text(title):
                            need_translate = True
                        elif content and not is_chinese_text(content):
                            need_translate = True
                        
                        if need_translate:
                            app.logger.info(f"检测到外文内容，开始翻译: {title[:50] if title else '无标题'}...")
                            translated_item = translate_item(item, translate_title=True, translate_content=True)
                            item = translated_item
                            # 更新metadata（翻译后的metadata可能包含原始内容）
                            if isinstance(item.get('metadata'), dict):
                                metadata.update(item.get('metadata', {}))
                            app.logger.info(f"翻译完成")
                    except Exception as translate_error:
                        app.logger.warning(f"翻译失败，使用原文本: {translate_error}")
                
                # 保存到数据库
                cursor.execute(insert_data_sql, (
                    task_id,
                    item_url,
                    item.get('data_type', 'general'),
                    item.get('title', '')[:500],  # 限制长度避免数据库错误
                    item.get('content', ''),
                    json.dumps(metadata, ensure_ascii=False),
                    datetime.now()
                ))
                saved_count += 1
                
            except Exception as item_error:
                app.logger.error(f"保存单个数据项失败: {item_error}")
                app.logger.error(f"数据项内容: {json.dumps(item, ensure_ascii=False, default=str)[:500]}")
                import traceback
                app.logger.error(traceback.format_exc())
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if skipped_count > 0:
            app.logger.info(f"任务 {task_id} 保存完成: 新增 {saved_count} 条, 跳过重复 {skipped_count} 条, 总计 {len(items)} 条")
        else:
            app.logger.info(f"任务 {task_id} 成功保存 {saved_count}/{len(items)} 条数据到数据库")
        
    except Exception as e:
        app.logger.error(f"保存数据到数据库失败: {e}")
        import traceback
        app.logger.error(traceback.format_exc())
        try:
            if conn:
                conn.rollback()
                conn.close()
        except:
            pass
    
    return saved_count

# 创建引擎实例（延迟导入避免循环依赖）
engine = None
_engine_lock = threading.Lock()

def get_engine():
    """获取引擎实例（单例，线程安全）"""
    global engine, _engine_lock
    
    # 双重检查锁定模式，确保线程安全
    if engine is None:
        with _engine_lock:
            # 再次检查，防止多线程同时初始化
            if engine is None:
                try:
                    app.logger.info("开始初始化引擎...")
                    from engine import CrawlerEngine
                    app.logger.info("CrawlerEngine 导入成功")
                    engine = CrawlerEngine()
                    app.logger.info("CrawlerEngine 实例创建成功")
                    # 初始化引擎（加载组件等）
                    engine.initialize()
                    app.logger.info("引擎初始化成功")
                except ImportError as e:
                    error_msg = f"引擎初始化失败：缺少依赖模块 - {str(e)}"
                    app.logger.error(error_msg)
                    app.logger.error("请运行以下命令安装依赖：")
                    app.logger.error("  pip install -r requirements.txt")
                    app.logger.error("  pip install -r backend/requirements.txt")
                    import traceback
                    app.logger.error(traceback.format_exc())
                    engine = None  # 确保设置为 None
                    return None
                except Exception as e:
                    error_msg = f"引擎初始化失败: {str(e)}"
                    app.logger.error(error_msg)
                    import traceback
                    app.logger.error(traceback.format_exc())
                    engine = None  # 确保设置为 None
                    return None
    
    if engine is None:
        app.logger.error("引擎实例为 None，初始化可能失败")
    
    return engine

def get_db_connection():
    """获取数据库连接"""
    password = MYSQL_CONFIG.get('password', '')
    # 如果密码为空，使用Docker容器的默认密码
    if not password:
        password = 'root123456'
    
    return pymysql.connect(
        host=MYSQL_CONFIG.get('host', 'localhost'),
        port=MYSQL_CONFIG.get('port', 3308),
        db=MYSQL_CONFIG.get('db', 'scrapy_db'),
        user=MYSQL_CONFIG.get('user', 'root'),
        password=password,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        # 尝试获取引擎状态（如果引擎未初始化也不报错）
        engine_status = None
        try:
            engine = get_engine()
            engine_status = engine.get_status()
        except:
            engine_status = {'message': 'Engine not initialized'}
        
        return jsonify({
            'status': 'ok',
            'database': 'connected',
            'engine_status': engine_status
        })
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        app.logger.error(f"健康检查失败: {error_msg}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'database': 'disconnected'
        }), 500

@app.route('/api/tasks/cleanup-stuck', methods=['POST'])
def cleanup_stuck_tasks():
    """清理卡在running状态的任务（服务重启后调用）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查找所有running状态且超过10分钟未更新的任务
        cursor.execute("""
            SELECT task_id, started_at, updated_at 
            FROM crawl_tasks 
            WHERE status = 'running' 
            AND (updated_at < DATE_SUB(NOW(), INTERVAL 10 MINUTE) 
                 OR started_at < DATE_SUB(NOW(), INTERVAL 10 MINUTE))
        """)
        stuck_tasks = cursor.fetchall()
        
        cleaned_count = 0
        for task in stuck_tasks:
            task_id = task['task_id']
            
            # 检查是否有数据
            cursor.execute("SELECT COUNT(*) as count FROM crawl_data WHERE task_id = %s", (task_id,))
            data_count = cursor.fetchone()['count']
            
            if data_count > 0:
                # 有数据，更新为completed
                cursor.execute("""
                    UPDATE crawl_tasks 
                    SET status = 'completed', items_count = %s, completed_at = NOW(), updated_at = NOW()
                    WHERE task_id = %s
                """, (data_count, task_id))
                app.logger.info(f"清理卡住的任务 {task_id}，更新为completed（数据条数: {data_count}）")
            else:
                # 没有数据，更新为failed
                cursor.execute("""
                    UPDATE crawl_tasks 
                    SET status = 'failed', completed_at = NOW(), updated_at = NOW()
                    WHERE task_id = %s
                """, (task_id,))
                app.logger.info(f"清理卡住的任务 {task_id}，更新为failed（无数据）")
            
            cleaned_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'cleaned_count': cleaned_count,
                'stuck_tasks': [t['task_id'] for t in stuck_tasks]
            }
        })
    except Exception as e:
        import traceback
        app.logger.error(f"清理卡住任务失败: {e}\n{traceback.format_exc()}")
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status', '').strip()
        keyword = request.args.get('keyword', '').strip()
        
        where_clauses = []
        params = []
        
        if status:
            where_clauses.append("status = %s")
            params.append(status)
        
        if keyword:
            where_clauses.append("(task_name LIKE %s OR task_id LIKE %s)")
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) as total FROM crawl_tasks WHERE {where_sql}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']
        
        # 查询数据
        offset = (page - 1) * per_page
        sql = f"""
            SELECT * FROM crawl_tasks 
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(sql, params + [per_page, offset])
        tasks = cursor.fetchall()
        
        # 转换JSON字段和日期格式
        for task in tasks:
            if task.get('task_config'):
                try:
                    task['task_config'] = json.loads(task['task_config']) if isinstance(task['task_config'], str) else task['task_config']
                except:
                    pass
            for key in ['started_at', 'completed_at', 'created_at', 'updated_at']:
                if task.get(key) and isinstance(task[key], datetime):
                    task[key] = task[key].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': tasks,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = "SELECT * FROM crawl_tasks WHERE task_id = %s"
        cursor.execute(sql, (task_id,))
        task = cursor.fetchone()
        
        # 获取最新的进度日志
        cursor.execute("""
            SELECT stage, message, created_at 
            FROM task_logs 
            WHERE task_id = %s AND level = 'INFO' 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (task_id,))
        latest_log = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if task:
            # 转换JSON字段和日期格式
            if task.get('task_config'):
                try:
                    task['task_config'] = json.loads(task['task_config']) if isinstance(task['task_config'], str) else task['task_config']
                except:
                    pass
            for key in ['started_at', 'completed_at', 'created_at', 'updated_at']:
                if task.get(key) and isinstance(task[key], datetime):
                    task[key] = task[key].isoformat()
            
            # 添加最新进度信息
            if latest_log:
                task['latest_progress'] = {
                    'stage': latest_log.get('stage'),
                    'message': latest_log.get('message'),
                    'updated_at': latest_log.get('created_at').isoformat() if isinstance(latest_log.get('created_at'), datetime) else latest_log.get('created_at')
                }
            
            return jsonify({'code': 200, 'message': 'success', 'data': task})
        else:
            return jsonify({'code': 404, 'message': 'Task not found', 'data': None}), 404
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/tasks/<task_id>/progress', methods=['GET'])
def get_task_progress(task_id):
    """获取任务实时进度"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取任务基本信息
        cursor.execute("SELECT * FROM crawl_tasks WHERE task_id = %s", (task_id,))
        task = cursor.fetchone()
        
        if not task:
            cursor.close()
            conn.close()
            return jsonify({'code': 404, 'message': 'Task not found', 'data': None}), 404
        
        # 获取最新的进度日志
        cursor.execute("""
            SELECT stage, message, created_at 
            FROM task_logs 
            WHERE task_id = %s AND level = 'INFO' 
            ORDER BY created_at DESC 
            LIMIT 10
        """, (task_id,))
        progress_logs = cursor.fetchall()
        
        # 解析最新日志中的进度信息
        current_stage = None
        progress_percentage = 0
        latest_message = None
        
        if progress_logs:
            latest_log = progress_logs[0]
            latest_message = latest_log.get('message', '')
            current_stage = latest_log.get('stage', '')
            
            # 尝试从消息中提取进度百分比
            import re
            progress_match = re.search(r'进度:\s*(\d+)%', latest_message)
            if progress_match:
                progress_percentage = int(progress_match.group(1))
        
        cursor.close()
        conn.close()
        
        # 转换日期格式
        for log in progress_logs:
            if log.get('created_at') and isinstance(log['created_at'], datetime):
                log['created_at'] = log['created_at'].isoformat()
        
        progress_data = {
            'task_id': task_id,
            'status': task.get('status'),
            'current_stage': current_stage,
            'progress_percentage': progress_percentage,
            'items_count': task.get('items_count', 0),
            'errors_count': task.get('errors_count', 0),
            'latest_message': latest_message,
            'progress_logs': progress_logs[:5],  # 返回最近5条进度日志
            'started_at': task.get('started_at').isoformat() if isinstance(task.get('started_at'), datetime) else task.get('started_at'),
            'updated_at': task.get('updated_at').isoformat() if isinstance(task.get('updated_at'), datetime) else task.get('updated_at')
        }
        
        return jsonify({'code': 200, 'message': 'success', 'data': progress_data})
    except Exception as e:
        import traceback
        app.logger.error(f"获取任务进度失败: {e}\n{traceback.format_exc()}")
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/tasks/<task_id>/data', methods=['GET'])
def get_task_data(task_id):
    """获取任务数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 查询总数
        cursor.execute("SELECT COUNT(*) as total FROM crawl_data WHERE task_id = %s", (task_id,))
        total = cursor.fetchone()['total']
        
        # 查询数据
        offset = (page - 1) * per_page
        sql = """
            SELECT * FROM crawl_data 
            WHERE task_id = %s
            ORDER BY extracted_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(sql, (task_id, per_page, offset))
        data = cursor.fetchall()
        
        # 转换JSON字段和日期格式
        for item in data:
            if item.get('metadata'):
                try:
                    item['metadata'] = json.loads(item['metadata']) if isinstance(item['metadata'], str) else item['metadata']
                except:
                    pass
            for key in ['extracted_at', 'created_at', 'updated_at']:
                if item.get(key) and isinstance(item[key], datetime):
                    item[key] = item[key].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': data,
                'total': total,
                'page': page,
                'per_page': per_page
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/tasks/<task_id>/retry', methods=['POST'])
def retry_task(task_id):
    """重试任务"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取任务配置
        sql = "SELECT task_config, task_name FROM crawl_tasks WHERE task_id = %s"
        cursor.execute(sql, (task_id,))
        task = cursor.fetchone()
        
        if not task:
            cursor.close()
            conn.close()
            return jsonify({'code': 404, 'message': 'Task not found', 'data': None}), 404
        
        task_config = task['task_config']
        if isinstance(task_config, str):
            task_config = json.loads(task_config)
        
        task_name = task['task_name']
        cursor.close()
        conn.close()
        
        # 重置任务状态
        conn = get_db_connection()
        cursor = conn.cursor()
        update_sql = """
            UPDATE crawl_tasks 
            SET status = %s, started_at = NULL, completed_at = NULL, 
                items_count = 0, errors_count = 0, updated_at = %s
            WHERE task_id = %s
        """
        cursor.execute(update_sql, ('pending', datetime.now(), task_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        # 更新任务状态为running
        conn = get_db_connection()
        cursor = conn.cursor()
        update_sql = """
            UPDATE crawl_tasks 
            SET status = %s, started_at = %s
            WHERE task_id = %s
        """
        cursor.execute(update_sql, ('running', datetime.now(), task_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        # 异步执行任务（复用创建任务的逻辑）
        import threading
        
        def run_task_thread():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def run_task_async():
                    try:
                        app.logger.info(f"开始执行任务 {task_id}")
                        engine = get_engine()
                        
                        if engine is None:
                            error_msg = (
                                "引擎未初始化。\n"
                                "可能的原因：\n"
                                "1. 缺少依赖模块（如 jieba），请运行：pip install -r requirements.txt\n"
                                "2. 组件导入失败，请检查日志查看详细错误信息\n"
                                "3. 请查看后端日志获取详细错误信息"
                            )
                            app.logger.error(error_msg)
                            app.logger.error("引擎实例为 None，请检查上方的初始化日志")
                            raise Exception(error_msg)
                        
                        app.logger.info(f"引擎获取成功，开始执行任务 {task_id}")
                        
                        # 确保task_config包含task_id
                        task_config['id'] = task_id
                        
                        # 定义进度更新回调函数
                        def update_task_progress(progress_task_id: str, progress_data: Dict[str, Any]):
                            """更新任务进度到数据库"""
                            try:
                                conn = get_db_connection()
                                cursor = conn.cursor()
                                
                                # 更新任务进度信息
                                update_sql = """
                                    UPDATE crawl_tasks 
                                    SET items_count = %s, errors_count = %s, updated_at = %s
                                    WHERE task_id = %s
                                """
                                cursor.execute(update_sql, (
                                    progress_data.get('items_count', 0),
                                    progress_data.get('errors_count', 0),
                                    datetime.now(),
                                    progress_task_id
                                ))
                                
                                # 记录进度日志（避免重复记录相同阶段）
                                insert_log_sql = """
                                    INSERT INTO task_logs (task_id, stage, level, message)
                                    VALUES (%s, %s, %s, %s)
                                """
                                stage = progress_data.get('stage', 'unknown')
                                status = progress_data.get('status', 'running')
                                items_count = progress_data.get('items_count', 0)
                                errors_count = progress_data.get('errors_count', 0)
                                progress_pct = progress_data.get('progress_percentage', 0)
                                latest_title = progress_data.get('latest_title', '')
                                
                                message = f"阶段: {stage}, 进度: {progress_pct}%, 数据: {items_count}条, 错误: {errors_count}个"
                                if latest_title:
                                    message += f" | 正在抓取: {latest_title}"
                                if status == 'completed':
                                    message += " [完成]"
                                elif status == 'error':
                                    message += f" [错误: {progress_data.get('error', 'unknown')}]"
                                
                                cursor.execute(insert_log_sql, (
                                    progress_task_id,
                                    stage,
                                    'INFO',
                                    message
                                ))
                                
                                conn.commit()
                                cursor.close()
                                conn.close()
                            except Exception as e:
                                app.logger.warning(f"更新任务进度失败: {e}")
                        
                        # 临时修改引擎的create_pipeline方法以传递进度回调
                        original_create_pipeline = engine.create_pipeline
                        engine.create_pipeline = lambda cfg: original_create_pipeline(cfg, progress_callback=update_task_progress)
                        
                        result = await engine.run_task(task_config)
                        
                        # 恢复原始的create_pipeline方法
                        engine.create_pipeline = original_create_pipeline
                        
                        app.logger.info(f"任务 {task_id} 执行完成")
                        
                        # 保存任务日志到数据库
                        try:
                            conn_logs = get_db_connection()
                            cursor_logs = conn_logs.cursor()
                            
                            # 保存错误日志
                            if result.get('errors'):
                                insert_log_sql = """
                                    INSERT INTO task_logs (task_id, stage, level, message, error_type, error_message)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """
                                for error in result.get('errors', []):
                                    error_msg = str(error.get('error', error))
                                    cursor_logs.execute(insert_log_sql, (
                                        task_id,
                                        error.get('stage', 'unknown'),
                                        'ERROR',
                                        error_msg[:500],
                                        type(error.get('error', Exception())).__name__ if isinstance(error.get('error'), Exception) else 'unknown',
                                        error_msg[:1000]
                                    ))
                            
                            conn_logs.commit()
                            cursor_logs.close()
                            conn_logs.close()
                        except Exception as log_error:
                            app.logger.error(f"保存任务日志失败: {log_error}")
                            import traceback
                            app.logger.error(traceback.format_exc())
                
                        # 保存数据到数据库
                        if result.get('items'):
                            saved_count = save_crawl_items_to_db(task_id, result['items'], task_config)
                            app.logger.info(f"任务 {task_id} 保存了 {saved_count} 条数据")
                        
                        # 更新任务状态为完成
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            update_sql = """
                                UPDATE crawl_tasks 
                                SET status = %s, items_count = %s, errors_count = %s, completed_at = %s, updated_at = %s
                                WHERE task_id = %s
                            """
                            cursor.execute(update_sql, (
                                'completed',
                                result.get('items_count', len(result.get('items', []))),
                                result.get('errors_count', 0),
                                datetime.now(),
                                datetime.now(),
                                task_id
                            ))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            app.logger.info(f"任务 {task_id} 状态已更新为 completed")
                        except Exception as update_error:
                            app.logger.error(f"更新任务状态失败: {update_error}")
                            import traceback
                            app.logger.error(traceback.format_exc())
                    except Exception as e:
                        # 保存错误日志到数据库
                        try:
                            conn_logs = get_db_connection()
                            cursor_logs = conn_logs.cursor()
                            insert_log_sql = """
                                INSERT INTO task_logs (task_id, stage, level, message, error_type, error_message)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """
                            import traceback
                            error_traceback = traceback.format_exc()
                            cursor_logs.execute(insert_log_sql, (
                                task_id,
                                'task_execution',
                                'ERROR',
                                f"任务执行失败: {str(e)}",
                                type(e).__name__,
                                error_traceback[:1000]
                            ))
                            conn_logs.commit()
                            cursor_logs.close()
                            conn_logs.close()
                        except Exception as log_error:
                            app.logger.error(f"保存错误日志失败: {log_error}")
                        
                        # 更新任务状态为失败
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            update_sql = """
                                UPDATE crawl_tasks 
                                SET status = %s, errors_count = %s, completed_at = %s, updated_at = %s
                                WHERE task_id = %s
                            """
                            cursor.execute(update_sql, ('failed', 1, datetime.now(), datetime.now(), task_id))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            app.logger.info(f"任务 {task_id} 状态已更新为 failed")
                        except Exception as update_error:
                            app.logger.error(f"更新任务失败状态失败: {update_error}")
                        
                        app.logger.error(f"任务执行失败: {str(e)}")
                        import traceback
                        app.logger.error(traceback.format_exc())
                    finally:
                        # 确保任务状态被更新（防止异常退出导致状态卡在running）
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            # 检查任务当前状态
                            cursor.execute("SELECT status FROM crawl_tasks WHERE task_id = %s", (task_id,))
                            current_task = cursor.fetchone()
                            
                            if current_task and current_task['status'] == 'running':
                                # 如果仍然是running状态，检查是否有数据
                                cursor.execute("SELECT COUNT(*) as count FROM crawl_data WHERE task_id = %s", (task_id,))
                                data_count = cursor.fetchone()['count']
                                
                                if data_count > 0:
                                    # 有数据，更新为completed
                                    update_sql = """
                                        UPDATE crawl_tasks 
                                        SET status = %s, items_count = %s, completed_at = NOW(), updated_at = NOW()
                                        WHERE task_id = %s
                                    """
                                    cursor.execute(update_sql, ('completed', data_count, task_id))
                                    app.logger.info(f"任务 {task_id} 在finally中更新为completed（数据条数: {data_count}）")
                                else:
                                    # 没有数据，可能是失败或异常退出
                                    update_sql = """
                                        UPDATE crawl_tasks 
                                        SET status = %s, completed_at = NOW(), updated_at = NOW()
                                        WHERE task_id = %s
                                    """
                                    cursor.execute(update_sql, ('failed', task_id))
                                    app.logger.warning(f"任务 {task_id} 在finally中更新为failed（无数据）")
                                
                                conn.commit()
                            cursor.close()
                            conn.close()
                        except Exception as finally_error:
                            app.logger.error(f"finally块中更新任务状态失败: {finally_error}")
                            import traceback
                            app.logger.error(traceback.format_exc())
                
                loop.run_until_complete(run_task_async())
                loop.close()
            except Exception as e:
                app.logger.error(f"任务线程执行失败: {str(e)}")
                import traceback
                app.logger.error(traceback.format_exc())
        
        # 启动后台线程执行任务
        thread = threading.Thread(target=run_task_thread, daemon=True)
        thread.start()
        
        return jsonify({
            'code': 200,
            'message': 'Task retry started',
            'data': {'task_id': task_id}
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查任务是否存在
        check_sql = "SELECT status FROM crawl_tasks WHERE task_id = %s"
        cursor.execute(check_sql, (task_id,))
        task = cursor.fetchone()
        
        if not task:
            cursor.close()
            conn.close()
            return jsonify({'code': 404, 'message': 'Task not found', 'data': None}), 404
        
        # 如果任务正在运行，不允许删除
        if task['status'] == 'running':
            cursor.close()
            conn.close()
            return jsonify({'code': 400, 'message': 'Cannot delete running task', 'data': None}), 400
        
        # 删除任务的执行日志（保留抓取的文章数据）
        delete_logs_sql = "DELETE FROM task_logs WHERE task_id = %s"
        cursor.execute(delete_logs_sql, (task_id,))
        deleted_logs_count = cursor.rowcount
        
        # 删除任务
        delete_sql = "DELETE FROM crawl_tasks WHERE task_id = %s"
        cursor.execute(delete_sql, (task_id,))
        conn.commit()
        
        app.logger.info(f"删除任务 {task_id}，同时删除了 {deleted_logs_count} 条执行日志（保留抓取的文章数据）")
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'Task deleted successfully',
            'data': {'task_id': task_id}
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/tasks/all', methods=['DELETE'])
def delete_all_tasks():
    """一键删除所有任务（不包括运行中的任务）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 先查询总数（不包括运行中的任务）
        cursor.execute("SELECT COUNT(*) as total FROM crawl_tasks WHERE status != 'running'")
        total = cursor.fetchone()['total']
        
        if total == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'code': 200,
                'message': '没有可删除的任务（运行中的任务不会被删除）',
                'data': {'deleted_count': 0, 'skipped_running': 0}
            })
        
        # 查询运行中的任务数量
        cursor.execute("SELECT COUNT(*) as count FROM crawl_tasks WHERE status = 'running'")
        running_count = cursor.fetchone()['count']
        
        # 获取所有要删除的任务ID
        cursor.execute("SELECT task_id FROM crawl_tasks WHERE status != 'running'")
        task_ids = [row['task_id'] for row in cursor.fetchall()]
        
        # 删除所有非运行中任务的执行日志（保留抓取的文章数据）
        if task_ids:
            placeholders = ','.join(['%s'] * len(task_ids))
            delete_logs_sql = f"DELETE FROM task_logs WHERE task_id IN ({placeholders})"
            cursor.execute(delete_logs_sql, task_ids)
            deleted_logs_count = cursor.rowcount
        else:
            deleted_logs_count = 0
        
        # 删除所有非运行中的任务
        cursor.execute("DELETE FROM crawl_tasks WHERE status != 'running'")
        deleted_count = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        app.logger.warning(f"一键删除所有任务: {deleted_count} 条任务，{deleted_logs_count} 条执行日志（跳过 {running_count} 个运行中的任务，保留抓取的文章数据）")
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'deleted_count': deleted_count,
                'deleted_logs_count': deleted_logs_count,
                'skipped_running': running_count
            }
        })
    except Exception as e:
        import traceback
        app.logger.error(f"一键删除所有任务失败: {e}\n{traceback.format_exc()}")
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """编辑任务配置"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查任务是否存在
        check_sql = "SELECT status, task_config FROM crawl_tasks WHERE task_id = %s"
        cursor.execute(check_sql, (task_id,))
        task = cursor.fetchone()
        
        if not task:
            cursor.close()
            conn.close()
            return jsonify({'code': 404, 'message': 'Task not found', 'data': None}), 404
        
        # 如果任务正在运行，不允许编辑
        if task['status'] == 'running':
            cursor.close()
            conn.close()
            return jsonify({'code': 400, 'message': 'Cannot edit running task', 'data': None}), 400
        
        # 获取更新的配置
        update_data = request.json
        if not update_data:
            cursor.close()
            conn.close()
            return jsonify({'code': 400, 'message': 'Update data is required', 'data': None}), 400
        
        # 合并配置
        old_config = task['task_config']
        if isinstance(old_config, str):
            old_config = json.loads(old_config)
        
        # 更新任务配置
        new_config = {**old_config, **update_data}
        
        # 更新任务名称（如果提供）
        task_name = update_data.get('name', task.get('task_name', 'Unnamed Task'))
        
        # 更新数据库
        update_sql = """
            UPDATE crawl_tasks 
            SET task_config = %s, task_name = %s, updated_at = %s
            WHERE task_id = %s
        """
        cursor.execute(update_sql, (
            json.dumps(new_config),
            task_name,
            datetime.now(),
            task_id
        ))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'Task updated successfully',
            'data': {
                'task_id': task_id,
                'task_config': new_config
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/tasks/<task_id>/logs', methods=['GET'])
def get_task_logs(task_id):
    """获取任务日志"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        level = request.args.get('level', '')
        stage = request.args.get('stage', '')
        limit = int(request.args.get('limit', 100))
        
        where_clauses = ["task_id = %s"]
        params = [task_id]
        
        if level:
            where_clauses.append("level = %s")
            params.append(level)
        
        if stage:
            where_clauses.append("stage = %s")
            params.append(stage)
        
        where_sql = " AND ".join(where_clauses)
        
        sql = f"""
            SELECT * FROM task_logs 
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT %s
        """
        cursor.execute(sql, params + [limit])
        logs = cursor.fetchall()
        
        # 转换日期格式
        for log in logs:
            if log.get('created_at') and isinstance(log['created_at'], datetime):
                log['created_at'] = log['created_at'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({'code': 200, 'message': 'success', 'data': logs})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/crawl', methods=['POST'])
def start_crawl():
    """启动爬取任务（兼容接口）"""
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'code': 400, 'message': 'URL不能为空', 'data': None}), 400
        
        # 创建任务配置
        task_config = {
            'id': f"crawl_{int(datetime.now().timestamp())}",
            'name': f'爬取任务: {url}',
            'source': {
                'type': 'http',
                'urls': [url]
            },
            'parser': {
                'type': 'html'
            },
            'extractor': {
                'type': 'css',
                'fields': {
                    'container': 'body',
                    'fields': {
                        'title': {'selector': 'title', 'attr': 'text'},
                        'content': {'selector': 'body', 'attr': 'text'}
                    }
                }
            },
            'transformer': {
                'pipeline': [{'type': 'data'}]
            },
            'output': {
                'type': 'database',
                'output_type': 'mysql'
            }
        }
        
        # 调用创建任务接口
        return create_task_internal(task_config)
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

def create_task_internal(task_config):
    """内部创建任务函数"""
    try:
        task_id = task_config.get('id') or f"task_{int(datetime.now().timestamp())}"
        task_name = task_config.get('name', 'Unnamed Task')
        
        # 保存任务到数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_sql = """
            INSERT INTO crawl_tasks (task_id, task_name, task_config, status, started_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (
            task_id,
            task_name,
            json.dumps(task_config),
            'running',
            datetime.now()
        ))
        conn.commit()
        cursor.close()
        conn.close()
        
        # 异步执行任务
        async def run_task_async():
            try:
                engine = get_engine()
                if not engine:
                    raise Exception("引擎未初始化，请检查日志查看详细错误信息")
                
                # 引擎已经在 get_engine() 中初始化了，直接使用即可
                result = await engine.run_task(task_config)
                
                # 保存数据到数据库
                if result.get('items'):
                    saved_count = save_crawl_items_to_db(task_id, result['items'], task_config)
                    app.logger.info(f"任务 {task_id} 保存了 {saved_count} 条数据")
                
                # 更新任务状态
                conn = get_db_connection()
                cursor = conn.cursor()
                update_sql = """
                    UPDATE crawl_tasks 
                    SET status = %s, items_count = %s, errors_count = %s, completed_at = %s
                    WHERE task_id = %s
                """
                cursor.execute(update_sql, (
                    'completed',
                    result.get('items_count', 0),
                    result.get('errors_count', 0),
                    datetime.now(),
                    task_id
                ))
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                # 更新任务状态为失败
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    update_sql = """
                        UPDATE crawl_tasks 
                        SET status = %s, errors_count = %s, completed_at = %s, updated_at = %s
                        WHERE task_id = %s
                    """
                    cursor.execute(update_sql, ('failed', 1, datetime.now(), datetime.now(), task_id))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    app.logger.info(f"任务 {task_id} 状态已更新为 failed")
                except Exception as update_error:
                    app.logger.error(f"更新任务失败状态失败: {update_error}")
            finally:
                    # 确保任务状态被更新（防止异常退出导致状态卡在running）
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        # 检查任务当前状态
                        cursor.execute("SELECT status FROM crawl_tasks WHERE task_id = %s", (task_id,))
                        current_task = cursor.fetchone()
                        
                        if current_task and current_task['status'] == 'running':
                            # 如果仍然是running状态，检查是否有数据
                            cursor.execute("SELECT COUNT(*) as count FROM crawl_data WHERE task_id = %s", (task_id,))
                            data_count = cursor.fetchone()['count']
                            
                            if data_count > 0:
                                # 有数据，更新为completed
                                update_sql = """
                                    UPDATE crawl_tasks 
                                    SET status = %s, items_count = %s, completed_at = %s, updated_at = %s
                                    WHERE task_id = %s
                                """
                                cursor.execute(update_sql, ('completed', data_count, datetime.now(), datetime.now(), task_id))
                                app.logger.info(f"任务 {task_id} 在finally中更新为completed（数据条数: {data_count}）")
                            else:
                                # 没有数据，可能是失败或异常退出
                                update_sql = """
                                    UPDATE crawl_tasks 
                                    SET status = %s, completed_at = %s, updated_at = %s
                                    WHERE task_id = %s
                                """
                                cursor.execute(update_sql, ('failed', datetime.now(), datetime.now(), task_id))
                                app.logger.warning(f"任务 {task_id} 在finally中更新为failed（无数据）")
                        
                        conn.commit()
                        cursor.close()
                        conn.close()
                    except Exception as finally_error:
                        app.logger.error(f"finally块中更新任务状态失败: {finally_error}")
        
        # 启动异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(run_task_async())
        
        return jsonify({
            'code': 200,
            'message': 'Task created and started',
            'data': {'task_id': task_id}
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """创建并启动抓取任务"""
    try:
        task_config = request.json
        
        if not task_config:
            return jsonify({'code': 400, 'message': 'Task config is required', 'data': None}), 400
        
        # 处理AI筛选描述
        ai_filter_description = task_config.get('ai_filter_description', '').strip()
        if ai_filter_description:
            # 获取AI服务实例（用于筛选器）
            try:
                from ai_recommender.service import get_ai_service
                ai_service = get_ai_service()
            except Exception as e:
                app.logger.warning(f"获取AI服务失败，AI筛选将使用降级方案: {e}")
                ai_service = None
            
            # 添加筛选器配置
            task_config['filter'] = {
                'enabled': True,
                'type': 'ai',
                'filter_description': ai_filter_description,
                'ai_service': ai_service  # 传递AI服务实例
            }
        else:
            # 如果没有AI筛选描述，禁用筛选
            task_config['filter'] = {
                'enabled': False
            }
        
        task_id = task_config.get('id') or f"task_{int(datetime.now().timestamp())}"
        task_name = task_config.get('name', 'Unnamed Task')
        
        # 保存任务到数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_sql = """
            INSERT INTO crawl_tasks (task_id, task_name, task_config, status, started_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (
            task_id,
            task_name,
            json.dumps(task_config),
            'pending',  # 初始状态为pending，执行时改为running
            None  # 开始时started_at为空
        ))
        conn.commit()
        cursor.close()
        conn.close()
        
        # 更新任务状态为running
        conn = get_db_connection()
        cursor = conn.cursor()
        update_sql = """
            UPDATE crawl_tasks 
            SET status = %s, started_at = %s
            WHERE task_id = %s
        """
        cursor.execute(update_sql, ('running', datetime.now(), task_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        # 异步执行任务（使用线程池避免阻塞）
        import threading
        
        def run_task_thread():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def run_task_async():
                    try:
                        app.logger.info(f"开始执行任务 {task_id}")
                        engine = get_engine()
                        
                        if engine is None:
                            error_msg = (
                                "引擎未初始化。\n"
                                "可能的原因：\n"
                                "1. 缺少依赖模块（如 jieba），请运行：pip install -r requirements.txt\n"
                                "2. 组件导入失败，请检查日志查看详细错误信息\n"
                                "3. 请查看后端日志获取详细错误信息"
                            )
                            app.logger.error(error_msg)
                            app.logger.error("引擎实例为 None，请检查上方的初始化日志")
                            raise Exception(error_msg)
                        
                        app.logger.info(f"引擎获取成功，开始执行任务 {task_id}")
                        result = await engine.run_task(task_config)
                        app.logger.info(f"任务 {task_id} 执行完成")
                        
                        # 保存任务日志到数据库
                        try:
                            conn_logs = get_db_connection()
                            cursor_logs = conn_logs.cursor()
                            
                            # 保存错误日志
                            if result.get('errors'):
                                insert_log_sql = """
                                    INSERT INTO task_logs (task_id, stage, level, message, error_type, error_message)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """
                                for error in result.get('errors', []):
                                    error_msg = str(error.get('error', error))
                                    cursor_logs.execute(insert_log_sql, (
                                        task_id,
                                        error.get('stage', 'unknown'),
                                        'ERROR',
                                        error_msg[:500],
                                        type(error.get('error', Exception())).__name__ if isinstance(error.get('error'), Exception) else 'unknown',
                                        error_msg[:1000]
                                    ))
                            
                            conn_logs.commit()
                            cursor_logs.close()
                            conn_logs.close()
                        except Exception as log_error:
                            app.logger.error(f"保存任务日志失败: {log_error}")
                            import traceback
                            app.logger.error(traceback.format_exc())
                
                        # 保存数据到数据库
                        if result.get('items'):
                            saved_count = save_crawl_items_to_db(task_id, result['items'], task_config)
                            app.logger.info(f"任务 {task_id} 保存了 {saved_count} 条数据")
                        
                        # 更新任务状态为完成
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            update_sql = """
                                UPDATE crawl_tasks 
                                SET status = %s, items_count = %s, errors_count = %s, completed_at = %s, updated_at = %s
                                WHERE task_id = %s
                            """
                            cursor.execute(update_sql, (
                                'completed',
                                result.get('items_count', len(result.get('items', []))),
                                result.get('errors_count', 0),
                                datetime.now(),
                                datetime.now(),
                                task_id
                            ))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            app.logger.info(f"任务 {task_id} 状态已更新为 completed")
                        except Exception as update_error:
                            app.logger.error(f"更新任务状态失败: {update_error}")
                            import traceback
                            app.logger.error(traceback.format_exc())
                    except Exception as e:
                        # 保存错误日志到数据库
                        try:
                            conn_logs = get_db_connection()
                            cursor_logs = conn_logs.cursor()
                            insert_log_sql = """
                                INSERT INTO task_logs (task_id, stage, level, message, error_type, error_message)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """
                            import traceback
                            error_traceback = traceback.format_exc()
                            cursor_logs.execute(insert_log_sql, (
                                task_id,
                                'task_execution',
                                'ERROR',
                                f"任务执行失败: {str(e)}",
                                type(e).__name__,
                                error_traceback[:1000]
                            ))
                            conn_logs.commit()
                            cursor_logs.close()
                            conn_logs.close()
                        except Exception as log_error:
                            app.logger.error(f"保存错误日志失败: {log_error}")
                        
                        # 更新任务状态为失败
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            update_sql = """
                                UPDATE crawl_tasks 
                                SET status = %s, errors_count = %s, completed_at = %s, updated_at = %s
                                WHERE task_id = %s
                            """
                            cursor.execute(update_sql, ('failed', 1, datetime.now(), datetime.now(), task_id))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            app.logger.info(f"任务 {task_id} 状态已更新为 failed")
                        except Exception as update_error:
                            app.logger.error(f"更新任务失败状态失败: {update_error}")
                        
                        app.logger.error(f"任务执行失败: {str(e)}")
                        import traceback
                        app.logger.error(traceback.format_exc())
                    finally:
                        # 确保任务状态被更新（防止异常退出导致状态卡在running）
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            # 检查任务当前状态
                            cursor.execute("SELECT status FROM crawl_tasks WHERE task_id = %s", (task_id,))
                            current_task = cursor.fetchone()
                            
                            if current_task and current_task['status'] == 'running':
                                # 如果仍然是running状态，检查是否有数据
                                cursor.execute("SELECT COUNT(*) as count FROM crawl_data WHERE task_id = %s", (task_id,))
                                data_count = cursor.fetchone()['count']
                                
                                if data_count > 0:
                                    # 有数据，更新为completed
                                    update_sql = """
                                        UPDATE crawl_tasks 
                                        SET status = %s, items_count = %s, completed_at = NOW(), updated_at = NOW()
                                        WHERE task_id = %s
                                    """
                                    cursor.execute(update_sql, ('completed', data_count, task_id))
                                    app.logger.info(f"任务 {task_id} 在finally中更新为completed（数据条数: {data_count}）")
                                else:
                                    # 没有数据，可能是失败或异常退出
                                    update_sql = """
                                        UPDATE crawl_tasks 
                                        SET status = %s, completed_at = NOW(), updated_at = NOW()
                                        WHERE task_id = %s
                                    """
                                    cursor.execute(update_sql, ('failed', task_id))
                                    app.logger.warning(f"任务 {task_id} 在finally中更新为failed（无数据）")
                                
                                conn.commit()
                            cursor.close()
                            conn.close()
                        except Exception as finally_error:
                            app.logger.error(f"finally块中更新任务状态失败: {finally_error}")
                            import traceback
                            app.logger.error(traceback.format_exc())
                
                loop.run_until_complete(run_task_async())
                loop.close()
            except Exception as e:
                app.logger.error(f"任务线程执行失败: {str(e)}")
                import traceback
                app.logger.error(traceback.format_exc())
        
        # 启动后台线程执行任务
        thread = threading.Thread(target=run_task_thread, daemon=True)
        thread.start()
        
        return jsonify({
            'code': 200,
            'message': 'Task created and started',
            'data': {
                'task_id': task_id,
                'task_name': task_name
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/extractor/analyze', methods=['POST'])
def analyze_extractor():
    """分析网页并推荐最适合的提取器类型"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'code': 400, 'message': 'URL参数必填', 'data': None}), 400
        
        # 获取网页内容（使用同步requests库）
        import requests
        
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=default_headers, timeout=10)
        response.raise_for_status()
        html_content = response.text
        
        # 分析网页
        from utils.extractor_analyzer import ExtractorAnalyzer
        analyzer = ExtractorAnalyzer()
        result = analyzer.analyze(html_content, url)
        
        return jsonify({
            'code': 200,
            'message': '分析成功',
            'data': result
        })
    except requests.exceptions.RequestException as e:
        app.logger.error(f"获取网页失败: {e}")
        return jsonify({'code': 500, 'message': f'获取网页失败: {str(e)}', 'data': None}), 500
    except Exception as e:
        import traceback
        app.logger.error(f"分析提取器失败: {e}\n{traceback.format_exc()}")
        return jsonify({'code': 500, 'message': f'分析失败: {str(e)}', 'data': None}), 500

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """获取所有文章列表（文章管理接口）"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        keyword = request.args.get('keyword', '').strip()
        data_type = request.args.get('data_type', '').strip()
        task_id = request.args.get('task_id', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        
        # 构建查询条件
        where_clauses = []
        params = []
        
        if keyword:
            where_clauses.append("(title LIKE %s OR content LIKE %s)")
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        if data_type:
            where_clauses.append("data_type = %s")
            params.append(data_type)
        
        if task_id:
            where_clauses.append("task_id = %s")
            params.append(task_id)
        
        if start_date:
            where_clauses.append("DATE(extracted_at) >= %s")
            params.append(start_date)
        
        if end_date:
            where_clauses.append("DATE(extracted_at) <= %s")
            params.append(end_date)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) as total FROM crawl_data WHERE {where_sql}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']
        
        # 查询数据
        offset = (page - 1) * per_page
        query_sql = f"""
            SELECT 
                id,
                task_id,
                source_url,
                data_type,
                title,
                content,
                metadata,
                extracted_at,
                created_at,
                updated_at
            FROM crawl_data 
            WHERE {where_sql}
            ORDER BY extracted_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query_sql, params + [per_page, offset])
        articles = cursor.fetchall()
        
        # 处理数据格式
        for article in articles:
            # 解析metadata
            if article.get('metadata'):
                try:
                    if isinstance(article['metadata'], str):
                        article['metadata'] = json.loads(article['metadata']) if article['metadata'].strip() else {}
                    elif not isinstance(article['metadata'], dict):
                        article['metadata'] = {}
                except:
                    article['metadata'] = {}
            else:
                article['metadata'] = {}
            
            # 转换日期格式
            for key in ['extracted_at', 'created_at', 'updated_at']:
                if article.get(key) and isinstance(article[key], datetime):
                    article[key] = article[key].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': articles,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page if per_page > 0 else 0
            }
        })
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        app.logger.error(f"获取文章列表失败: {error_msg}")
        if conn:
            conn.close()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/articles/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    """删除文章"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查文章是否存在
        cursor.execute("SELECT id FROM crawl_data WHERE id = %s", (article_id,))
        article = cursor.fetchone()
        
        if not article:
            cursor.close()
            conn.close()
            return jsonify({'code': 404, 'message': 'Article not found', 'data': None}), 404
        
        # 删除文章
        cursor.execute("DELETE FROM crawl_data WHERE id = %s", (article_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        app.logger.info(f"删除文章成功: {article_id}")
        return jsonify({'code': 200, 'message': 'success', 'data': None})
    except Exception as e:
        import traceback
        app.logger.error(f"删除文章失败: {e}\n{traceback.format_exc()}")
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/articles/batch-delete', methods=['POST'])
def batch_delete_articles():
    """批量删除文章"""
    try:
        data = request.json
        ids = data.get('ids', [])
        
        if not ids or not isinstance(ids, list):
            return jsonify({'code': 400, 'message': '文章ID列表不能为空', 'data': None}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 批量删除
        placeholders = ','.join(['%s'] * len(ids))
        delete_sql = f"DELETE FROM crawl_data WHERE id IN ({placeholders})"
        cursor.execute(delete_sql, ids)
        deleted_count = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        app.logger.info(f"批量删除文章成功: {deleted_count} 条")
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {'deleted_count': deleted_count}
        })
    except Exception as e:
        import traceback
        app.logger.error(f"批量删除文章失败: {e}\n{traceback.format_exc()}")
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/articles/all', methods=['DELETE'])
def delete_all_articles():
    """一键删除所有文章"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 先查询总数
        cursor.execute("SELECT COUNT(*) as total FROM crawl_data")
        total = cursor.fetchone()['total']
        
        if total == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'code': 200,
                'message': '没有可删除的文章',
                'data': {'deleted_count': 0}
            })
        
        # 删除所有文章
        cursor.execute("DELETE FROM crawl_data")
        deleted_count = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        app.logger.warning(f"一键删除所有文章: {deleted_count} 条")
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {'deleted_count': deleted_count}
        })
    except Exception as e:
        import traceback
        app.logger.error(f"一键删除所有文章失败: {e}\n{traceback.format_exc()}")
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/websites', methods=['GET'])
def get_websites():
    """获取网站列表（兼容接口，从crawl_data表查询）"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查表是否存在，如果不存在则返回空列表
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'crawl_data'
        """)
        table_exists = cursor.fetchone()['count'] > 0
        
        if not table_exists:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'list': [],
                    'total': 0,
                    'page': 1,
                    'page_size': 10,
                    'total_pages': 0
                }
            })
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        keyword = request.args.get('keyword', '').strip()
        domain = request.args.get('domain', '').strip()
        
        # 构建查询条件
        where_clauses = []
        params = []
        
        if keyword:
            where_clauses.append("(title LIKE %s OR content LIKE %s)")
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        if domain:
            where_clauses.append("source_url LIKE %s")
            params.append(f'%{domain}%')
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) as total FROM crawl_data WHERE {where_sql}"
        cursor.execute(count_sql, params)
        total_result = cursor.fetchone()
        total = total_result['total'] if total_result else 0
        
        # 查询数据 - 简化查询，避免JSON_EXTRACT可能的问题
        offset = (page - 1) * page_size
        query_sql = f"""
            SELECT 
                id,
                source_url as url,
                COALESCE(title, '') as title,
                COALESCE(content, '') as content,
                extracted_at as crawl_time,
                created_at,
                COALESCE(metadata, '{{}}') as metadata
            FROM crawl_data 
            WHERE {where_sql}
            ORDER BY extracted_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query_sql, params + [page_size, offset])
        websites = cursor.fetchall()
        
        # 处理数据格式
        from urllib.parse import urlparse
        
        for website in websites:
            # 提取域名
            if website.get('url'):
                try:
                    parsed = urlparse(website['url'])
                    website['domain'] = parsed.netloc or ''
                except:
                    website['domain'] = ''
            else:
                website['domain'] = ''
            
            # 从metadata提取字段
            metadata = {}
            if website.get('metadata'):
                try:
                    if isinstance(website['metadata'], str):
                        if website['metadata'].strip():
                            metadata = json.loads(website['metadata'])
                        else:
                            metadata = {}
                    elif isinstance(website['metadata'], dict):
                        metadata = website['metadata']
                    else:
                        metadata = {}
                except Exception as e:
                    # JSON解析失败，使用空字典
                    metadata = {}
            
            website['description'] = metadata.get('description', '') or ''
            website['keywords'] = metadata.get('keywords', '') or ''
            website['author'] = metadata.get('author', '') or ''
            website['publish_time'] = metadata.get('publish_time', '') or ''
            website['status_code'] = 200
            
            # 转换日期格式
            for key in ['crawl_time', 'created_at']:
                if website.get(key):
                    if isinstance(website[key], datetime):
                        website[key] = website[key].strftime('%Y-%m-%d %H:%M:%S')
                    elif isinstance(website[key], str) and website[key]:
                        try:
                            dt = datetime.fromisoformat(website[key].replace('Z', '+00:00'))
                            website[key] = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass
            
            # publish_time可能是字符串，不需要转换
            if website.get('publish_time') and isinstance(website['publish_time'], datetime):
                website['publish_time'] = website['publish_time'].strftime('%Y-%m-%d %H:%M:%S')
            
            # 移除metadata字段（已提取）
            if 'metadata' in website:
                del website['metadata']
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'list': websites,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
            }
        })
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        app.logger.error(f"获取网站列表失败: {error_msg}")
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/websites/<int:website_id>', methods=['GET'])
def get_website_detail(website_id):
    """获取网站详情（兼容接口）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query_sql = """
            SELECT 
                id,
                source_url as url,
                COALESCE(title, '') as title,
                content,
                extracted_at as crawl_time,
                created_at,
                updated_at,
                metadata
            FROM crawl_data 
            WHERE id = %s
        """
        cursor.execute(query_sql, [website_id])
        website = cursor.fetchone()
        
        if not website:
            return jsonify({'code': 404, 'message': 'Website not found', 'data': None}), 404
        
        # 提取域名
        from urllib.parse import urlparse
        if website.get('url'):
            try:
                parsed = urlparse(website['url'])
                website['domain'] = parsed.netloc or ''
            except:
                website['domain'] = ''
        else:
            website['domain'] = ''
        
        # 从metadata提取字段
        metadata = {}
        if website.get('metadata'):
            try:
                if isinstance(website['metadata'], str):
                    metadata = json.loads(website['metadata'])
                else:
                    metadata = website['metadata']
            except:
                metadata = {}
        
        website['description'] = metadata.get('description', '')
        website['keywords'] = metadata.get('keywords', '')
        website['author'] = metadata.get('author', '')
        website['publish_time'] = metadata.get('publish_time', '')
        website['status_code'] = 200
        
        # 转换日期格式
        for key in ['publish_time', 'crawl_time', 'created_at', 'updated_at']:
            if website.get(key):
                if isinstance(website[key], datetime):
                    website[key] = website[key].strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(website[key], str) and website[key]:
                    try:
                        dt = datetime.fromisoformat(website[key].replace('Z', '+00:00'))
                        website[key] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
        
        # 移除metadata字段
        if 'metadata' in website:
            del website['metadata']
        
        cursor.close()
        conn.close()
        
        return jsonify({'code': 200, 'message': 'success', 'data': website})
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        return jsonify({'code': 500, 'message': error_msg, 'data': None}), 500

@app.route('/api/websites/<int:website_id>', methods=['DELETE'])
def delete_website(website_id):
    """删除网站记录（兼容接口）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        delete_sql = 'DELETE FROM crawl_data WHERE id = %s'
        cursor.execute(delete_sql, [website_id])
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'code': 200, 'message': 'success', 'data': {'id': website_id}})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取统计信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 任务统计
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM crawl_tasks 
            GROUP BY status
        """)
        task_stats = cursor.fetchall()
        
        # 数据统计（兼容旧接口）
        cursor.execute("SELECT COUNT(*) as total FROM crawl_data")
        total_data = cursor.fetchone()['total']
        
        # 按域名统计（兼容旧接口）
        cursor.execute("""
            SELECT 
                SUBSTRING_INDEX(SUBSTRING_INDEX(source_url, '/', 3), '//', -1) as domain,
                COUNT(*) as count 
            FROM crawl_data 
            GROUP BY domain
            ORDER BY count DESC 
            LIMIT 10
        """)
        domain_stats = cursor.fetchall()
        
        # 按日期统计（最近7天，兼容旧接口）
        cursor.execute("""
            SELECT DATE(extracted_at) as date, COUNT(*) as count 
            FROM crawl_data 
            WHERE extracted_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(extracted_at)
            ORDER BY date DESC
        """)
        date_stats = cursor.fetchall()
        
        # 转换日期格式
        for stat in date_stats:
            if stat.get('date') and isinstance(stat['date'], datetime):
                stat['date'] = stat['date'].strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT data_type, COUNT(*) as count 
            FROM crawl_data 
            GROUP BY data_type
        """)
        data_type_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total': total_data,
                'domain_stats': domain_stats,
                'date_stats': date_stats,
                'task_stats': task_stats,
                'data_type_stats': data_type_stats
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

# AI推荐服务（延迟初始化）
ai_service = None

def get_ai_service():
    """获取AI推荐服务实例（单例）"""
    global ai_service
    if ai_service is None:
        try:
            app.logger.info("开始初始化AI推荐服务...")
            from ai_recommender.service import AIRecommendationService
            app.logger.info("AIRecommendationService 导入成功")
            ai_config = config.get('ai_recommender', {})
            ai_service = AIRecommendationService(ai_config)
            app.logger.info("AI推荐服务初始化成功")
        except ImportError as e:
            error_msg = f"AI推荐服务初始化失败：缺少依赖模块 - {str(e)}"
            app.logger.error(error_msg)
            app.logger.error("请运行以下命令安装依赖：")
            app.logger.error("  pip install langchain langchain-openai langchain-community openai pydantic")
            import traceback
            app.logger.error(traceback.format_exc())
            ai_service = None
            return None
        except Exception as e:
            error_msg = f"AI推荐服务初始化失败: {str(e)}"
            app.logger.error(error_msg)
            import traceback
            app.logger.error(traceback.format_exc())
            ai_service = None
            return None
    
    if ai_service is None:
        app.logger.warning("AI推荐服务实例为 None，初始化可能失败。将使用降级方案。")
    
    return ai_service

@app.route('/api/ai/recommend/topics', methods=['POST'])
def recommend_topics():
    """AI主题推荐"""
    try:
        data = request.json
        articles = data.get('articles', [])
        num_topics = data.get('num_topics', 5)
        
        if not articles:
            return jsonify({'code': 400, 'message': '文章列表不能为空', 'data': None}), 400
        
        service = get_ai_service()
        if not service:
            # 如果AI服务未初始化，返回默认主题推荐
            app.logger.warning("AI推荐服务未初始化，使用默认主题推荐")
            return jsonify({
                'code': 200,
                'message': 'success (使用默认主题推荐)',
                'data': _get_default_topic_recommendations(articles, num_topics)
            })
        
        result = service.get_topic_recommendations(articles, num_topics)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        app.logger.error(f"主题推荐失败: {error_msg}")
        
        # 尝试返回默认主题推荐作为降级方案
        try:
            return jsonify({
                'code': 200,
                'message': 'success (使用默认主题推荐)',
                'data': _get_default_topic_recommendations(articles if 'articles' in locals() else [], num_topics if 'num_topics' in locals() else 5)
            })
        except:
            return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

def _get_default_topic_recommendations(articles: list, num_topics: int = 5) -> dict:
    """
    默认主题推荐（当AI服务不可用时使用）
    
    Args:
        articles: 文章列表
        num_topics: 推荐主题数量
        
    Returns:
        推荐结果
    """
    # 从文章标题和内容中提取关键词作为主题
    topics = []
    
    # 常见主题关键词
    common_topics = [
        '人工智能', '机器学习', '深度学习', '自然语言处理', '计算机视觉',
        '数据科学', '大数据', '云计算', '区块链', '物联网',
        '网络安全', '移动开发', 'Web开发', 'DevOps', '微服务',
        '前端技术', '后端开发', '数据库', '算法', '编程语言'
    ]
    
    # 如果文章数量较少，返回通用主题
    if len(articles) < 3:
        topics = [{'topic': topic, 'score': 0.8, 'articles_count': 0} for topic in common_topics[:num_topics]]
    else:
        # 尝试从文章标题中提取主题
        titles = [article.get('title', '') for article in articles if article.get('title')]
        for topic in common_topics[:num_topics]:
            count = sum(1 for title in titles if topic in title)
            if count > 0:
                topics.append({
                    'topic': topic,
                    'score': min(0.9, 0.5 + count * 0.1),
                    'articles_count': count
                })
        
        # 如果提取的主题不够，补充通用主题
        while len(topics) < num_topics:
            for topic in common_topics:
                if not any(t['topic'] == topic for t in topics):
                    topics.append({
                        'topic': topic,
                        'score': 0.6,
                        'articles_count': 0
                    })
                    if len(topics) >= num_topics:
                        break
    
    return {
        'topics': topics[:num_topics],
        'total_articles': len(articles),
        'method': 'default'
    }

@app.route('/api/ai/analyze/article', methods=['POST'])
def analyze_article():
    """分析文章细节"""
    try:
        data = request.json
        article = data.get('article')
        
        if not article:
            return jsonify({'code': 400, 'message': '文章数据不能为空', 'data': None}), 400
        
        service = get_ai_service()
        if not service:
            # 如果AI服务未初始化，返回默认文章分析
            app.logger.warning("AI推荐服务未初始化，使用默认文章分析")
            return jsonify({
                'code': 200,
                'message': 'success (使用默认文章分析)',
                'data': _get_default_article_analysis(article)
            })
        
        result = service.analyze_article(article)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        app.logger.error(f"文章分析失败: {error_msg}")
        
        # 尝试返回默认文章分析作为降级方案
        try:
            return jsonify({
                'code': 200,
                'message': 'success (使用默认文章分析)',
                'data': _get_default_article_analysis(article if 'article' in locals() and article else {})
            })
        except:
            return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

def _get_default_article_analysis(article: dict) -> dict:
    """
    默认文章分析（当AI服务不可用时使用）
    
    Args:
        article: 文章数据
        
    Returns:
        分析结果
    """
    title = article.get('title', '无标题')
    content = article.get('content', '')
    article_id = article.get('id') or article.get('url', '')
    
    # 基础统计
    words = content.split() if content else []
    word_count = len(words)
    char_count = len(content)
    
    # 估算阅读时间（假设每分钟200字）
    read_time = max(1, word_count // 200)
    
    # 估算复杂度
    if word_count < 300:
        complexity = 'simple'
    elif word_count < 1000:
        complexity = 'medium'
    else:
        complexity = 'complex'
    
    # 简单摘要（取前200字符）
    summary = content[:200] + '...' if len(content) > 200 else content
    
    # 提取关键要点（简单分词，取前5个）
    key_points = []
    if content:
        # 简单的句子分割
        sentences = content.split('。')[:5]
        key_points = [s.strip() + '。' for s in sentences if s.strip()][:5]
    
    # 简单情感分析（基于关键词）
    positive_words = ['好', '优秀', '成功', '进步', '发展', '提升', '改善', '创新', '突破']
    negative_words = ['问题', '困难', '失败', '下降', '风险', '危机', '担忧']
    
    positive_count = sum(1 for word in positive_words if word in content)
    negative_count = sum(1 for word in negative_words if word in content)
    
    if positive_count > negative_count:
        sentiment = 'positive'
    elif negative_count > positive_count:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    
    # 提取标签（基于常见关键词）
    tags = []
    common_tags = [
        '人工智能', 'AI', '机器学习', '深度学习', '自然语言处理', '计算机视觉',
        '数据科学', '大数据', '云计算', '区块链', '物联网', '网络安全',
        '前端', '后端', '移动开发', 'Web开发', '算法', '编程'
    ]
    
    content_lower = content.lower()
    for tag in common_tags:
        if tag.lower() in content_lower or tag in title:
            tags.append(tag)
            if len(tags) >= 5:
                break
    
    # 提取实体（简化版，基于关键词匹配）
    entities = {
        'companies': [],
        'technologies': tags[:3],
        'persons': []
    }
    
    return {
        'article_id': article_id,
        'summary': summary or '暂无摘要',
        'key_points': key_points or ['暂无关键要点'],
        'sentiment': sentiment,
        'entities': entities,
        'tags': tags[:5] if tags else ['未分类'],
        'analysis': {
            'word_count': word_count,
            'char_count': char_count,
            'read_time': read_time,
            'complexity': complexity
        },
        'method': 'default'
    }

@app.route('/api/ai/select/topics', methods=['POST'])
def select_topics():
    """手动选择主题"""
    try:
        data = request.json
        user_id = data.get('user_id', 'anonymous')
        topics = data.get('topics', [])
        articles = data.get('articles', [])
        
        if not topics:
            return jsonify({'code': 400, 'message': '主题列表不能为空', 'data': None}), 400
        
        service = get_ai_service()
        if not service:
            return jsonify({'code': 500, 'message': 'AI推荐服务未初始化', 'data': None}), 500
        
        result = service.manual_select_topics(user_id, topics, articles)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/ai/select/articles', methods=['POST'])
def select_articles():
    """手动选择文章"""
    try:
        data = request.json
        user_id = data.get('user_id', 'anonymous')
        article_ids = data.get('article_ids', [])
        reason = data.get('reason')
        
        if not article_ids:
            return jsonify({'code': 400, 'message': '文章ID列表不能为空', 'data': None}), 400
        
        service = get_ai_service()
        if not service:
            return jsonify({'code': 500, 'message': 'AI推荐服务未初始化', 'data': None}), 500
        
        result = service.manual_select_articles(user_id, article_ids, reason)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/ai/selections/<user_id>', methods=['GET'])
def get_user_selections(user_id):
    """获取用户选择记录"""
    try:
        service = get_ai_service()
        if not service:
            return jsonify({'code': 500, 'message': 'AI推荐服务未初始化', 'data': None}), 500
        
        result = service.get_user_selections(user_id)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/ai/recommend/pipeline', methods=['POST'])
def get_recommendation_pipeline():
    """获取完整推荐流程结果"""
    try:
        data = request.json
        articles = data.get('articles', [])
        user_id = data.get('user_id')
        
        if not articles:
            return jsonify({'code': 400, 'message': '文章列表不能为空', 'data': None}), 400
        
        service = get_ai_service()
        if not service:
            return jsonify({'code': 500, 'message': 'AI推荐服务未初始化', 'data': None}), 500
        
        result = service.get_recommendation_pipeline(articles, user_id)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        app.logger.error(f"推荐流程失败: {error_msg}")
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500

@app.route('/api/ai/recommend/sites', methods=['POST'])
def recommend_sites():
    """AI推荐网站（基于主题）"""
    try:
        data = request.json
        topic = data.get('topic', '').strip()
        
        if not topic:
            return jsonify({'code': 400, 'message': '主题不能为空', 'data': None}), 400
        
        service = get_ai_service()
        if not service:
            # 如果AI服务未初始化，返回默认网站列表
            app.logger.warning("AI推荐服务未初始化，使用默认网站列表")
            from ai_recommender.service import AIRecommendationService
            temp_service = AIRecommendationService({})
            result = temp_service._get_default_sites_for_topic(topic, 10)
            return jsonify({
                'code': 200,
                'message': 'success (使用默认网站列表)',
                'data': {
                    'sites': result.get('sites', []),
                    'topic': topic,
                    'count': len(result.get('sites', []))
                }
            })
        
        result = service.recommend_sites_for_topic(topic)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        app.logger.error(f"网站推荐失败: {error_msg}")
        
        # 尝试返回默认网站列表作为降级方案
        try:
            from ai_recommender.service import AIRecommendationService
            temp_service = AIRecommendationService({})
            result = temp_service._get_default_sites_for_topic(topic, 10)
            app.logger.info("使用默认网站列表作为降级方案")
            return jsonify({
                'code': 200,
                'message': 'success (使用默认网站列表)',
                'data': {
                    'sites': result.get('sites', []),
                    'topic': topic,
                    'count': len(result.get('sites', []))
                }
            })
        except Exception as fallback_error:
            app.logger.error(f"降级方案也失败: {fallback_error}")
            return jsonify({
                'code': 500,
                'message': f'网站推荐失败: {str(e)}',
                'data': None
            }), 500

def cleanup_stuck_tasks_on_startup():
    """服务启动时清理卡在running状态的任务"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查找所有running状态且超过10分钟未更新的任务
        cursor.execute("""
            SELECT task_id, started_at, updated_at 
            FROM crawl_tasks 
            WHERE status = 'running' 
            AND (updated_at < DATE_SUB(NOW(), INTERVAL 10 MINUTE) 
                 OR started_at < DATE_SUB(NOW(), INTERVAL 10 MINUTE)
                 OR updated_at IS NULL)
        """)
        stuck_tasks = cursor.fetchall()
        
        cleaned_count = 0
        for task in stuck_tasks:
            task_id = task['task_id']
            
            # 检查是否有数据
            cursor.execute("SELECT COUNT(*) as count FROM crawl_data WHERE task_id = %s", (task_id,))
            data_count = cursor.fetchone()['count']
            
            if data_count > 0:
                # 有数据，更新为completed
                cursor.execute("""
                    UPDATE crawl_tasks 
                    SET status = 'completed', items_count = %s, completed_at = NOW(), updated_at = NOW()
                    WHERE task_id = %s
                """, (data_count, task_id))
                app.logger.info(f"启动时清理卡住的任务 {task_id}，更新为completed（数据条数: {data_count}）")
            else:
                # 没有数据，更新为failed
                cursor.execute("""
                    UPDATE crawl_tasks 
                    SET status = 'failed', completed_at = NOW(), updated_at = NOW()
                    WHERE task_id = %s
                """, (task_id,))
                app.logger.info(f"启动时清理卡住的任务 {task_id}，更新为failed（无数据）")
            
            cleaned_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if cleaned_count > 0:
            app.logger.info(f"服务启动时清理了 {cleaned_count} 个卡住的任务")
    except Exception as e:
        app.logger.warning(f"清理卡住任务失败: {e}")
        import traceback
        app.logger.warning(traceback.format_exc())

if __name__ == '__main__':
    # 服务启动时清理卡住的任务
    cleanup_stuck_tasks_on_startup()
    
    host = BACKEND_CONFIG.get('host', '0.0.0.0')
    port = BACKEND_CONFIG.get('port', 6000)
    debug = BACKEND_CONFIG.get('debug', False)
    
    app.logger.info(f"启动后端服务: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
