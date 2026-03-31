#!/bin/bash
################################################################################
# 🛑 Crypto Projects - 停止所有后台功能
################################################################################

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🛑 停止 Crypto Projects 后台功能${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# 停止 Alpha Hunter
echo -e "${YELLOW}[1/6]${NC} 停止 Alpha Hunter..."
if [ -f /tmp/alpha.pid ]; then
    kill $(cat /tmp/alpha.pid) 2>/dev/null
    rm -f /tmp/alpha.pid
    echo -e "${GREEN}✅${NC} Alpha Hunter 已停止"
else
    pkill -f "alpha_hunter.py" 2>/dev/null
    echo -e "${GREEN}✅${NC} Alpha Hunter 已停止"
fi

# 停止 Smart Gem Scanner
echo -e "${YELLOW}[2/6]${NC} 停止 Smart Gem Scanner..."
if [ -f /tmp/gem.pid ]; then
    kill $(cat /tmp/gem.pid) 2>/dev/null
    rm -f /tmp/gem.pid
    echo -e "${GREEN}✅${NC} Smart Gem Scanner 已停止"
else
    pkill -f "smart_gem_scanner.py" 2>/dev/null
    echo -e "${GREEN}✅${NC} Smart Gem Scanner 已停止"
fi

# 停止 News Market Analyzer
echo -e "${YELLOW}[3/6]${NC} 停止 News Market Analyzer..."
if [ -f /tmp/news.pid ]; then
    kill $(cat /tmp/news.pid) 2>/dev/null
    rm -f /tmp/news.pid
    echo -e "${GREEN}✅${NC} News Market Analyzer 已停止"
else
    pkill -f "news_market_analyzer.py" 2>/dev/null
    echo -e "${GREEN}✅${NC} News Market Analyzer 已停止"
fi

# 停止 Binance Monitor
echo -e "${YELLOW}[4/6]${NC} 停止 Binance Monitor..."
if [ -f /tmp/binance.pid ]; then
    kill $(cat /tmp/binance.pid) 2>/dev/null
    rm -f /tmp/binance.pid
    echo -e "${GREEN}✅${NC} Binance Monitor 已停止"
else
    pkill -f "binance_announcement_monitor.py" 2>/dev/null
    echo -e "${GREEN}✅${NC} Binance Monitor 已停止"
fi

# 停止 Polymarket Scanner
echo -e "${YELLOW}[5/6]${NC} 停止 Polymarket Scanner..."
if [ -f /tmp/polymarket.pid ]; then
    kill $(cat /tmp/polymarket.pid) 2>/dev/null
    rm -f /tmp/polymarket.pid
    echo -e "${GREEN}✅${NC} Polymarket Scanner 已停止"
else
    pkill -f "polymarket_scanner.py" 2>/dev/null
    echo -e "${GREEN}✅${NC} Polymarket Scanner 已停止"
fi

# 停止 LocalTunnel（可选）
echo -e "${YELLOW}[6/6]${NC} 停止 LocalTunnel 隧道..."
if ps aux | grep -q "[n]ode.*lt --port 8000"; then
    pkill -f "lt --port 8000"
    echo -e "${GREEN}✅${NC} LocalTunnel 隧道已停止"
else
    echo -e "${GREEN}✅${NC} LocalTunnel 隧道未运行"
fi

echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${GREEN}🎉 所有功能已停止！${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo -e "${BLUE}🛠️ 管理命令：${NC}"
echo "  启动所有: ${GREEN}./start_all.sh${NC}"
echo "  查看状态: ${GREEN}./check_status.sh${NC}"
echo ""
echo -e "${BLUE}=============================================================================${NC}"