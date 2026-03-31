#!/bin/bash
################################################################################
# Crypto Projects 功能测试脚本
################################################################################

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$(dirname "$0")"

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🧪 Crypto Projects 功能测试${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

passed=0
failed=0

# 测试 1: 依赖检查
echo -e "${YELLOW}[测试 1/6]${NC} 依赖包检查..."
python3 << 'EOPY' > /tmp/test_deps.log 2>&1
import sys
packages = ['requests', 'cryptography', 'aiohttp', 'psutil', 'dotenv', 'yaml']
missing = []
for pkg in packages:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print(f"Missing packages: {missing}")
    sys.exit(1)
else:
    print("All dependencies OK")
EOPY

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((passed++))
else
    echo -e "${RED}❌ 失败${NC}"
    ((failed++))
fi

# 测试 2: Alpha Hunter
echo -e "${YELLOW}[测试 2/6]${NC} Alpha Hunter (早期机会发现)..."
if [ -f "alpha_hunter.py" ]; then
    timeout 10 python3 alpha_hunter.py > /tmp/test_alpha.log 2>&1 && {
        echo -e "${GREEN}✅ 通过${NC}"
        ((passed++))
    } || {
        echo -e "${YELLOW}⚠️ 超时或执行失败${NC}"
        ((failed++))
    }
else
    echo -e "${RED}❌ 文件不存在${NC}"
    ((failed++))
fi

# 测试 3: Smart Gem Scanner
echo -e "${YELLOW}[测试 3/6]${NC} Smart Gem Scanner..."
if [ -f "smart_gem_scanner.py" ]; then
    timeout 10 python3 smart_gem_scanner.py > /tmp/test_gem.log 2>&1 && {
        echo -e "${GREEN}✅ 通过${NC}"
        ((passed++))
    } || {
        echo -e "${YELLOW}⚠️ 超时或执行失败${NC}"
        ((failed++))
    }
else
    echo -e "${RED}❌ 文件不存在${NC}"
    ((failed++))
fi

# 测试 4: News Market Analyzer
echo -e "${YELLOW}[测试 4/6]${NC} News Market Analyzer..."
if [ -f "news_market_analyzer.py" ]; then
    timeout 10 python3 news_market_analyzer.py dashboard > /tmp/test_news.log 2>&1 && {
        echo -e "${GREEN}✅ 通过${NC}"
        ((passed++))
    } || {
        echo -e "${YELLOW}⚠️ 超时或执行失败${NC}"
        ((failed++))
    }
else
    echo -e "${RED}❌ 文件不存在${NC}"
    ((failed++))
fi

# 测试 5: 目录结构检查
echo -e "${YELLOW}[测试 5/6]${NC} 目录结构检查..."
missing_dirs=0
required_dirs=("data/warroom/temp_news" "data/warroom/analysis/reports" "data/arbitrage" "data/logs" "data/intel" "data/alpha_hunter")
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "  ${RED}✗${NC} 缺失目录: $dir"
        ((missing_dirs++))
    fi
done

if [ $missing_dirs -eq 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((passed++))
else
    echo -e "${RED}❌ 失败 - 缺失 $missing_dirs 个目录${NC}"
    ((failed++))
fi

# 测试 6: 辅助模块检查
echo -e "${YELLOW}[测试 6/6]${NC} 辅助模块检查..."
missing_modules=0
for module in "secure_key_storage.py" "courier.py"; do
    if [ ! -f "$module" ]; then
        echo -e "  ${RED}✗${NC} 缺失模块: $module"
        ((missing_modules++))
    fi
done

if [ $missing_modules -eq 0 ]; then
    echo -e "${GREEN}✅ 通过${NC}"
    ((passed++))
else
    echo -e "${RED}❌ 失败 - 缺失 $missing_modules 个模块${NC}"
    ((failed++))
fi

# 测试总结
echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}📊 测试总结${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${GREEN}✅ 通过: ${passed}/6${NC}"
echo -e "${RED}❌ 失败: ${failed}/6${NC}"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！系统已准备就绪。${NC}"
    echo ""
    echo -e "${YELLOW}📝 快速开始：${NC}"
    echo "   ./run_alpha_hunter.sh        # 早期机会发现"
    echo "   ./run_gem_scanner.sh        # 智能宝石扫描"
    echo "   ./run_news_analyzer.sh      # 新闻市场分析"
else
    echo -e "${YELLOW}⚠️ 部分测试失败，请检查日志：${NC}"
    echo "   - /tmp/test_deps.log"
    echo "   - /tmp/test_alpha.log"
    echo "   - /tmp/test_gem.log"
    echo "   - /tmp/test_news.log"
fi

exit $failed