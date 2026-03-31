#!/bin/bash
################################################################################
# 📱 APK 在线构建详细指南
################################################################################

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}📱 Crypto Dashboard APK 在线构建详细指南${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${GREEN}✅ 已准备完成的内容：${NC}"
echo "  • PWA 配置文件: manifest.json"
echo "  • Service Worker: sw.js"
echo "  • PWA 网页: dashboard_pwa.html"
echo "  • 应用图标: 8 个尺寸 (72-512px)"
echo "  • Capacitor 项目: 已初始化"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}方案 1：PWABuilder（推荐）${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${YELLOW}步骤 1：访问 PWABuilder${NC}"
echo "  🌐 打开浏览器"
echo "  📍 访问: ${GREEN}https://www.pwabuilder.com${NC}"
echo ""

echo -e "${YELLOW}步骤 2：输入 PWA URL${NC}"
echo "  📝 在输入框中输入:"
echo "  ${GREEN}https://crypto-dashboard.loca.lt/dashboard_pwa.html${NC}"
echo ""

echo -e "${YELLOW}步骤 3：点击构建${NC}"
echo "  🖱️ 点击 \"Start\" 或 \"Pack\" 按钮"
echo ""

echo -e "${YELLOW}步骤 4：选择平台${NC}"
echo "  📱 选择 ${GREEN}Android${NC}"
echo ""

echo -e "${YELLOW}步骤 5：等待构建${NC}"
echo "  ⏳ 等待大约 2-5 分钟"
echo ""

echo -e "${YELLOW}步骤 6：下载 APK${NC}"
echo "  📥 点击下载按钮"
echo "  📄 保存 APK 文件"
echo ""

echo -e "${YELLOW}步骤 7：安装到手机${NC}"
echo "  📲 传输 APK 到手机"
echo "  📱 点击 APK 文件安装"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}方案 2：使用 Bubblewrap CLI（本地）${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${YELLOW}步骤 1：安装 Bubblewrap${NC}"
echo "  ${GREEN}npm install -g @bubblewrap/cli${NC}"
echo ""

echo -e "${YELLOW}步骤 2：初始化项目${NC}"
echo "  ${GREEN}bubblewrap init --manifest https://crypto-dashboard.loca.lt/manifest.json${NC}"
echo ""

echo -e "${YELLOW}步骤 3：构建 APK${NC}"
echo "  ${GREEN}bubblewrap build${NC}"
echo ""

echo -e "${YELLOW}步骤 4：下载 APK${NC}"
echo "  📥 APK 文件将在当前目录生成"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}方案 3：使用 Weppy（在线）${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${YELLOW}访问:${NC} ${GREEN}https://www.weppy.com${NC}"
echo "  输入 PWA URL"
echo "  选择 Android 平台"
echo "  下载 APK"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}方案 4：使用 GoNative（在线）${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${YELLOW}访问:${NC} ${GREEN}https://gonative.io${NC}"
echo "  输入 PWA URL"
echo "  选择 Android 平台"
echo "  下载 APK"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}📱 PWA URL 复制区${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo -e "${GREEN}https://crypto-dashboard.loca.lt/dashboard_pwa.html${NC}"
echo ""
echo -e "${GREEN}https://crypto-dashboard.loca.lt/manifest.json${NC}"
echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${YELLOW}⚠️ 注意事项${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo "  1. ${YELLOW}确保公网隧道正常运行${NC}"
echo "     • LocalTunnel: https://crypto-dashboard.loca.lt"
echo "     • Serveo: https://crypto0176.serveo.net"
echo ""
echo "  2. ${YELLOW}使用 HTTPS URL${NC}"
echo "     • PWA 需要 HTTPS 才能安装"
echo ""
echo "  3. ${YELLOW}等待构建完成${NC}"
echo "     • 通常需要 2-5 分钟"
echo ""
echo "  4. ${YELLOW}检查 APK 质量${NC}"
echo "     • 确保图标正确显示"
echo "     • 确保应用名称正确"
echo ""
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${YELLOW}🎯 推荐操作步骤${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo "  1️⃣  ${GREEN}访问 PWABuilder${NC}"
echo "      https://www.pwabuilder.com"
echo ""
echo "  2️⃣  ${GREEN}复制并粘贴 URL${NC}"
echo "      https://crypto-dashboard.loca.lt/dashboard_pwa.html"
echo ""
echo "  3️⃣  ${GREEN}点击构建${NC}"
echo ""
echo "  4️⃣  ${GREEN}等待 2-5 分钟${NC}"
echo ""
echo "  5️⃣  ${GREEN}下载 APK${NC}"
echo ""
echo "  6️⃣  ${GREEN}安装到手机${NC}"
echo ""
echo -e "${BLUE}=============================================================================${NC}"