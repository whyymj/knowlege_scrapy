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

# 检查并启动 MySQL Docker 容器
check_and_start_mysql() {
    print_info "检查 MySQL Docker 容器..."
    
    # 检查 Docker 是否运行
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker 未运行，请先启动 Docker"
        exit 1
    fi
    
    MYSQL_CONTAINER_NAME="scrapy_mysql_local"
    MYSQL_PORT=3308
    
    # 检查容器是否存在
    if docker ps -a --format '{{.Names}}' | grep -q "^${MYSQL_CONTAINER_NAME}$"; then
        print_info "MySQL 容器已存在: ${MYSQL_CONTAINER_NAME}"
        
        # 检查容器是否运行
        if docker ps --format '{{.Names}}' | grep -q "^${MYSQL_CONTAINER_NAME}$"; then
            print_info "MySQL 容器正在运行"
        else
            print_info "启动 MySQL 容器..."
            docker start ${MYSQL_CONTAINER_NAME}
            
            # 等待 MySQL 启动
            print_info "等待 MySQL 启动..."
            sleep 5
            
            # 检查是否启动成功
            local retries=0
            while [ $retries -lt 30 ]; do
                if docker exec ${MYSQL_CONTAINER_NAME} mysqladmin ping -h localhost -u root -proot123456 --silent 2>/dev/null; then
                    print_info "MySQL 容器启动成功"
                    return 0
                fi
                sleep 1
                retries=$((retries + 1))
            done
            
            print_warn "MySQL 容器启动中，可能需要更多时间..."
        fi
    else
        print_info "创建 MySQL Docker 容器..."
        
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
            if docker pull mysql:8.0 2>&1 | tee /tmp/docker_pull.log; then
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
                exit 1
            fi
        else
            print_info "MySQL 镜像已存在"
        fi
        
        # 从 config.json 读取数据库配置
        DB_PASSWORD="root123456"
        DB_NAME="scrapy_db"
        DB_USER="scrapy_user"
        DB_USER_PASSWORD="scrapy_pass"
        
        # 尝试从 config.json 读取配置
        if [ -f "config.json" ]; then
            if command -v python3 &> /dev/null; then
                DB_PASSWORD=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('docker', {}).get('mysql', {}).get('root_password', 'root123456'))" 2>/dev/null || echo "root123456")
                DB_NAME=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('database', {}).get('db', 'scrapy_db'))" 2>/dev/null || echo "scrapy_db")
                DB_USER=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('docker', {}).get('mysql', {}).get('user', 'scrapy_user'))" 2>/dev/null || echo "scrapy_user")
                DB_USER_PASSWORD=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('docker', {}).get('mysql', {}).get('password', 'scrapy_pass'))" 2>/dev/null || echo "scrapy_pass")
            fi
        fi
        
        # 创建 MySQL 容器
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
            --collation-server=utf8mb4_unicode_ci 2>&1; then
            print_info "MySQL 容器创建成功"
            print_info "等待 MySQL 初始化..."
            
            # 等待 MySQL 启动
            local retries=0
            while [ $retries -lt 60 ]; do
                if docker exec ${MYSQL_CONTAINER_NAME} mysqladmin ping -h localhost -u root -p${DB_PASSWORD} --silent 2>/dev/null; then
                    print_info "MySQL 初始化完成"
                    
                    # 执行初始化脚本（如果存在）
                    if [ -f "init_db.sql" ]; then
                        print_info "执行数据库初始化脚本..."
                        docker exec -i ${MYSQL_CONTAINER_NAME} mysql -u root -p${DB_PASSWORD} < init_db.sql 2>/dev/null || true
                    fi
                    
                    return 0
                fi
                sleep 2
                retries=$((retries + 1))
                if [ $((retries % 10)) -eq 0 ]; then
                    print_info "等待 MySQL 启动... (${retries}/60)"
                fi
            done
            
            print_warn "MySQL 启动超时，但容器已创建，请稍后手动检查"
        else
            print_error "MySQL 容器创建失败"
            exit 1
        fi
    fi
    
    # 最终检查 MySQL 是否可用
    if docker exec ${MYSQL_CONTAINER_NAME} mysqladmin ping -h localhost -u root -proot123456 --silent 2>/dev/null; then
        print_info "MySQL 服务运行正常"
    else
        print_warn "MySQL 容器运行中，但连接测试失败，请稍后重试"
    fi
}

# 检查端口是否被占用
check_port() {
    local port=$1
    local service_name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        local pids=$(lsof -ti :$port 2>/dev/null)
        local process_info=""
        
        if [ ! -z "$pids" ]; then
            # 获取进程信息
            for pid in $pids; do
                local cmd=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
                process_info="${process_info}PID: $pid ($cmd) "
            done
        fi
        
        print_warn "端口 $port 已被占用"
        if [ ! -z "$process_info" ]; then
            print_warn "占用进程: $process_info"
        fi
        
        # 询问是否停止占用端口的进程
        if [ ! -z "$service_name" ]; then
            echo ""
            read -p "是否停止占用端口 $port 的进程？(y/N): " stop_process
            if [[ $stop_process == [yY] || $stop_process == [yY][eE][sS] ]]; then
                print_info "正在停止占用端口 $port 的进程..."
                for pid in $pids; do
                    kill $pid 2>/dev/null
                    sleep 1
                    # 如果还在运行，强制杀死
                    if kill -0 $pid 2>/dev/null; then
                        kill -9 $pid 2>/dev/null
                    fi
                done
                sleep 1
                
                # 再次检查端口
                if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
                    print_info "端口 $port 已释放"
                    return 0
                else
                    print_error "无法释放端口 $port"
                    return 1
                fi
            else
                return 1
            fi
        else
            return 1
        fi
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
    check_command pnpm
    check_command docker

    # 检查并启动 MySQL Docker 容器
    check_and_start_mysql

    # 获取脚本所在目录
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"

    # 检查后端端口（从配置文件读取）
    BACKEND_PORT=6000
    if [ -f "config.json" ] && command -v python3 &> /dev/null; then
        BACKEND_PORT=$(python3 -c "import json; f=open('config.json'); d=json.load(f); print(d.get('backend', {}).get('port', 6000))" 2>/dev/null || echo "6000")
    fi
    
    if ! check_port $BACKEND_PORT "后端服务"; then
        print_error "后端端口 $BACKEND_PORT 已被占用，无法启动服务"
        print_info "提示：可以手动停止占用端口的进程，或修改 config.json 中的后端端口配置"
        exit 1
    fi

    # 检查前端端口
    if ! check_port 3000 "前端服务"; then
        print_error "前端端口 3000 已被占用，无法启动服务"
        print_info "提示：可以手动停止占用端口的进程，或修改 config.json 中的前端端口配置"
        exit 1
    fi

    # 检查 Python 依赖
    print_info "检查 Python 依赖..."
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        print_warn "未检测到虚拟环境，建议创建虚拟环境"
        print_info "提示：可以运行 ./scripts/install_deps.sh 安装所有依赖"
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
        
        # 配置 pnpm 使用国内镜像源
        if ! pnpm config get registry | grep -q "npmmirror.com\|taobao.org"; then
            print_info "配置 pnpm 使用国内镜像源..."
            pnpm config set registry https://registry.npmmirror.com
        fi
        
        pnpm install
        cd ..
    fi

    # 启动后端服务
    print_info "启动后端服务 (端口 $BACKEND_PORT)..."
    cd backend
    
    # 检查后端文件是否存在
    if [ ! -f "app.py" ]; then
        print_error "后端文件不存在: backend/app.py"
        exit 1
    fi
    
    # 检查并安装 Python 依赖
    print_info "检查 Python 依赖..."
    
    # 检查关键模块
    MISSING_MODULES=()
    if ! python3 -c "import flask" 2>/dev/null; then
        MISSING_MODULES+=("flask")
    fi
    if ! python3 -c "import flask_cors" 2>/dev/null; then
        MISSING_MODULES+=("flask_cors")
    fi
    if ! python3 -c "import pymysql" 2>/dev/null; then
        MISSING_MODULES+=("pymysql")
    fi
    
    if [ ${#MISSING_MODULES[@]} -gt 0 ]; then
        print_warn "缺少以下 Python 模块: ${MISSING_MODULES[*]}"
        print_info "正在安装依赖..."
        
        # 先安装后端依赖
        if [ -f "requirements.txt" ]; then
            print_info "安装后端依赖..."
            pip install -r requirements.txt 2>&1 | grep -E "(Successfully|Requirement|ERROR|WARNING)" | tail -10
        fi
        
        # 再安装根目录依赖（包含 Scrapy）
        if [ -f "../requirements.txt" ]; then
            print_info "安装项目依赖..."
            pip install -r ../requirements.txt 2>&1 | grep -E "(Successfully|Requirement|ERROR|WARNING)" | tail -10
        fi
        
        # 验证安装结果
        sleep 1
        FAILED_MODULES=()
        for module in "${MISSING_MODULES[@]}"; do
            if ! python3 -c "import $module" 2>/dev/null; then
                FAILED_MODULES+=("$module")
            fi
        done
        
        if [ ${#FAILED_MODULES[@]} -gt 0 ]; then
            print_error "以下模块安装失败: ${FAILED_MODULES[*]}"
            print_error "请手动安装: pip install ${FAILED_MODULES[*]}"
            exit 1
        else
            print_info "依赖安装成功"
        fi
    else
        print_info "Python 依赖检查通过"
    fi
    
    # 检查 config.json 和 utils 模块
    if [ ! -f "../config.json" ]; then
        print_warn "config.json 不存在，尝试复制示例文件..."
        if [ -f "../config.json.example" ]; then
            cp ../config.json.example ../config.json
            print_info "已创建 config.json（从示例文件）"
        else
            print_error "config.json 和 config.json.example 都不存在"
            exit 1
        fi
    fi
    
    if [ ! -d "../utils" ]; then
        print_error "utils 目录不存在，无法加载配置"
        print_error "请确保项目结构完整"
        exit 1
    fi
    
    # 测试导入配置模块
    print_info "测试配置模块..."
    if ! python3 -c "import sys; sys.path.insert(0, '..'); from utils.config_loader import config" 2>/dev/null; then
        print_error "配置模块导入失败"
        print_info "运行诊断: python3 ../scripts/test_backend.py"
        exit 1
    fi
    
    # 启动后端服务
    print_info "正在启动后端服务..."
    python3 app.py > ../backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    print_info "后端服务进程已创建 (PID: $BACKEND_PID)"

    # 等待后端启动
    print_info "等待后端服务启动..."
    sleep 3

    # 检查进程是否还在运行
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "后端服务启动失败，进程已退出"
        print_error "查看错误日志："
        if [ -f "backend.log" ]; then
            echo "----------------------------------------"
            tail -30 backend.log
            echo "----------------------------------------"
        else
            print_error "日志文件不存在"
        fi
        print_info "提示：可以运行 ./scripts/check_backend.sh 进行详细诊断"
        exit 1
    fi
    
    # 检查端口是否被监听
    local retries=0
    local port_ready=false
    while [ $retries -lt 10 ]; do
        if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
            port_ready=true
            break
        fi
        sleep 1
        retries=$((retries + 1))
    done
    
    if [ "$port_ready" = true ]; then
        print_info "后端服务启动成功 (PID: $BACKEND_PID, 端口: $BACKEND_PORT)"
    else
        print_warn "后端进程运行中，但端口 $BACKEND_PORT 未监听"
        print_warn "查看日志了解详情：tail -f backend.log"
        print_info "提示：可以运行 ./scripts/check_backend.sh 进行详细诊断"
    fi

    # 启动前端服务
    print_info "启动前端服务 (端口 3000)..."
    cd frontend
    
    # 确保使用国内镜像源
    if ! pnpm config get registry | grep -q "npmmirror.com\|taobao.org"; then
        pnpm config set registry https://registry.npmmirror.com
    fi
    
    pnpm run dev > ../frontend.log 2>&1 &
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
    print_info "后端 API: http://localhost:$BACKEND_PORT"
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
