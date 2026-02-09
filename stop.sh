#!/bin/bash

# 网站爬虫管理系统 - 停止脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 停止指定端口的服务
stop_port() {
    local port=$1
    local name=$2
    
    # 查找占用端口的进程
    local pids=$(lsof -ti :$port 2>/dev/null)
    
    if [ -z "$pids" ]; then
        print_warn "$name (端口 $port) 未运行"
        return 0
    fi
    
    # 停止进程
    for pid in $pids; do
        print_info "停止 $name (PID: $pid, 端口: $port)..."
        kill $pid 2>/dev/null
    done
    
    # 等待进程结束
    sleep 1
    
    # 如果还在运行，强制杀死
    pids=$(lsof -ti :$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        for pid in $pids; do
            print_warn "强制停止 $name (PID: $pid)..."
            kill -9 $pid 2>/dev/null
        done
    fi
    
    print_info "$name 已停止"
}

# 停止 MySQL Docker 容器
stop_mysql_container() {
    MYSQL_CONTAINER_NAME="scrapy_mysql_local"
    
    if docker ps --format '{{.Names}}' | grep -q "^${MYSQL_CONTAINER_NAME}$"; then
        print_info "停止 MySQL 容器: ${MYSQL_CONTAINER_NAME}"
        docker stop ${MYSQL_CONTAINER_NAME}
        print_info "MySQL 容器已停止（容器保留，下次启动会自动启动）"
    elif docker ps -a --format '{{.Names}}' | grep -q "^${MYSQL_CONTAINER_NAME}$"; then
        print_info "MySQL 容器已停止"
    else
        print_info "MySQL 容器不存在"
    fi
}

# 主函数
main() {
    print_info "=========================================="
    print_info "  停止网站爬虫管理系统服务"
    print_info "=========================================="
    echo ""
    
    # 停止后端服务（从配置文件读取端口）
    BACKEND_PORT=6000
    if [ -f "config.json" ] && command -v python3 &> /dev/null; then
        BACKEND_PORT=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('backend', {}).get('port', 6000))" 2>/dev/null || echo "6000")
    fi
    stop_port $BACKEND_PORT "后端服务"
    
    # 停止前端服务
    stop_port 3000 "前端服务"
    
    # 询问是否停止 MySQL 容器
    echo ""
    read -p "是否停止 MySQL Docker 容器？(y/N): " stop_mysql
    if [[ $stop_mysql == [yY] || $stop_mysql == [yY][eE][sS] ]]; then
        stop_mysql_container
    else
        print_info "MySQL 容器保持运行"
    fi
    
    echo ""
    print_info "所有服务已停止"
    print_info "=========================================="
}

# 运行主函数
main
