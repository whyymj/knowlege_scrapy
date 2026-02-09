#!/usr/bin/env python3
"""
自动初始化数据库脚本
"""
import sys
import os
import subprocess
import pymysql
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config_loader import config

def get_db_config():
    """获取数据库配置"""
    db_config = config.get_database_config()
    password = db_config.get('password', '')
    # 如果密码为空，使用Docker容器的默认密码
    if not password:
        password = 'root123456'
    
    return {
        'host': db_config.get('host', 'localhost'),
        'port': db_config.get('port', 3308),
        'user': db_config.get('user', 'root'),
        'password': password,
        'database': db_config.get('db', 'scrapy_db')
    }

def check_docker_container():
    """检查Docker容器是否运行"""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=scrapy_mysql_local', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return 'scrapy_mysql_local' in result.stdout
    except:
        return False

def init_via_docker(db_config, sql_file):
    """通过Docker初始化数据库"""
    print("使用Docker方式初始化数据库...")
    
    sql_path = project_root / sql_file
    
    if not sql_path.exists():
        print(f"错误: SQL文件不存在: {sql_path}")
        return False
    
    try:
        # 读取SQL文件
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 尝试使用PyMySQL直接连接（更可靠）
        print("  尝试使用PyMySQL直接连接...")
        return init_via_pymysql(db_config, sql_file)
            
    except Exception as e:
        print(f"✗ Docker执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def init_via_pymysql(db_config, sql_file):
    """通过PyMySQL直接初始化数据库"""
    print("使用PyMySQL方式初始化数据库...")
    
    sql_path = project_root / sql_file
    
    if not sql_path.exists():
        print(f"错误: SQL文件不存在: {sql_path}")
        return False
    
    try:
        # 读取SQL文件
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 连接数据库（不指定数据库，先创建数据库）
        conn = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 执行SQL语句
        # 分割SQL语句（按分号和换行）
        statements = []
        current_statement = []
        
        for line in sql_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            
            current_statement.append(line)
            
            if line.endswith(';'):
                statement = ' '.join(current_statement)
                if statement:
                    statements.append(statement)
                current_statement = []
        
        # 执行每个SQL语句
        for statement in statements:
            if statement.strip():
                try:
                    cursor.execute(statement)
                    conn.commit()
                except Exception as e:
                    # 忽略"表已存在"等错误
                    if 'already exists' not in str(e).lower() and 'duplicate' not in str(e).lower():
                        print(f"警告: {e}")
        
        cursor.close()
        conn.close()
        
        print("✓ 数据库初始化成功！")
        return True
        
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_tables(db_config):
    """验证表是否创建成功"""
    try:
        conn = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['crawl_tasks', 'crawl_data', 'task_logs', 'task_metrics']
        
        print("\n验证数据库表:")
        for table in expected_tables:
            if table in tables:
                # 检查表记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  ✓ {table} ({count} 条记录)")
            else:
                print(f"  ✗ {table} (不存在)")
        
        cursor.close()
        conn.close()
        
        return all(table in tables for table in expected_tables)
        
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("数据库自动初始化脚本")
    print("=" * 60)
    
    # 获取数据库配置
    db_config = get_db_config()
    
    print(f"\n数据库配置:")
    print(f"  主机: {db_config['host']}")
    print(f"  端口: {db_config['port']}")
    print(f"  用户: {db_config['user']}")
    print(f"  数据库: {db_config['database']}")
    
    # 检查Docker容器
    use_docker = check_docker_container()
    
    if use_docker:
        print("\n✓ 检测到Docker容器 scrapy_mysql_local")
    else:
        print("\n⚠ 未检测到Docker容器，将使用PyMySQL直接连接")
    
    # 初始化数据库
    sql_file = 'init_db.sql'
    print(f"\n开始初始化数据库...")
    print(f"SQL文件: {sql_file}")
    
    if use_docker:
        success = init_via_docker(db_config, sql_file)
    else:
        success = init_via_pymysql(db_config, sql_file)
    
    if success:
        # 验证表
        print("\n" + "=" * 60)
        if verify_tables(db_config):
            print("\n✓ 数据库初始化完成！所有表已创建。")
            return 0
        else:
            print("\n⚠ 数据库初始化完成，但部分表可能未创建。")
            return 1
    else:
        print("\n✗ 数据库初始化失败！")
        return 1

if __name__ == '__main__':
    sys.exit(main())
