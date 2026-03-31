#!/bin/bash
################################################################################
# 🚀 Crypto Projects - 一键启动所有后台功能
################################################################################

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

cd /root/.copaw/crypto_projects

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🚀 启动 Crypto Projects 后台功能${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# 1. Alpha Hunter
echo -e "${YELLOW}[1/5]${NC} 启动 Alpha Hunter..."
if ps aux | grep -q "[a]lpha_hunter.py"; then
    echo -e "${GREEN}✅${NC} Alpha Hunter 已在运行"
else
    nohup python3 alpha_hunter.py > /tmp/alpha.log 2>&1 &
    echo $! > /tmp/alpha.pid
    echo -e "${GREEN}✅${NC} Alpha Hunter 已启动 (PID: $(cat /tmp/alpha.pid))"
fi

# 2. Smart Gem Scanner
echo -e "${YELLOW}[2/5]${NC} 启动 Smart Gem Scanner..."
if ps aux | grep -q "[s]mart_gem_scanner.py"; then
    echo -e "${GREEN}✅${NC} Smart Gem Scanner 已在运行"
else
    nohup python3 smart_gem_scanner.py > /tmp/gem.log 2>&1 &
    echo $! > /tmp/gem.pid
    echo -e "${GREEN}✅${NC} Smart Gem Scanner 已启动 (PID: $(cat /tmp/gem.pid))"
fi

# 3. News Market Analyzer
echo -e "${YELLOW}[3/5]${NC} 启动 News Market Analyzer..."
if ps aux | grep -q "[n]ews_market_analyzer.py"; then
    echo -e "${GREEN}✅${NC} News Market Analyzer 已在运行"
else
    nohup python3 news_market_analyzer.py dashboard > /tmp/news.log 2>&1 &
    echo $! > /tmp/news.pid
    echo -e "${GREEN}✅${NC} News Market Analyzer 已启动 (PID: $(cat /tmp/news.pid))"
fi

# 4. Binance Announcement Monitor
echo -e "${YELLOW}[4/5]${NC} 启动 Binance Announcement Monitor..."
if ps aux | grep -q "[b]inance_announcement_monitor.py"; then
    echo -e "${GREEN}✅${NC} Binance Monitor 已在运行"
else
    nohup python3 binance_announcement_monitor.py > /tmp/binance.log 2>&1 &
    echo $! > /tmp/binance.pid
    echo -e "${GREEN}✅${NC} Binance Monitor 已启动 (PID: $(cat /tmp/binance.pid))"
fi

# 5. Polymarket Scanner
echo -e "${YELLOW}[5/5]${NC} 启动 Polymarket Scanner..."
if ps aux | grep -q "[p]olymarket_scanner.py"; then
    echo -e "${GREEN}✅${NC} Polymarket Scanner 已在运行"
else
    nohup python3 polymarket_scanner.py > /tmp/polymarket.log 2>&1 &
    echo $! > /tmp/polymarket.pid
    echo -e "${GREEN}✅${NC} Polymarket Scanner 已启动 (PID: $(cat /tmp/polymarket.pid))"
fi

echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${GREEN}🎉 所有功能已启动！${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo -e "${BLUE}📋 后台进程：${NC}"
ps aux | grep -E "alpha_hunter|smart_gem|news_market_analyzer|binance_announcement|polymarket" | grep -v grep | awk '{print "  " $11 " (PID: " $2 ")"}'
echo ""
echo -e "${BLUE}📁 日志文件：${NC}"
echo "  Alpha Hunter:       ${GREEN}/tmp/alpha.log${NC}"
echo "  Smart Gem Scanner:  ${GREEN}/tmp/gem.log${NC}"
echo "  News Analyzer:      ${GREEN}/tmp/news.log${NC}"
echo "  Binance Monitor:    ${GREEN}/tmp/binance.log${NC}"
echo "  Polymarket Scanner: ${GREEN}/tmp/polymarket.log${NC}"
echo ""
echo -e "${BLUE}🌐 公网访问：${NC}"
echo "  Dashboard: ${GREEN}https://crypto-dashboard.loca.lt/dashboard.html${NC}"
echo ""
echo -e "${BLUE}🛠️ 管理命令：${NC}"
echo "  查看状态: ${GREEN}./check_status.sh${NC}"
echo "  停止所有: ${GREEN}./stop_all.sh${NC}"
echo ""
echo -e "${BLUE}=============================================================================${NC}"