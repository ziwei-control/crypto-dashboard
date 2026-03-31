# Crypto Projects Dashboard

加密货币交易策略与工具集合 - PWA Dashboard

## 📱 安装到手机

### PWA 版本
在 Chrome 浏览器中访问：
```
https://crypto-dashboard.loca.lt/dashboard_pwa.html
```

然后选择"添加到主屏幕"即可安装。

### APK 版本
使用 GitHub Actions 自动构建 APK。

## 🚀 本地运行

```bash
# 安装依赖
npm install

# 启动服务器
python3 -m http.server 8000

# 启动公网隧道
lt --port 8000 --subdomain crypto-dashboard
```

## 📊 功能模块

- Alpha Hunter（早期机会发现）
- Smart Gem Scanner（智能宝石扫描）
- News Market Analyzer（新闻情绪分析）
- Polymarket Scanner（预测市场）
- 等等...

## 📝 构建 APK

### 自动构建

推送代码到 GitHub 后，GitHub Actions 会自动构建 APK。

### 本地构建

在有 Java 环境的机器上：

```bash
cd android
./gradlew assembleDebug
```

APK 文件位置：
```
android/app/build/outputs/apk/debug/app-debug.apk
```

## 🔗 公网访问

- 主隧道: https://crypto-dashboard.loca.lt/dashboard.html
- 备用: https://crypto0176.serveo.net/dashboard.html

## 📄 许可证

MIT License