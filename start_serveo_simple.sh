#!/bin/bash
# 简化版 Serveo 隧道启动

echo "🌐 启动 Serveo 隧道..."

# 停止现有隧道
pkill -f "ssh.*serveo" 2>/dev/null
screen -wipe serveo 2>/dev/null
sleep 2

# 使用随机子域名
SUBDOMAIN="crypto$(date +%s | tail -c 4)"

# 直接使用 SSH 启动（不需要 screen）
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:localhost:8000 ${SUBDOMAIN}.serveo.net > /tmp/serveo.log 2>&1 &

echo "✅ Serveo 隧道已启动"
echo "🌐 URL: https://${SUBDOMAIN}.serveo.net/dashboard.html"
echo ""
echo "日志: tail -f /tmp/serveo.log"
