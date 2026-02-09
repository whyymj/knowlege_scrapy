#!/bin/bash

# 后端服务检查脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 获取项目根目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

# 读取后端端口
BACKEND_PORT=6000
if [ -f "config.json" ] && command -v python3 &> /dev/null; then
    BACKEND_PORT=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('backend', {}).get('port', 6000))" 2>/dev/null || echo "6000")
fi

print_info "=========================================="
print_info "  后端服务检查"
print_info "=========================================="
echo ""

# 检查端口
print_step "检查端口 $BACKEND_PORT..."
if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_info "端口 $BACKEND_PORT 正在监听"
    PID=$(lsof -ti :$BACKEND_PORT)
    print_info "进程 PID: $PID"
    
    # 获取进程信息
    if [ ! -z "$PID" ]; then
        CMD=$(ps -p $PID -o command= 2>/dev/null || echo "unknown")
        print_info "进程命令: $CMD"
    fi
else
    print_warn "端口 $BACKEND_PORT 未监听"
fi

# 检查进程
print_step "检查后端进程..."
BACKEND_PIDS=$(pgrep -f "python.*app.py" 2>/dev/null || echo "")
if [ ! -z "$BACKEND_PIDS" ]; then
    print_info "找到后端进程:"
    for pid in $BACKEND_PIDS; do
        CMD=$(ps -p $pid -o command= 2>/dev/null || echo "unknown")
        print_info "  PID: $pid - $CMD"
    done
else
    print_warn "未找到后端进程"
fi

# 测试 API
print_step "测试后端 API..."
if curl -s -f "http://localhost:$BACKEND_PORT/api/statistics" > /dev/null 2>&1; then
    print_info "后端 API 响应正常"
    echo ""
    print_info "API 测试结果："
    curl -s "http://localhost:$BACKEND_PORT/api/statistics" | head -20
else
    print_error "后端 API 无响应"
fi

# 查看日志
if [ -f "backend.log" ]; then
    echo ""
    print_step "最近日志（最后 20 行）："
    tail -20 backend.log
else
    print_warn "日志文件不存在: backend.log"
fi

echo ""
print_info "=========================================="
