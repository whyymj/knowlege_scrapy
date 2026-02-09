#!/bin/bash

# 网站爬虫管理系统 - Docker 一键启动脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装，请先安装 $1"
        exit 1
    fi
}

# 主函数
main() {
    print_info "=========================================="
    print_info "  网站爬虫管理系统 - Docker 启动脚本"
    print_info "=========================================="
    echo ""

    # 检查必要的命令
    print_step "检查 Docker 环境..."
    check_command docker
    check_command docker-compose

    # 检查 Docker 是否运行
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker 服务未运行，请先启动 Docker"
        exit 1
    fi

    # 获取脚本所在目录
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"

    # 检查 docker-compose.yml 是否存在
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml 文件不存在"
        exit 1
    fi

    # 询问操作
    echo ""
    print_step "请选择操作："
    echo "  1) 构建并启动所有服务（首次运行）"
    echo "  2) 启动服务（已构建）"
    echo "  3) 停止服务"
    echo "  4) 重启服务"
    echo "  5) 查看日志"
    echo "  6) 清理并重建（删除数据卷）"
    echo ""
    read -p "请输入选项 [1-6]: " choice

    case $choice in
        1)
            print_step "构建并启动所有服务..."
            docker-compose up -d --build
            print_info "等待服务启动..."
            sleep 5
            print_info "查看服务状态..."
            docker-compose ps
            ;;
        2)
            print_step "启动服务..."
            docker-compose up -d
            print_info "查看服务状态..."
            docker-compose ps
            ;;
        3)
            print_step "停止服务..."
            docker-compose down
            print_info "服务已停止"
            ;;
        4)
            print_step "重启服务..."
            docker-compose restart
            print_info "查看服务状态..."
            docker-compose ps
            ;;
        5)
            print_step "查看日志（按 Ctrl+C 退出）..."
            docker-compose logs -f
            ;;
        6)
            print_warn "这将删除所有数据卷，数据将丢失！"
            read -p "确认继续？[y/N]: " confirm
            if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
                print_step "停止并清理服务..."
                docker-compose down -v
                print_step "重建并启动服务..."
                docker-compose up -d --build
                print_info "查看服务状态..."
                docker-compose ps
            else
                print_info "已取消操作"
            fi
            ;;
        *)
            print_error "无效选项"
            exit 1
            ;;
    esac

    echo ""
    print_info "=========================================="
    print_info "  服务信息"
    print_info "=========================================="
    print_info "前端界面: http://localhost:3000"
    print_info "后端 API: http://localhost:5000"
    print_info "MySQL: localhost:3306"
    print_info ""
    print_info "常用命令："
    print_info "  查看日志: docker-compose logs -f"
    print_info "  查看状态: docker-compose ps"
    print_info "  停止服务: docker-compose down"
    print_info "  进入容器: docker exec -it <container_name> bash"
    print_info "=========================================="
}

# 运行主函数
main
