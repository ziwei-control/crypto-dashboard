#!/bin/bash
################################################################################
# 📱 APK 构建完整指南（Capacitor + Gradle）
################################################################################

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}📱 Crypto Dashboard APK 构建完整指南${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${GREEN}✅ 已完成：${NC}"
echo "  • PWA 配置文件"
echo "  • Capacitor 项目初始化"
echo "  • Android 平台添加"
echo "  • Web 资源准备"
echo ""

echo -e "${YELLOW}⚠️ 需要的环境：${NC}"
echo "  1. Java JDK 17 或更高"
echo "  2. Android SDK"
echo "  3. Gradle"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}方案 1：在有 Java 环境的机器上构建${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${YELLOW}步骤 1：传输项目到构建机器${NC}"
echo "  📁 将整个 crypto_projects 文件夹复制到有 Java 环境的机器"
echo ""

echo -e "${YELLOW}步骤 2：检查 Java 环境${NC}"
echo "  ${GREEN}java -version${NC}"
echo "  ${GREEN}echo \$JAVA_HOME${NC}"
echo ""

echo -e "${YELLOW}步骤 3：进入 Android 目录${NC}"
echo "  ${GREEN}cd crypto_projects/android${NC}"
echo ""

echo -e "${YELLOW}步骤 4：构建 Debug APK${NC}"
echo "  ${GREEN}./gradlew assembleDebug${NC}"
echo ""

echo -e "${YELLOW}步骤 5：查找 APK${NC}"
echo "  📄 位置: ${GREEN}app/build/outputs/apk/debug/app-debug.apk${NC}"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}方案 2：使用 Docker 构建（推荐）${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${YELLOW}步骤 1：安装 Docker${NC}"
echo "  ${GREEN}curl -fsSL https://get.docker.com | sh${NC}"
echo ""

echo -e "${YELLOW}步骤 2：使用 Docker 构建镜像${NC}"
echo "  ${GREEN}cd crypto_projects${NC}"
echo "  ${GREEN}docker build -t crypto-dashboard .${NC}"
echo ""

echo -e "${YELLOW}步骤 3：运行构建${NC}"
echo "  ${GREEN}docker run --rm -v \$(pwd):/app -w /app/android ./gradlew assembleDebug${NC}"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}方案 3：使用 GitHub Actions（CI/CD）${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${YELLOW}步骤 1：推送到 GitHub${NC}"
echo "  ${GREEN}git init${NC}"
echo "  ${GREEN}git add .${NC}"
echo "  ${GREEN}git commit -m 'Add PWA project'${NC}"
echo "  ${GREEN}git remote add origin <your-repo-url>${NC}"
echo "  ${GREEN}git push -u origin main${NC}"
echo ""

echo -e "${YELLOW}步骤 2：创建 GitHub Actions workflow${NC}"
echo "  创建文件: ${GREEN}.github/workflows/build-apk.yml${NC}"
echo ""

echo -e "${YELLOW}步骤 3：配置 workflow${NC}"
cat << 'EOF'
name: Build Android APK

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Java
      uses: actions/setup-java@v2
      with:
        distribution: 'adopt'
        java-version: '17'
    
    - name: Grant execute permission for gradlew
      run: chmod +x android/gradlew
    
    - name: Build Debug APK
      run: cd android && ./gradlew assembleDebug
    
    - name: Upload APK
      uses: actions/upload-artifact@v2
      with:
        name: app-debug
        path: android/app/build/outputs/apk/debug/app-debug.apk
EOF
echo ""

echo -e "${YELLOW}步骤 4：提交并推送${NC}"
echo "  ${GREEN}git add .github/workflows/build-apk.yml${NC}"
echo "  ${GREEN}git commit -m 'Add CI/CD workflow'${NC}"
echo "  ${GREEN}git push${NC}"
echo ""

echo -e "${YELLOW}步骤 5：下载 APK${NC}"
echo "  在 GitHub Actions 页面下载构建的 APK"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}方案 4：使用 APK 构建服务${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${YELLOW}推荐服务：${NC}"
echo "  1. ${GREEN}AppCenter${NC} - https://appcenter.ms"
echo "  2. ${GREEN}Bitrise${NC} - https://www.bitrise.io"
echo "  3. ${GREEN}Codemagic${NC} - https://codemagic.io"
echo "  4. ${GREEN}GitHub Actions${NC} - https://github.com"
echo ""

echo -e "${YELLOW}使用步骤：${NC}"
echo "  1. 注册账号"
echo "  2. 连接 GitHub 仓库"
echo "  3. 配置构建流程"
echo "  4. 自动构建 APK"
echo "  5. 下载 APK"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}方案 5：使用在线构建工具（最简单）${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${YELLOW}推荐工具：${NC}"
echo "  1. ${GREEN}PWABuilder${NC} - https://www.pwabuilder.com"
echo "  2. ${GREEN}Weppy${NC} - https://www.weppy.com"
echo "  3. ${GREEN}GoNative${NC} - https://gonative.io"
echo "  4. ${GREEN}AndroïdPWA${NC} - https://androidpwa.com"
echo ""

echo -e "${YELLOW}使用步骤：${NC}"
echo "  1. 访问网站"
echo "  2. 输入 PWA URL: ${GREEN}https://crypto-dashboard.loca.lt/dashboard_pwa.html${NC}"
echo "  3. 选择 Android 平台"
echo "  4. 等待构建"
echo "  5. 下载 APK"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${YELLOW}📋 快速选择指南${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

echo -e "${GREEN}最快（5 分钟）：${NC}"
echo "  使用在线工具: ${GREEN}https://www.pwabuilder.com${NC}"
echo ""

echo -e "${GREEN}最可靠（推荐）：${NC}"
echo "  使用 GitHub Actions 自动构建"
echo ""

echo -e "${GREEN}最灵活：${NC}"
echo "  在有 Java 环境的机器上本地构建"
echo ""

echo -e "${GREEN}最自动化：${NC}"
echo "  使用 CI/CD 服务（AppCenter, Bitrise, Codemagic）"
echo ""

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${YELLOW}📱 当前可用 URL${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo "  PWA URL: ${GREEN}https://crypto-dashboard.loca.lt/dashboard_pwa.html${NC}"
echo "  Manifest: ${GREEN}https://crypto-dashboard.loca.lt/manifest.json${NC}"
echo ""

echo -e "${BLUE}=============================================================================${NC}"