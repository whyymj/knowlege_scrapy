#!/bin/bash

# 初始化数据库脚本
# 用于创建数据库和表结构

set -e

echo "开始初始化数据库..."

# 从配置文件读取数据库配置（如果存在）
if [ -f "config.json" ]; then
    DB_HOST=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('database', {}).get('host', 'localhost'))" 2>/dev/null || echo "localhost")
    DB_PORT=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('database', {}).get('port', 3308))" 2>/dev/null || echo "3308")
    DB_USER=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('database', {}).get('user', 'root'))" 2>/dev/null || echo "root")
    DB_PASSWORD=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('database', {}).get('password', ''))" 2>/dev/null || echo "")
    DB_NAME=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('database', {}).get('db', 'scrapy_db'))" 2>/dev/null || echo "scrapy_db")
else
    DB_HOST="localhost"
    DB_PORT="3308"
    DB_USER="root"
    DB_PASSWORD="root123456"
    DB_NAME="scrapy_db"
fi

echo "数据库配置:"
echo "  主机: $DB_HOST"
echo "  端口: $DB_PORT"
echo "  用户: $DB_USER"
echo "  数据库: $DB_NAME"

# 检查是否使用Docker
if docker ps | grep -q "scrapy_mysql_local"; then
    echo ""
    echo "检测到Docker容器 scrapy_mysql_local，使用Docker方式初始化..."
    
    # 使用Docker exec执行SQL
    if [ -z "$DB_PASSWORD" ]; then
        docker exec -i scrapy_mysql_local mysql -u"$DB_USER" < init_db.sql
    else
        docker exec -i scrapy_mysql_local mysql -u"$DB_USER" -p"$DB_PASSWORD" < init_db.sql
    fi
    
    echo "数据库初始化完成！"
else
    echo ""
    echo "使用本地MySQL客户端初始化..."
    
    # 检查mysql命令是否存在
    if ! command -v mysql &> /dev/null; then
        echo "错误: 未找到mysql命令，请安装MySQL客户端"
        echo "或者使用Docker方式: docker exec -i scrapy_mysql_local mysql -uroot -proot123456 < init_db.sql"
        exit 1
    fi
    
    # 使用本地mysql客户端
    if [ -z "$DB_PASSWORD" ]; then
        mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" < init_db.sql
    else
        mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" < init_db.sql
    fi
    
    echo "数据库初始化完成！"
fi

echo ""
echo "验证数据库表..."
if docker ps | grep -q "scrapy_mysql_local"; then
    if [ -z "$DB_PASSWORD" ]; then
        docker exec scrapy_mysql_local mysql -u"$DB_USER" -e "USE $DB_NAME; SHOW TABLES;"
    else
        docker exec scrapy_mysql_local mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME; SHOW TABLES;"
    fi
else
    if [ -z "$DB_PASSWORD" ]; then
        mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -e "USE $DB_NAME; SHOW TABLES;"
    else
        mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME; SHOW TABLES;"
    fi
fi

echo ""
echo "数据库初始化成功！"
