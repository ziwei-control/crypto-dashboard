#!/bin/bash
################################################################################
# 🌐 Serveo 公网隧道启动脚本（使用 autossh 自动重连）
################################################################################

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

cd /root/.copaw/crypto_projects

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🌐 启动 Serveo 公网隧道${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# 检查 autossh 是否安装
if ! command -v autossh &> /dev/null; then
    echo -e "${YELLOW}⏳${NC} 安装 autossh..."
    apt-get update -qq && apt-get install -y autossh > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅${NC} autossh 安装成功"
    else
        echo -e "${RED}❌${NC} autossh 安装失败，使用普通 SSH"
        USE_AUTOSSH=0
    fi
else
    echo -e "${GREEN}✅${NC} autossh 已安装"
    USE_AUTOSSH=1
fi

echo ""

# 停止现有的 serveo 隧道
echo -e "${YELLOW}[1/2]${NC} 停止现有隧道..."
pkill -f "ssh.*serveo.net" 2>/dev/null
pkill -f "autossh.*serveo.net" 2>/dev/null
sleep 2
echo -e "${GREEN}✅${NC} 现有隧道已停止"

# 启动新隧道
echo -e "${YELLOW}[2/2]${NC} 启动新隧道..."
echo ""

if [ "$USE_AUTOSSH" = "1" ]; then
    # 使用 autossh 启动（自动重连）
    nohup autossh -M 0 \
        -o "ServerAliveInterval 60" \
        -o "ServerAliveCountMax 3" \
        -o "ExitOnForwardFailure yes" \
        -o "StrictHostKeyChecking=no" \
        -R 0:localhost:8000 serveo.net > /tmp/serveo.log 2>&1 &
    
    SSH_PID=$!
    echo -e "${GREEN}✅${NC} Serveo 隧道已启动 (autossh, PID: $SSH_PID)"
else
    # 使用普通 SSH 启动
    nohup ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 0:localhost:8000 serveo.net > /tmp/serveo.log 2>&1 &
    
    SSH_PID=$!
    echo -e "${GREEN}✅${NC} Serveo 隧道已启动 (SSH, PID: $SSH_PID)"
fi

echo $SSH_PID > /tmp/serveo.pid

# 等待隧道启动并获取 URL
echo ""
echo -e "${YELLOW}⏳${NC} 等待隧道启动..."

for i in {1..15}; do
    sleep 1
    if grep -q "serveo.net" /tmp/serveo.log 2>/dev/null; then
        break
    fi
done

# 显示结果
echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${GREEN}🎉 隧道启动成功！${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# 尝试从日志中提取 URL
if [ -f /tmp/serveo.log ]; then
    echo -e "${BLUE}📋 隧道日志：${NC}"
    tail -10 /tmp/serveo.log
    echo ""
    
    URL=$(grep -oE 'https?://[a-zA-Z0-9.-]+\.serveo\.net' /tmp/serveo.log | head -1)
    if [ -n "$URL" ]; then
        echo -e "${GREEN}🌐 公网 URL: $URL${NC}"
        echo ""
        echo -e "${BLUE}访问地址：${NC}"
        echo "  📱 Dashboard: ${GREEN}$URL/dashboard.html${NC}"
    fi
fi

echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}📁 日志文件：${NC} ${GREEN}/tmp/serveo.log${NC}"
echo -e "${BLUE}🛠️ 管理命令：${NC}"
echo "  查看日志: ${GREEN}tail -f /tmp/serveo.log${NC}"
echo "  停止隧道: ${GREEN}pkill -f 'serveo.net'${NC}"
echo "  重启隧道: ${GREEN}./serveo_tunnel.sh${NC}"
echo -e "${BLUE}=============================================================================${NC}"
