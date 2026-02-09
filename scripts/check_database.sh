#!/bin/bash

# 检查数据库连接和表结构

set -e

echo "检查数据库连接和表结构..."

# 从配置文件读取数据库配置
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
echo ""

# 检查Docker容器
if docker ps | grep -q "scrapy_mysql_local"; then
    echo "✓ Docker容器 scrapy_mysql_local 正在运行"
    
    # 检查数据库连接
    echo ""
    echo "检查数据库连接..."
    if [ -z "$DB_PASSWORD" ]; then
        docker exec scrapy_mysql_local mysql -u"$DB_USER" -e "SELECT 1;" > /dev/null 2>&1
    else
        docker exec scrapy_mysql_local mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" > /dev/null 2>&1
    fi
    
    if [ $? -eq 0 ]; then
        echo "✓ 数据库连接成功"
    else
        echo "✗ 数据库连接失败"
        exit 1
    fi
    
    # 检查数据库是否存在
    echo ""
    echo "检查数据库 $DB_NAME..."
    if [ -z "$DB_PASSWORD" ]; then
        DB_EXISTS=$(docker exec scrapy_mysql_local mysql -u"$DB_USER" -e "SHOW DATABASES LIKE '$DB_NAME';" 2>/dev/null | grep -c "$DB_NAME" || echo "0")
    else
        DB_EXISTS=$(docker exec scrapy_mysql_local mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "SHOW DATABASES LIKE '$DB_NAME';" 2>/dev/null | grep -c "$DB_NAME" || echo "0")
    fi
    
    if [ "$DB_EXISTS" -gt 0 ]; then
        echo "✓ 数据库 $DB_NAME 存在"
    else
        echo "✗ 数据库 $DB_NAME 不存在，请先运行 init_database.sh"
        exit 1
    fi
    
    # 检查表
    echo ""
    echo "检查数据库表..."
    if [ -z "$DB_PASSWORD" ]; then
        TABLES=$(docker exec scrapy_mysql_local mysql -u"$DB_USER" -e "USE $DB_NAME; SHOW TABLES;" 2>/dev/null | tail -n +2)
    else
        TABLES=$(docker exec scrapy_mysql_local mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME; SHOW TABLES;" 2>/dev/null | tail -n +2)
    fi
    
    if [ -z "$TABLES" ]; then
        echo "✗ 数据库表不存在，请先运行 init_database.sh"
        exit 1
    else
        echo "✓ 数据库表:"
        echo "$TABLES" | while read table; do
            echo "  - $table"
        done
    fi
    
    # 检查 crawl_data 表的数据
    echo ""
    echo "检查 crawl_data 表数据..."
    if [ -z "$DB_PASSWORD" ]; then
        COUNT=$(docker exec scrapy_mysql_local mysql -u"$DB_USER" -e "USE $DB_NAME; SELECT COUNT(*) as count FROM crawl_data;" 2>/dev/null | tail -n 1)
    else
        COUNT=$(docker exec scrapy_mysql_local mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME; SELECT COUNT(*) as count FROM crawl_data;" 2>/dev/null | tail -n 1)
    fi
    
    echo "  crawl_data 表中有 $COUNT 条记录"
    
else
    echo "✗ Docker容器 scrapy_mysql_local 未运行"
    echo "请先启动MySQL容器:"
    echo "  docker start scrapy_mysql_local"
    echo "或使用 dev.sh 脚本启动"
    exit 1
fi

echo ""
echo "数据库检查完成！"
