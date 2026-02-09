#!/bin/bash

# 依赖安装脚本

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

print_info "=========================================="
print_info "  安装项目依赖"
print_info "=========================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 未安装"
    exit 1
fi

print_info "Python 版本: $(python3 --version)"
echo ""

# 配置 pip 镜像源
print_step "0. 配置 pip 镜像源..."
PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
PIP_TRUSTED_HOST="${PIP_TRUSTED_HOST:-pypi.tuna.tsinghua.edu.cn}"

# 检查是否已有 pip 配置文件
PIP_CONFIG_DIR="$HOME/.pip"
PIP_CONFIG_FILE="$PIP_CONFIG_DIR/pip.conf"

if [ ! -f "$PIP_CONFIG_FILE" ]; then
    print_info "创建 pip 配置文件..."
    mkdir -p "$PIP_CONFIG_DIR"
    cat > "$PIP_CONFIG_FILE" << EOF
[global]
index-url = $PIP_INDEX_URL

[install]
trusted-host = $PIP_TRUSTED_HOST
EOF
    print_info "✓ pip 配置文件已创建: $PIP_CONFIG_FILE"
else
    print_info "✓ pip 配置文件已存在: $PIP_CONFIG_FILE"
fi
echo ""

# 安装根目录依赖（包含 Scrapy）
print_step "1. 安装项目依赖（Scrapy 等）..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        print_info "✓ 项目依赖安装成功"
    else
        print_error "✗ 项目依赖安装失败"
        exit 1
    fi
else
    print_warn "requirements.txt 不存在，跳过"
fi
echo ""

# 安装后端依赖
print_step "2. 安装后端依赖（Flask 等）..."
if [ -f "backend/requirements.txt" ]; then
    pip install -r backend/requirements.txt
    if [ $? -eq 0 ]; then
        print_info "✓ 后端依赖安装成功"
    else
        print_error "✗ 后端依赖安装失败"
        exit 1
    fi
else
    print_warn "backend/requirements.txt 不存在，跳过"
fi
echo ""

# 验证关键模块
print_step "3. 验证关键模块..."
MODULES=("flask" "flask_cors" "pymysql" "scrapy")
ALL_OK=true

for module in "${MODULES[@]}"; do
    if python3 -c "import $module" 2>/dev/null; then
        print_info "✓ $module"
    else
        print_error "✗ $module - 未安装"
        ALL_OK=false
    fi
done

echo ""
if [ "$ALL_OK" = true ]; then
    print_info "=========================================="
    print_info "  所有依赖安装成功！"
    print_info "=========================================="
else
    print_error "=========================================="
    print_error "  部分模块未安装，请检查错误信息"
    print_error "=========================================="
    exit 1
fi
