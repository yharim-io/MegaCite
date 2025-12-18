#!/bin/bash

echo "[*] Resetting Database..."
mysql -u root -p114514 < dao/init.sql

echo "[*] Starting Server on port 8080..."
python cli.py server start 8080