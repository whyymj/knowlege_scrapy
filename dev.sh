#!/bin/bash

# 网站爬虫管理系统 - 一键启动脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装，请先安装 $1"
        exit 1
    fi
}

# 检查 MySQL 是否运行
check_mysql() {
    print_info "检查 MySQL 服务..."
    if mysqladmin ping -h localhost -P 3306 -u root --silent 2>/dev/null; then
        print_info "MySQL 服务运行正常"
    else
        print_warn "MySQL 服务可能未运行，请确保 MySQL 已启动（端口 3306）"
    fi
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_warn "端口 $port 已被占用"
        return 1
    fi
    return 0
}

# 清理函数
cleanup() {
    print_info "正在停止服务..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        print_info "后端服务已停止 (PID: $BACKEND_PID)"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        print_info "前端服务已停止 (PID: $FRONTEND_PID)"
    fi
    exit 0
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    print_info "=========================================="
    print_info "  网站爬虫管理系统 - 启动脚本"
    print_info "=========================================="
    echo ""

    # 检查必要的命令
    check_command python3
    check_command npm
    check_command mysql

    # 检查 MySQL
    check_mysql

    # 获取脚本所在目录
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"

    # 检查后端端口
    if ! check_port 5000; then
        print_error "后端端口 5000 已被占用，请先停止占用该端口的服务"
        exit 1
    fi

    # 检查前端端口
    if ! check_port 3000; then
        print_error "前端端口 3000 已被占用，请先停止占用该端口的服务"
        exit 1
    fi

    # 检查 Python 依赖
    print_info "检查 Python 依赖..."
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        print_warn "未检测到虚拟环境，建议创建虚拟环境"
    fi

    # 检查后端依赖
    if [ ! -f "backend/app.py" ]; then
        print_error "后端文件不存在: backend/app.py"
        exit 1
    fi

    # 检查前端依赖
    if [ ! -d "frontend/node_modules" ]; then
        print_warn "前端依赖未安装，正在安装..."
        cd frontend
        npm install
        cd ..
    fi

    # 启动后端服务
    print_info "启动后端服务 (端口 5000)..."
    cd backend
    python3 app.py > ../backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    print_info "后端服务已启动 (PID: $BACKEND_PID)"

    # 等待后端启动
    sleep 2

    # 检查后端是否启动成功
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "后端服务启动失败，请查看 backend.log"
        exit 1
    fi

    # 启动前端服务
    print_info "启动前端服务 (端口 3000)..."
    cd frontend
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    print_info "前端服务已启动 (PID: $FRONTEND_PID)"

    # 等待前端启动
    sleep 3

    # 检查前端是否启动成功
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "前端服务启动失败，请查看 frontend.log"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi

    echo ""
    print_info "=========================================="
    print_info "  服务启动成功！"
    print_info "=========================================="
    print_info "后端 API: http://localhost:5000"
    print_info "前端界面: http://localhost:3000"
    print_info ""
    print_info "日志文件:"
    print_info "  - 后端日志: backend.log"
    print_info "  - 前端日志: frontend.log"
    print_info ""
    print_info "按 Ctrl+C 停止所有服务"
    print_info "=========================================="
    echo ""

    # 等待用户中断
    wait
}

# 运行主函数
main
