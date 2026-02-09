#!/usr/bin/env python3
"""
后端服务测试脚本
用于诊断后端启动问题
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("=" * 50)
print("后端服务诊断")
print("=" * 50)
print()

# 1. 检查 Python 版本
print("1. 检查 Python 版本...")
print(f"   Python 版本: {sys.version}")
print()

# 2. 检查必要的模块
print("2. 检查 Python 模块...")
modules = ['flask', 'flask_cors', 'pymysql', 'json', 'datetime']
missing_modules = []

for module in modules:
    try:
        __import__(module)
        print(f"   ✓ {module}")
    except ImportError:
        print(f"   ✗ {module} - 未安装")
        missing_modules.append(module)

if missing_modules:
    print(f"\n   缺少模块: {', '.join(missing_modules)}")
    print("   安装命令: pip install " + " ".join(missing_modules))
print()

# 3. 检查配置文件
print("3. 检查配置文件...")
config_file = os.path.join(os.path.dirname(__file__), '..', 'config.json')
if os.path.exists(config_file):
    print(f"   ✓ config.json 存在")
    try:
        import json
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"   ✓ config.json 格式正确")
        print(f"   数据库配置: {config.get('database', {}).get('host', 'N/A')}:{config.get('database', {}).get('port', 'N/A')}")
    except Exception as e:
        print(f"   ✗ config.json 解析失败: {e}")
else:
    print(f"   ✗ config.json 不存在")
print()

# 4. 检查 utils 模块
print("4. 检查 utils 模块...")
utils_dir = os.path.join(os.path.dirname(__file__), '..', 'utils')
if os.path.exists(utils_dir):
    print(f"   ✓ utils 目录存在")
    config_loader = os.path.join(utils_dir, 'config_loader.py')
    if os.path.exists(config_loader):
        print(f"   ✓ config_loader.py 存在")
        try:
            from utils.config_loader import config
            print(f"   ✓ 配置加载器导入成功")
            db_config = config.get_database_config()
            print(f"   数据库配置: {db_config.get('host')}:{db_config.get('port')}")
        except Exception as e:
            print(f"   ✗ 配置加载器导入失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"   ✗ config_loader.py 不存在")
else:
    print(f"   ✗ utils 目录不存在")
print()

# 5. 测试数据库连接
print("5. 测试数据库连接...")
try:
    import pymysql
    from utils.config_loader import config
    
    db_config = config.get_database_config()
    print(f"   尝试连接: {db_config.get('host')}:{db_config.get('port')}")
    
    conn = pymysql.connect(
        host=db_config.get('host', 'localhost'),
        port=db_config.get('port', 3308),
        user=db_config.get('user', 'root'),
        password=db_config.get('password', ''),
        charset=db_config.get('charset', 'utf8mb4')
    )
    print("   ✓ 数据库连接成功")
    conn.close()
except Exception as e:
    print(f"   ✗ 数据库连接失败: {e}")
print()

# 6. 测试导入 app
print("6. 测试导入 app.py...")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
    import app
    print("   ✓ app.py 导入成功")
except Exception as e:
    print(f"   ✗ app.py 导入失败: {e}")
    import traceback
    traceback.print_exc()
print()

print("=" * 50)
print("诊断完成")
print("=" * 50)
