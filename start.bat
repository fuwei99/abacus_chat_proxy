@echo off
chcp 65001 > nul

echo 正在检查 Python 是否已安装...
python --version > nul 2>&1
if errorlevel 1 (
    echo Python 未安装。请先安装 Python 3.7 或更高版本。
    echo 安装完成后，重新运行此脚本。
    pause
    exit /b
)

echo 正在检查 pip 是否已安装...
pip --version > nul 2>&1
if errorlevel 1 (
    echo pip 未安装。请确保 pip 已正确安装并添加到环境变量。
    pause
    exit /b
)

echo 正在创建虚拟环境...
python -m venv venv
if errorlevel 1 (
    echo 创建虚拟环境失败。请检查是否已安装 venv 模块。
    pause
    exit /b
)

echo 正在激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
 echo 无法激活虚拟环境，尝试使用全局环境安装依赖
 goto install_dependencies
)

echo 虚拟环境激活成功。

:install_dependencies
echo 正在安装依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo 安装依赖失败。请检查网络连接和 requirements.txt 文件。
    pause
    exit /b
)

echo 依赖安装成功。

echo 正在启动 Flask 应用...
python app.py
if errorlevel 1 (
    echo 启动 Flask 应用失败。请检查代码和端口是否被占用。
    pause
    exit /b
)
 
echo Flask 应用已启动。默认使用 http://127.0.0.1:9876/v1

pause
exit /b
