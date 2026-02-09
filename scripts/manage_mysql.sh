#!/bin/bash

# MySQL Docker 容器管理脚本

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

MYSQL_CONTAINER_NAME="scrapy_mysql_local"
MYSQL_PORT=3308

# 检查 Docker
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker 未运行，请先启动 Docker"
        exit 1
    fi
}

# 创建 MySQL 容器
create_mysql() {
    check_docker
    
    if docker ps -a --format '{{.Names}}' | grep -q "^${MYSQL_CONTAINER_NAME}$"; then
        print_warn "MySQL 容器已存在: ${MYSQL_CONTAINER_NAME}"
        return 1
    fi
    
    print_step "创建 MySQL Docker 容器..."
    
    # 检查 MySQL 镜像是否存在
    print_info "检查 MySQL 镜像..."
    if ! docker images --format '{{.Repository}}:{{.Tag}}' | grep -q '^mysql:8.0$'; then
        print_warn "MySQL 镜像不存在，尝试拉取..."
        print_info "如果网络较慢，可以使用以下命令手动拉取："
        print_info "  docker pull mysql:8.0"
        print_info "或使用国内镜像源："
        print_info "  docker pull registry.cn-hangzhou.aliyuncs.com/acs/mysql:8.0"
        echo ""
        
        # 尝试拉取镜像
        print_info "正在拉取 MySQL 镜像（这可能需要几分钟）..."
        if docker pull mysql:8.0 2>&1; then
            print_info "MySQL 镜像拉取成功"
        else
            print_error "MySQL 镜像拉取失败"
            print_error "可能的原因："
            print_error "  1. 网络连接问题"
            print_error "  2. Docker Hub 访问受限"
            print_error ""
            print_info "解决方案："
            print_info "  1. 检查网络连接"
            print_info "  2. 配置 Docker 镜像加速器"
            print_info "  3. 手动拉取镜像：docker pull mysql:8.0"
            print_info "  4. 或使用国内镜像：docker pull registry.cn-hangzhou.aliyuncs.com/acs/mysql:8.0"
            return 1
        fi
    else
        print_info "MySQL 镜像已存在"
    fi
    
    # 读取配置
    DB_PASSWORD="root123456"
    DB_NAME="scrapy_db"
    DB_USER="scrapy_user"
    DB_USER_PASSWORD="scrapy_pass"
    
    if [ -f "config.json" ] && command -v python3 &> /dev/null; then
        SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
        PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
        cd "$PROJECT_ROOT"
        
        DB_PASSWORD=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('docker', {}).get('mysql', {}).get('root_password', 'root123456'))" 2>/dev/null || echo "root123456")
        DB_NAME=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('database', {}).get('db', 'scrapy_db'))" 2>/dev/null || echo "scrapy_db")
        DB_USER=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('docker', {}).get('mysql', {}).get('user', 'scrapy_user'))" 2>/dev/null || echo "scrapy_user")
        DB_USER_PASSWORD=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('docker', {}).get('mysql', {}).get('password', 'scrapy_pass'))" 2>/dev/null || echo "scrapy_pass")
    fi
    
    print_info "正在创建 MySQL 容器..."
    if docker run -d \
        --name ${MYSQL_CONTAINER_NAME} \
        -p ${MYSQL_PORT}:3306 \
        -e MYSQL_ROOT_PASSWORD=${DB_PASSWORD} \
        -e MYSQL_DATABASE=${DB_NAME} \
        -e MYSQL_USER=${DB_USER} \
        -e MYSQL_PASSWORD=${DB_USER_PASSWORD} \
        -e TZ=Asia/Shanghai \
        --restart unless-stopped \
        mysql:8.0 \
        --character-set-server=utf8mb4 \
        --collation-server=utf8mb4_unicode_ci
    
    if [ $? -eq 0 ]; then
        print_info "MySQL 容器创建成功"
        print_info "等待 MySQL 初始化..."
        
        local retries=0
        while [ $retries -lt 60 ]; do
            if docker exec ${MYSQL_CONTAINER_NAME} mysqladmin ping -h localhost -u root -p${DB_PASSWORD} --silent 2>/dev/null; then
                print_info "MySQL 初始化完成"
                
                # 执行初始化脚本
                if [ -f "init_db.sql" ]; then
                    print_info "执行数据库初始化脚本..."
                    docker exec -i ${MYSQL_CONTAINER_NAME} mysql -u root -p${DB_PASSWORD} < init_db.sql 2>/dev/null || true
                fi
                
                return 0
            fi
            sleep 2
            retries=$((retries + 1))
        done
        
        print_warn "MySQL 启动超时，但容器已创建"
    else
        print_error "MySQL 容器创建失败"
        return 1
    fi
}

# 启动 MySQL 容器
start_mysql() {
    check_docker
    
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${MYSQL_CONTAINER_NAME}$"; then
        print_warn "MySQL 容器不存在，正在创建..."
        create_mysql
        return $?
    fi
    
    if docker ps --format '{{.Names}}' | grep -q "^${MYSQL_CONTAINER_NAME}$"; then
        print_info "MySQL 容器已在运行"
        return 0
    fi
    
    print_step "启动 MySQL 容器..."
    docker start ${MYSQL_CONTAINER_NAME}
    
    if [ $? -eq 0 ]; then
        print_info "MySQL 容器启动成功"
        sleep 3
    else
        print_error "MySQL 容器启动失败"
        return 1
    fi
}

# 停止 MySQL 容器
stop_mysql() {
    check_docker
    
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${MYSQL_CONTAINER_NAME}$"; then
        print_warn "MySQL 容器不存在"
        return 0
    fi
    
    if docker ps --format '{{.Names}}' | grep -q "^${MYSQL_CONTAINER_NAME}$"; then
        print_step "停止 MySQL 容器..."
        docker stop ${MYSQL_CONTAINER_NAME}
        print_info "MySQL 容器已停止"
    else
        print_info "MySQL 容器已停止"
    fi
}

# 删除 MySQL 容器
remove_mysql() {
    check_docker
    
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${MYSQL_CONTAINER_NAME}$"; then
        print_warn "MySQL 容器不存在"
        return 0
    fi
    
    print_warn "这将删除 MySQL 容器及其数据！"
    read -p "确认删除？(y/N): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        if docker ps --format '{{.Names}}' | grep -q "^${MYSQL_CONTAINER_NAME}$"; then
            docker stop ${MYSQL_CONTAINER_NAME}
        fi
        docker rm ${MYSQL_CONTAINER_NAME}
        print_info "MySQL 容器已删除"
    else
        print_info "已取消"
    fi
}

# 查看状态
status_mysql() {
    check_docker
    
    print_info "MySQL 容器状态："
    
    if docker ps -a --format '{{.Names}}' | grep -q "^${MYSQL_CONTAINER_NAME}$"; then
        if docker ps --format '{{.Names}}' | grep -q "^${MYSQL_CONTAINER_NAME}$"; then
            print_info "  状态: 运行中"
            print_info "  容器名: ${MYSQL_CONTAINER_NAME}"
            print_info "  端口: ${MYSQL_PORT}:3306"
            
            # 测试连接
            if docker exec ${MYSQL_CONTAINER_NAME} mysqladmin ping -h localhost -u root -proot123456 --silent 2>/dev/null; then
                print_info "  连接: 正常"
            else
                print_warn "  连接: 异常"
            fi
        else
            print_info "  状态: 已停止"
            print_info "  容器名: ${MYSQL_CONTAINER_NAME}"
        fi
    else
        print_info "  状态: 不存在"
    fi
}

# 主函数
main() {
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
    cd "$PROJECT_ROOT"
    
    case "${1:-}" in
        create)
            create_mysql
            ;;
        start)
            start_mysql
            ;;
        stop)
            stop_mysql
            ;;
        restart)
            stop_mysql
            sleep 2
            start_mysql
            ;;
        remove)
            remove_mysql
            ;;
        status)
            status_mysql
            ;;
        *)
            echo "用法: $0 {create|start|stop|restart|remove|status}"
            echo ""
            echo "命令说明:"
            echo "  create  - 创建 MySQL 容器"
            echo "  start   - 启动 MySQL 容器"
            echo "  stop    - 停止 MySQL 容器"
            echo "  restart - 重启 MySQL 容器"
            echo "  remove  - 删除 MySQL 容器（会删除数据）"
            echo "  status  - 查看 MySQL 容器状态"
            exit 1
            ;;
    esac
}

main "$@"
