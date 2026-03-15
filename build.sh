#!/bin/bash
echo "========================================"
echo "  Email Server 构建脚本 (Linux/Mac)"
echo "========================================"

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
