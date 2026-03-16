#!/bin/bash
echo "========================================"
echo "  Email Server 构建脚本 (Linux/Mac)"
echo "========================================"

# 检测操作系统
OS_TYPE=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="mac"
else
    echo "[警告] 未知操作系统: $OSTYPE"
fi

# Linux 上检查并安装 binutils (提供 objdump)
if [[ "$OS_TYPE" == "linux" ]]; then
    if ! command -v objdump &> /dev/null; then
        echo "[依赖] objdump 未找到，正在尝试安装 binutils..."
        
        # 检测包管理器并安装（优先使用 sudo，没有则直接运行）
        INSTALL_CMD=""
        if command -v apt-get &> /dev/null; then
            INSTALL_CMD="apt-get update && apt-get install -y binutils"
        elif command -v yum &> /dev/null; then
            INSTALL_CMD="yum install -y binutils"
        elif command -v dnf &> /dev/null; then
            INSTALL_CMD="dnf install -y binutils"
        elif command -v pacman &> /dev/null; then
            INSTALL_CMD="pacman -S --noconfirm binutils"
        elif command -v zypper &> /dev/null; then
            INSTALL_CMD="zypper install -y binutils"
        fi
        
        if [[ -n "$INSTALL_CMD" ]]; then
            # 检查是否有 sudo 且可用
            if command -v sudo &> /dev/null && sudo -n true 2>/dev/null; then
                eval "sudo $INSTALL_CMD"
            elif [[ $EUID -eq 0 ]]; then
                # 已经是 root 用户
                eval "$INSTALL_CMD"
            else
                echo "[提示] 需要 root 权限安装 binutils，请手动执行："
                echo ""
                echo "    sudo $INSTALL_CMD"
                echo ""
                echo "安装完成后重新运行此脚本。"
                exit 1
            fi
        else
            echo "[错误] 无法识别包管理器，请手动安装 binutils"
            exit 1
        fi
        
        if ! command -v objdump &> /dev/null; then
            echo "[错误] binutils 安装失败"
            exit 1
        fi
        echo "[依赖] binutils 安装成功"
    fi
fi

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "[错误] uv 未安装，请先安装: pip install uv"
    exit 1
fi

# 同步依赖
echo "[1/2] 同步依赖..."
uv sync
if [ $? -ne 0 ]; then
    echo "[错误] 依赖同步失败"
    exit 1
fi

# 构建 exe
echo "[2/2] 构建可执行文件..."
uv run pyinstaller EmailServer.spec --noconfirm
if [ $? -ne 0 ]; then
    echo "[错误] 构建失败"
    exit 1
fi

echo ""
echo "========================================"
echo "  构建成功！"
echo "  输出文件: dist/EmailServer"
echo "========================================"
