#!/bin/bash

# 脚本功能：自动化安装 MySQL 并导入项目初始数据。
# 运行方式：在 Scripts 目录下执行 `sudo bash install_mysql.sh`

# --- 安全设置：任何命令失败则立即退出 ---
set -e

# --- 1. 检查 root 权限 ---
if [ "$EUID" -ne 0 ]; then
  echo "错误：此脚本需要 root 权限运行，请使用 'sudo'。"
  exit 1
fi

echo "--- [1/5] 更新软件包列表 ---"
apt-get update

echo "--- [2/5] 安装 MySQL 服务器 ---"
# 使用 -y 标志自动确认安装过程中的所有提示
apt-get install -y mysql-server

echo "--- [3/5] 启动 MySQL  ---"
systemctl start mysql
# systemctl enable mysql

# 短暂等待，确保 MySQL 服务已完全启动并准备好接受连接
echo "正在等待 MySQL 服务初始化..."
sleep 5 # 等待 5 秒

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
# 在大多数默认配置的 Ubuntu/Debian 系统上，使用 sudo 可以让 root 用户无需密码访问 MySQL
mysql < "$INIT_SQL_PATH"

echo "--- [5/5] 安装与初始化成功 ---"
echo "MySQL 已成功安装并配置！"
echo "数据库 'megacite' 及所有相关表均已创建。"
echo "你可以通过 'sudo mysql' 命令登录到 MySQL 客户端进行检查。"