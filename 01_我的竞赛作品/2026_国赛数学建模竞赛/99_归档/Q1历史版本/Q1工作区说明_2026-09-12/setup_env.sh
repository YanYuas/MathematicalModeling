#!/bin/bash
# Q1 编程环境配置脚本
# 用途：快速搭建Python开发环境

echo "==================================="
echo "Q1 编程手环境配置"
echo "==================================="

# 检查Python版本
echo -e "\n[1/4] 检查Python版本..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "当前Python版本: $python_version"

# 创建虚拟环境
echo -e "\n[2/4] 创建虚拟环境..."
if [ -d "venv" ]; then
    echo "虚拟环境已存在，跳过创建"
else
    python -m venv venv
    echo "✓ 虚拟环境创建成功"
fi

# 激活虚拟环境
echo -e "\n[3/4] 激活虚拟环境..."
source venv/Scripts/activate

# 安装依赖
echo -e "\n[4/4] 安装依赖包..."
pip install --upgrade pip
pip install numpy matplotlib

echo -e "\n==================================="
echo "✓ 环境配置完成！"
echo "==================================="
echo ""
echo "下一步："
echo "1. source venv/Scripts/activate  # 激活环境"
echo "2. cd 代码                       # 进入代码目录"
echo "3. python q1_main.py            # 开始编程"
echo ""
echo "提示：每次打开新终端都需要激活虚拟环境"
