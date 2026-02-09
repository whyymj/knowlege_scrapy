#!/usr/bin/env python3
"""
系统诊断脚本
检查配置、数据库连接等
"""
import sys
import os
import pymysql

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.config_loader import config

def check_config():
    """检查配置"""
    print("=" * 60)
    print("1. 检查配置文件")
    print("=" * 60)
    
    db_config = config.get_database_config()
    
    print(f"数据库配置:")
    print(f"  主机: {db_config.get('host')}")
    print(f"  端口: {db_config.get('port')}")
    print(f"  用户: {db_config.get('user')}")
    password = db_config.get('password', '')
    if password:
        print(f"  密码: {'*' * len(password)} (已配置)")
    else:
        print(f"  密码: (空) ⚠ 将使用默认密码 root123456")
    
    print(f"  数据库: {db_config.get('db')}")
    
    return db_config

def check_database_connection(db_config):
    """检查数据库连接"""
    print("\n" + "=" * 60)
    print("2. 检查数据库连接")
    print("=" * 60)
    
    password = db_config.get('password', '')
    if not password:
        password = 'root123456'
        print("⚠ 配置中密码为空，使用默认密码: root123456")
    
    try:
        conn = pymysql.connect(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 3308),
            user=db_config.get('user', 'root'),
            password=password,
            charset='utf8mb4',
            connect_timeout=5
        )
        
        print("✓ 数据库连接成功")
        
        # 检查数据库是否存在
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES LIKE %s", (db_config.get('db', 'scrapy_db'),))
        db_exists = cursor.fetchone()
        
        if db_exists:
            print(f"✓ 数据库 {db_config.get('db')} 存在")
            
            # 切换到数据库
            cursor.execute(f"USE {db_config.get('db')}")
            
            # 检查表
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['crawl_tasks', 'crawl_data', 'task_logs', 'task_metrics']
            
            print(f"\n数据库表:")
            for table in expected_tables:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  ✓ {table} ({count} 条记录)")
                else:
                    print(f"  ✗ {table} (不存在)")
            
            cursor.close()
        else:
            print(f"✗ 数据库 {db_config.get('db')} 不存在")
            print("  请运行: python3 scripts/init_database.py")
        
        conn.close()
        return True
        
    except pymysql.Error as e:
        print(f"✗ 数据库连接失败: {e}")
        print("\n可能的原因:")
        print("  1. MySQL服务未启动")
        print("  2. 密码错误")
        print("  3. 端口不正确")
        print("  4. 用户权限不足")
        return False
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_backend_service():
    """检查后端服务"""
    print("\n" + "=" * 60)
    print("3. 检查后端服务")
    print("=" * 60)
    
    try:
        import requests
        response = requests.get("http://localhost:6000/api/health", timeout=2)
        
        if response.status_code == 200:
            print("✓ 后端服务运行正常")
            data = response.json()
            print(f"  响应: {data}")
            return True
        else:
            print(f"⚠ 后端服务返回状态码: {response.status_code}")
            print(f"  响应: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ 后端服务未运行")
        print("  请启动: cd backend && python app.py")
        return False
    except ImportError:
        print("⚠ 无法检查后端服务（requests模块未安装）")
        return None
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return False

def main():
    """主函数"""
    print("系统诊断工具")
    print("=" * 60)
    
    # 检查配置
    db_config = check_config()
    
    # 检查数据库连接
    db_ok = check_database_connection(db_config)
    
    # 检查后端服务
    backend_ok = check_backend_service()
    
    # 总结
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)
    
    if db_ok:
        print("✓ 数据库连接正常")
    else:
        print("✗ 数据库连接失败")
    
    if backend_ok is True:
        print("✓ 后端服务正常")
    elif backend_ok is False:
        print("✗ 后端服务异常")
    else:
        print("? 无法检查后端服务")
    
    if db_ok and backend_ok:
        print("\n✓ 系统状态正常")
        return 0
    else:
        print("\n✗ 系统存在问题，请根据上述信息修复")
        return 1

if __name__ == '__main__':
    sys.exit(main())
