#!/bin/bash
# 验证双隧道系统状态

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🌐 Crypto Projects Dashboard - 双隧道系统状态${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# 检查本地服务器
echo -e "${BLUE}[1/4]${NC} 检查本地服务器..."
if netstat -tuln | grep -q ":8000"; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/dashboard.html)
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅${NC} 本地服务器运行正常 (HTTP 200)"
    else
        echo -e "${RED}❌${NC} 本地服务器异常 (HTTP $HTTP_CODE)"
    fi
else
    echo -e "${RED}❌${NC} 本地服务器未运行"
fi

# 检查 LocalTunnel 隧道
echo ""
echo -e "${BLUE}[2/4]${NC} 检查 LocalTunnel 隧道..."
if ps aux | grep -q "[n]ode.*lt --port 8000"; then
    LT_URL=$(cat /tmp/localtunnel.log 2>/dev/null | grep "your url is" | awk '{print $4}')
    if [ -n "$LT_URL" ]; then
        echo -e "${GREEN}✅${NC} LocalTunnel 运行中"
        echo -e "   ${GREEN}🌐 URL: $LT_URL/dashboard.html${NC}"
    else
        echo -e "${GREEN}✅${NC} LocalTunnel 运行中 (URL: https://crypto-dashboard.loca.lt/dashboard.html)"
    fi
else
    echo -e "${RED}❌${NC} LocalTunnel 未运行"
fi

# 检查 Serveo 隧道
echo ""
echo -e "${BLUE}[3/4]${NC} 检查 Serveo 隧道..."
if ps aux | grep -q "[s]sh.*serveo"; then
    SERVEO_URL=$(cat /tmp/serveo.log 2>/dev/null | grep -oE 'https?://[a-zA-Z0-9.-]+\.serveo\.net' | head -1)
    if [ -n "$SERVEO_URL" ]; then
        echo -e "${GREEN}✅${NC} Serveo 隧道运行中"
        echo -e "   ${GREEN}🌐 URL: $SERVEO_URL/dashboard.html${NC}"
    else
        echo -e "${GREEN}✅${NC} Serveo 隧道运行中"
        echo -e "   ${GREEN}🌐 URL: https://crypto9486.serveo.net/dashboard.html${NC}"
    fi
else
    echo -e "${RED}❌${NC} Serveo 隧道未运行"
fi

# 检查后台功能
echo ""
echo -e "${BLUE}[4/4]${NC} 检查后台功能..."
ACTIVE_COUNT=0

if ps aux | grep -q "[a]lpha_hunter.py"; then
    echo -e "${GREEN}✅${NC} Alpha Hunter"
    ((ACTIVE_COUNT++))
fi

if ps aux | grep -q "[s]mart_gem_scanner.py"; then
    echo -e "${GREEN}✅${NC} Smart Gem Scanner"
    ((ACTIVE_COUNT++))
fi

if ps aux | grep -q "[n]ews_market_analyzer.py"; then
    echo -e "${GREEN}✅${NC} News Market Analyzer"
    ((ACTIVE_COUNT++))
fi

if ps aux | grep -q "[b]inance_announcement_monitor.py"; then
    echo -e "${GREEN}✅${NC} Binance Monitor"
    ((ACTIVE_COUNT++))
fi

if ps aux | grep -q "[p]olymarket_scanner.py"; then
    echo -e "${GREEN}✅${NC} Polymarket Scanner"
    ((ACTIVE_COUNT++))
fi

if [ $ACTIVE_COUNT -eq 0 ]; then
    echo -e "${YELLOW}⚠️${NC} 未启动后台功能"
else
    echo -e "${GREEN}✅${NC} 运行中 ($ACTIVE_COUNT 个功能)"
fi

echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${GREEN}🌐 公网访问地址${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo -e "${YELLOW}📱 主隧道（LocalTunnel）：${NC}"
echo -e "   ${GREEN}https://crypto-dashboard.loca.lt/dashboard.html${NC}"
echo ""
echo -e "${YELLOW}🔐 备用隧道（Serveo）：${NC}"
if [ -n "$SERVEO_URL" ]; then
    echo -e "   ${GREEN}$SERVEO_URL/dashboard.html${NC}"
else
    echo -e "   ${GREEN}https://crypto9486.serveo.net/dashboard.html${NC}"
fi
echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}📁 日志文件${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo "  本地服务器:    ${GREEN}tail -f /tmp/http_server.log${NC}"
echo "  LocalTunnel:   ${GREEN}tail -f /tmp/localtunnel.log${NC}"
echo "  Serveo:        ${GREEN}tail -f /tmp/serveo.log${NC}"
echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🛠️ 管理命令${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo "  查看完整状态:   ${GREEN}./check_status.sh${NC}"
echo "  启动所有功能:   ${GREEN}./start_all.sh${NC}"
echo "  停止所有功能:   ${GREEN}./stop_all.sh${NC}"
echo "  启动 Serveo:    ${GREEN}./serveo_backup.sh${NC}"
echo "  重启 LocalTunnel: ${GREEN}pkill -f 'lt --port 8000' && nohup lt --port 8000 --subdomain crypto-dashboard > /tmp/localtunnel.log 2>&1 &${NC}"
echo ""
echo -e "${BLUE}=============================================================================${NC}"