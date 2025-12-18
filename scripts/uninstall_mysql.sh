#!/bin/bash

# 卸载 MySQL 的自动化脚本（谨慎使用）
# 用法:
#   sudo bash uninstall_mysql.sh        # 交互式，会询问是否删除数据文件/配置
#   sudo bash uninstall_mysql.sh --yes  # 非交互式，强制删除所有 MySQL 包、数据与配置

set -euo pipefail

FORCE=false
if [ "${1-}" = "--yes" ] || [ "${1-}" = "-y" ]; then
  FORCE=true
fi

if [ "$EUID" -ne 0 ]; then
  echo "错误: 请使用 sudo 或 root 运行此脚本。"
  exit 1
fi

read -r -p "警告：此操作将停止 MySQL 服务并可能删除数据库数据。你确定要继续吗? [y/N] " answer
if [ "$FORCE" = true ]; then
  echo "--yes 指定，跳过交互确认。"
else
  case "$answer" in
    [yY][eE][sS]|[yY])
      ;;
    *)
      echo "已取消。"
      exit 0
      ;;
  esac
fi

echo "停止 MySQL 服务..."
systemctl stop mysql || true

# 尝试用 mysql 客户端删除数据库（如果存在）
DBNAME="megacite"
if command -v mysql >/dev/null 2>&1; then
  echo "尝试删除数据库 '$DBNAME'（如果存在）..."
  # 以 root 身份连接（在默认配置下 root 可能通过 socket 登录）
  mysql -e "DROP DATABASE IF EXISTS \\`$DBNAME\\`;" || true
else
  echo "警告：mysql 客户端不可用，跳过删除数据库步骤。"
fi

# 卸载 MySQL 包
echo "卸载 mysql-server 包（apt）..."
apt-get remove -y --purge mysql-server mysql-client mysql-common mysql-server-core-* mysql-client-core-*

echo "自动清理不再需要的依赖..."
apt-get autoremove -y
apt-get autoclean -y

# 删除 MySQL 数据目录和配置（需确认或强制）
if [ "$FORCE" = true ]; then
  DO_CLEAN=true
else
  read -r -p "是否删除 MySQL 数据目录 '/var/lib/mysql' 和配置 '/etc/mysql' ?  此操作不可恢复。 [y/N] " delans
  case "$delans" in
    [yY][eE][sS]|[yY]) DO_CLEAN=true ;;
    *) DO_CLEAN=false ;;
  esac
fi

if [ "$DO_CLEAN" = true ]; then
  echo "删除 /var/lib/mysql ..."
  rm -rf /var/lib/mysql || true
  echo "删除 /etc/mysql ..."
  rm -rf /etc/mysql || true
  echo "删除 /var/log/mysql 日志（如存在）..."
  rm -rf /var/log/mysql* || true
fi

# 禁用与停止服务（确保已停止）
systemctl disable mysql || true
systemctl stop mysql || true

echo "MySQL 卸载与可选清理已完成。"

echo "建议：若你打算重新安装 MySQL，请检查 /etc/apt/sources.list 与 apt 存储库，随后运行："
echo "  sudo apt-get update && sudo apt-get install -y mysql-server"

exit 0
