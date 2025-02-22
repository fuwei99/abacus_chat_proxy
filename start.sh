#!/bin/bash

# 检查 Python 是否已安装
if ! command -v python3 &> /dev/null; then
    echo "Python 3 未安装。请先安装 Python 3.7 或更高版本。"
    echo "安装完成后，重新运行此脚本。"
    exit 1
fi

# 检查 pip 是否已安装
if ! command -v pip3 &> /dev/null; then
    echo "pip3 未安装。请确保 pip 已正确安装并添加到环境变量。"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "创建虚拟环境失败。请检查是否已安装 venv 模块。"
        exit 1
    fi
fi

# 激活虚拟环境
echo "正在激活虚拟环境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
   echo "无法激活虚拟环境，尝试使用全局环境安装依赖"
else
   echo "虚拟环境激活成功"
fi

# 安装依赖
echo "正在安装依赖..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "安装依赖失败。请检查网络连接和 requirements.txt 文件。"
    exit 1
fi

echo "依赖安装成功。"

# 启动 Flask 应用
echo "正在启动 Flask 应用..."
python3 app.py
if [ $? -ne 0 ]; then
    echo "启动 Flask 应用失败。请检查代码和端口是否被占用。"
    exit 1
fi

echo "Flask 应用已启动。默认使用 http://127.0.0.1:9876/v1"

# 等待 Ctrl+C 退出（在 shell 脚本中通常不需要像 bat 文件那样暂停）
trap "exit" INT TERM  # 捕获中断信号（Ctrl+C）和终止信号
wait
