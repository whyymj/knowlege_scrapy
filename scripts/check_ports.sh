#!/bin/bash

# 端口检查工具脚本

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

# 检查端口占用
check_port() {
    local port=$1
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        local pids=$(lsof -ti :$port 2>/dev/null)
        print_warn "端口 $port 已被占用"
        
        echo ""
        echo "占用进程信息："
        for pid in $pids; do
            local cmd=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
            local full_cmd=$(ps -p $pid -o command= 2>/dev/null || echo "unknown")
            echo "  PID: $pid"
            echo "  命令: $cmd"
            echo "  完整命令: $full_cmd"
            echo ""
        done
        
        return 1
    else
        print_info "端口 $port 可用"
        return 0
    fi
}

# 停止占用端口的进程
stop_port() {
    local port=$1
    
    if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_info "端口 $port 未被占用"
        return 0
    fi
    
    local pids=$(lsof -ti :$port 2>/dev/null)
    
    print_warn "端口 $port 被以下进程占用："
    for pid in $pids; do
        local cmd=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
        echo "  PID: $pid ($cmd)"
    done
    
    echo ""
    read -p "是否停止这些进程？(y/N): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        for pid in $pids; do
            print_info "停止进程 PID: $pid"
            kill $pid 2>/dev/null
            sleep 1
            
            # 如果还在运行，强制杀死
            if kill -0 $pid 2>/dev/null; then
                print_warn "强制停止进程 PID: $pid"
                kill -9 $pid 2>/dev/null
            fi
        done
        
        sleep 1
        
        # 验证端口是否已释放
        if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_info "端口 $port 已释放"
            return 0
        else
            print_error "端口 $port 仍被占用"
            return 1
        fi
    else
        print_info "已取消操作"
        return 1
    fi
}

# 主函数
main() {
    echo "=========================================="
    echo "  端口检查工具"
    echo "=========================================="
    echo ""
    
    # 检查常用端口
    print_step "检查项目常用端口..."
    echo ""
    
    check_port 3308
    check_port 6000
    check_port 3000
    
    echo ""
    echo "=========================================="
    echo "  操作选项"
    echo "=========================================="
    echo ""
    echo "1. 检查端口 3308 (MySQL)"
    echo "2. 检查端口 6000 (后端)"
    echo "3. 检查端口 3000 (前端)"
    echo "4. 停止端口 6000 的进程"
    echo "5. 停止端口 3000 的进程"
    echo "6. 停止端口 3308 的进程"
    echo "0. 退出"
    echo ""
    
    read -p "请选择操作 [0-6]: " choice
    
    case $choice in
        1)
            check_port 3308
            ;;
        2)
            check_port 6000
            ;;
        3)
            check_port 3000
            ;;
        4)
            stop_port 6000
            ;;
        5)
            stop_port 3000
            ;;
        6)
            stop_port 3308
            ;;
        0)
            echo "退出"
            exit 0
            ;;
        *)
            print_error "无效选项"
            exit 1
            ;;
    esac
}

# 如果直接运行脚本
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
