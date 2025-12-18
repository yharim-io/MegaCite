#!/bin/bash

# 脚本功能：[macOS版] 自动化安装 MySQL 并导入项目初始数据。
# 运行方式：在 Scripts 目录下执行 `bash install_mysql_mac.sh` (不需要 sudo)

# --- 安全设置：任何命令失败则立即退出 ---
set -e

# --- 1. 环境与权限检查 ---
# macOS 使用 Homebrew，不能以 root 用户运行
if [ "$EUID" -eq 0 ]; then
  echo "错误：Homebrew 不建议使用 root 权限运行。"
  echo "请不要使用 'sudo'，直接运行：bash $0"
  exit 1
fi

# 检查是否安装了 Homebrew
if ! command -v brew &> /dev/null; then
    echo "错误：未检测到 Homebrew。请先安装 Homebrew (https://brew.sh/)"
    exit 1
fi

echo "--- [1/5] 更新 Homebrew 软件源 ---"
brew update

echo "--- [2/5] 安装 MySQL ---"
# 检查是否已经安装 MySQL
if brew list mysql &>/dev/null; then
    echo "MySQL 似乎已经安装，跳过安装步骤..."
else
    brew install mysql
fi

echo "--- [3/5] 启动 MySQL 服务 ---"
# 使用 brew services 启动，这样重启电脑后也会自动运行
brew services start mysql

# 短暂等待，macOS 初始化 MySQL 可能比 Linux 稍慢
echo "正在等待 MySQL 服务初始化..."
sleep 10 

echo "--- [4/5] 导入数据库结构和初始数据 ---"

# 获取脚本所在目录，并基于此定位 init.sql 文件
SCRIPT_DIR=$(dirname "$0")
INIT_SQL_PATH="$SCRIPT_DIR/../dao/init.sql"

# 检查 init.sql 文件是否存在
if [ ! -f "$INIT_SQL_PATH" ]; then
    echo "错误：无法找到数据库初始化文件，路径检查失败: $INIT_SQL_PATH"
    exit 1
fi

echo "找到 init.sql 文件，正在执行导入..."

# macOS Homebrew 安装的 MySQL 默认 root 用户没有密码
# 如果你之前设置过密码，这里需要改为: mysql -u root -p < "$INIT_SQL_PATH"
mysql -u root < "$INIT_SQL_PATH"

echo "--- [5/5] 安装与初始化成功 ---"
echo "MySQL 已成功安装并配置！"
echo "数据库 'megacite' 及所有相关表均已创建。"
echo "你可以通过 'mysql -u root' 命令登录到 MySQL 客户端进行检查。"