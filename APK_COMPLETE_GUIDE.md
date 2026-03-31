# 📱 APK 构建完整指南

## ✅ 已完成的工作

### 1. Capacitor 项目初始化
- ✅ 创建了 Capacitor 配置文件
- ✅ 添加了 Android 平台
- ✅ 复制了 Web 资源到 www 目录
- ✅ 配置了应用信息

### 2. 项目结构
```
crypto_projects/
├── www/                          # Web 资源
│   ├── index.html               # PWA 网页
│   ├── manifest.json            # PWA 清单
│   ├── sw.js                    # Service Worker
│   └── icons/                   # 应用图标
├── android/                     # Android 项目
│   ├── app/
│   ├── gradle/
│   ├── gradlew                  # Gradle 构建脚本
│   └── build.gradle             # 构建配置
├── capacitor.config.json        # Capacitor 配置
├── package.json                 # NPM 配置
└── node_modules/                # NPM 依赖
```

---

## 🎯 两种构建 APK 的方法

### 方法 1：使用在线工具（推荐，5 分钟完成）

#### 步骤：

1. **打开 PWABuilder**
   ```
   访问: https://www.pwabuilder.com
   ```

2. **输入 PWA URL**
   ```
   URL: https://crypto-dashboard.loca.lt/dashboard_pwa.html
   ```

3. **选择平台**
   ```
   点击 "Package for Android"
   ```

4. **等待构建**
   ```
   大约需要 2-5 分钟
   ```

5. **下载 APK**
   ```
   点击下载按钮，保存 APK 文件
   ```

6. **安装到手机**
   ```
   传输到手机，安装即可
   ```

#### 优点：
- ✅ 无需安装 Java
- ✅ 无需配置环境
- ✅ 快速简单
- ✅ 自动签名

---

### 方法 2：本地构建（需要 Java JDK）

#### 步骤：

1. **安装 Java JDK**
   ```bash
   apt update
   apt install -y openjdk-21-jdk
   ```

2. **配置环境变量**
   ```bash
   export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
   export PATH=$JAVA_HOME/bin:$PATH
   ```

3. **验证安装**
   ```bash
   java -version
   ```

4. **构建 APK**
   ```bash
   cd /root/.copaw/crypto_projects/android
   ./gradlew assembleDebug
   ```

5. **查找 APK**
   ```
   位置: android/app/build/outputs/apk/debug/app-debug.apk
   ```

6. **下载到本地**
   ```bash
   # 使用 scp 或其他工具下载 APK 文件
   ```

---

## 📱 安装 APK 到手机

### 通过 USB 传输：

1. **启用 USB 调试**
   ```
   手机设置 → 关于手机 → 连续点击"版本号" 7 次
   返回设置 → 开发者选项 → 启用"USB 调试"
   ```

2. **连接手机**
   ```
   使用 USB 数据线连接电脑
   ```

3. **传输 APK**
   ```
   将 APK 文件复制到手机存储
   ```

4. **安装**
   ```
   在手机文件管理器中找到 APK
   点击安装
   允许未知来源安装
   ```

---

### 通过浏览器下载：

1. **上传 APK 到服务器**
   ```bash
   # 将 APK 上传到可公开访问的位置
   cp android/app/build/outputs/apk/debug/app-debug.apk /root/.copaw/crypto_projects/
   ```

2. **在手机浏览器下载**
   ```
   访问 APK 的下载链接
   ```

3. **安装**
   ```
   点击下载的 APK 文件
   允许安装
   ```

---

## 📋 APK 应用信息

| 属性 | 值 |
|------|-----|
| 应用名称 | Crypto Dashboard |
| 包名 | com.crypto.dashboard |
| 版本 | 1.0.0 |
| 图标 | Bitcoin (₿) 符号 |
| 主题色 | #667eea (紫色) |
| 最小 SDK | Android 5.0 (API 21) |
| 目标 SDK | Android 14 (API 34) |

---

## 🔐 签名 APK（用于发布）

### 生成签名密钥：
```bash
keytool -genkey -v -keystore crypto-dashboard.keystore \
  -alias crypto-dashboard-key \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000
```

### 配置签名：
编辑 `android/app/build.gradle`，添加：
```gradle
android {
    signingConfigs {
        release {
            storeFile file("crypto-dashboard.keystore")
            storePassword "your-password"
            keyAlias "crypto-dashboard-key"
            keyPassword "your-password"
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }
}
```

### 构建发布版本：
```bash
cd android
./gradlew assembleRelease
```

---

## 🎯 推荐操作

### 快速方案（推荐）：
```
使用 PWABuilder 在线工具
https://www.pwabuilder.com
```

### 本地方案（高级）：
```
安装 Java JDK 后本地构建
apt install openjdk-21-jdk
```

---

## 📊 项目文件

| 文件 | 路径 |
|------|------|
| Web 资源 | `/root/.copaw/crypto_projects/www/` |
| Android 项目 | `/root/.copaw/crypto_projects/android/` |
| 配置文件 | `/root/.copaw/crypto_projects/capacitor.config.json` |
| 构建脚本 | `/root/.copaw/crypto_projects/android/gradlew` |

---

## ✅ 总结

### 已完成：
- ✅ PWA 转换（manifest.json, sw.js, icons）
- ✅ Capacitor 项目初始化
- ✅ Android 平台添加
- ✅ Web 资源准备

### 待完成：
- ⚠️ 安装 Java JDK（如果本地构建）
- ⚠️ 构建 APK 文件
- ⚠️ 签名 APK（可选，用于发布）

---

## 🚀 现在可以做什么？

### 方案 A：在线构建（推荐）
1. 访问 https://www.pwabuilder.com
2. 输入 PWA URL
3. 下载 APK
4. 安装到手机

### 方案 B：本地构建
1. 安装 Java JDK
2. 运行构建命令
3. 下载 APK
4. 安装到手机

---

**🎉 Capacitor 项目已准备就绪！您可以选择在线构建或本地构建 APK 文件。**