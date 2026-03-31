#!/bin/bash
################################################################################
# 📱 APK 构建指南
################################################################################

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}📱 Crypto Dashboard APK 构建指南${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${YELLOW}当前状态：${NC}"
echo -e "${GREEN}✅${NC} Capacitor 项目已初始化"
echo -e "${GREEN}✅${NC} Android 平台已添加"
echo -e "${RED}❌${NC} 缺少 Java JDK（需要构建 APK）"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}方案选择${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${GREEN}方案 1：使用在线工具（推荐，无需安装 Java）${NC}"
echo -e "  工具: PWABuilder (https://www.pwabuilder.com)"
echo -e "  步骤:"
echo "    1. 访问: https://www.pwabuilder.com"
echo "    2. 输入 PWA URL: https://crypto-dashboard.loca.lt/dashboard_pwa.html"
echo "    3. 点击 'Package for Android'"
echo "    4. 下载 APK 文件"
echo -e "  优点: ${GREEN}简单快速，无需安装 Java${NC}"
echo -e "  缺点: ${YELLOW}依赖在线服务${NC}"
echo ""

echo -e "${GREEN}方案 2：使用本地构建（需要安装 Java JDK）${NC}"
echo -e "  工具: Capacitor + Android Gradle"
echo -e "  步骤:"
echo "    1. 安装 Java JDK: ${YELLOW}apt install openjdk-21-jdk${NC}"
echo "    2. 配置环境变量: ${YELLOW}export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64${NC}"
echo "    3. 构建 APK: ${YELLOW}cd android && ./gradlew assembleDebug${NC}"
echo "    4. APK 位置: ${YELLOW}android/app/build/outputs/apk/debug/app-debug.apk${NC}"
echo -e "  优点: ${GREEN}完全本地控制${NC}"
echo -e "  缺点: ${YELLOW}需要安装 Java（约 500MB）${NC}"
echo ""

echo -e "${GREEN}方案 3：使用 Bubblewrap（需要 Node.js 和 Java）${NC}"
echo -e "  工具: Bubblewrap CLI"
echo -e "  步骤:"
echo "    1. 安装: ${YELLOW}npm install -g @bubblewrap/cli${NC}"
echo "    2. 初始化: ${YELLOW}bubblewrap init --manifest https://crypto-dashboard.loca.lt/manifest.json${NC}"
echo "    3. 构建: ${YELLOW}bubblewrap build${NC}"
echo -e "  优点: ${GREEN}Google 官方工具${NC}"
echo -e "  缺点: ${YELLOW}配置较复杂${NC}"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${YELLOW}推荐操作步骤${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${GREEN}快速方法（5 分钟内完成）：${NC}"
echo "  1. 打开浏览器"
echo "  2. 访问: https://www.pwabuilder.com"
echo "  3. 输入 URL: https://crypto-dashboard.loca.lt/dashboard_pwa.html"
echo "  4. 点击 'Package for Android'"
echo "  5. 下载 APK"
echo "  6. 安装到手机"
echo ""

echo -e "${YELLOW}如果要本地构建（需要等待 Java 安装）：${NC}"
echo "  运行: ${GREEN}bash build_apk_local.sh${NC}"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}文件位置${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo -e "项目目录: ${GREEN}/root/.copaw/crypto_projects${NC}"
echo -e "Web 文件:  ${GREEN}www/${NC}"
echo -e "Android 项目: ${GREEN}android/${NC}"
echo -e "配置文件:  ${GREEN}capacitor.config.json${NC}"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}当前可用资源${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo -e "✅ PWA 配置文件: manifest.json"
echo -e "✅ Service Worker: sw.js"
echo -e "✅ PWA 网页: dashboard_pwa.html"
echo -e "✅ 应用图标: icons/ (8 个尺寸)"
echo -e "✅ Capacitor 项目: 已初始化"
echo -e "✅ Android 平台: 已添加"
echo -e "❌ Java JDK: 未安装"
echo ""

echo -e "${BLUE}=============================================================================${NC}"