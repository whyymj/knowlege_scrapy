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

# 主函数
main() {
    print_info "=========================================="
    print_info "  停止网站爬虫管理系统服务"
    print_info "=========================================="
    echo ""
    
    # 停止后端服务
    stop_port 5000 "后端服务"
    
    # 停止前端服务
    stop_port 3000 "前端服务"
    
    echo ""
    print_info "所有服务已停止"
    print_info "=========================================="
}

# 运行主函数
main
