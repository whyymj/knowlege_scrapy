#!/bin/bash

# pip 镜像源配置脚本

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

print_info "=========================================="
print_info "  配置 pip 镜像源"
print_info "=========================================="
echo ""

# 检测操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    # Linux/Mac
    PIP_CONFIG_DIR="$HOME/.pip"
    PIP_CONFIG_FILE="$PIP_CONFIG_DIR/pip.conf"
    CONFIG_EXAMPLE="$PROJECT_ROOT/pip.conf.example"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    PIP_CONFIG_DIR="$APPDATA/pip"
    PIP_CONFIG_FILE="$PIP_CONFIG_DIR/pip.ini"
    CONFIG_EXAMPLE="$PROJECT_ROOT/pip.conf.example"
else
    print_error "不支持的操作系统: $OSTYPE"
    exit 1
fi

# 检查配置文件是否存在
if [ -f "$PIP_CONFIG_FILE" ]; then
    print_warn "pip 配置文件已存在: $PIP_CONFIG_FILE"
    read -p "是否覆盖现有配置? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "已取消配置"
        exit 0
    fi
fi

# 创建配置目录
print_step "创建配置目录..."
mkdir -p "$PIP_CONFIG_DIR"
if [ $? -eq 0 ]; then
    print_info "✓ 配置目录已创建: $PIP_CONFIG_DIR"
else
    print_error "✗ 创建配置目录失败"
    exit 1
fi

# 复制配置文件
print_step "复制配置文件..."
if [ -f "$CONFIG_EXAMPLE" ]; then
    cp "$CONFIG_EXAMPLE" "$PIP_CONFIG_FILE"
    print_info "✓ 配置文件已复制: $PIP_CONFIG_FILE"
else
    # 如果示例文件不存在，直接创建
    cat > "$PIP_CONFIG_FILE" << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple

[install]
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
    print_info "✓ 配置文件已创建: $PIP_CONFIG_FILE"
fi

echo ""
print_info "=========================================="
print_info "  配置完成！"
print_info "=========================================="
print_info "配置文件位置: $PIP_CONFIG_FILE"
print_info ""
print_info "现在可以直接使用 pip install，无需指定镜像源"
print_info "例如: pip install -r requirements.txt"
echo ""
