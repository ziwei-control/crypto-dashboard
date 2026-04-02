# 📤 推送到 GitHub 自动构建 APK 指南

## 📍 项目位置

```
/home/admin/projects/crypto-dashboard/
```

---

## ✅ 已完成

- ✅ 项目已克隆到本地
- ✅ GitHub Actions 工作流已创建 (`.github/workflows/build-apk.yml`)
- ✅ Git 提交已完成

---

## 🔐 需要配置 GitHub 认证

### 方法 1: 使用 SSH 密钥 (推荐)

**1. 复制 SSH 公钥**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAURHiZestvzS9Md5rlLG9g8VUFsBmzGhzFWywxE179a pandaco-20260401
```

**2. 添加到 GitHub**
1. 访问：https://github.com/settings/keys
2. 点击 **"New SSH key"**
3. 粘贴上面的公钥
4. 点击 **"Add SSH key"**

**3. 推送代码**
```bash
cd /home/admin/projects/crypto-dashboard
git push origin master
```

---

### 方法 2: 使用 Personal Access Token

**1. 生成 Token**
1. 访问：https://github.com/settings/tokens
2. 点击 **"Generate new token (classic)"**
3. 勾选权限：**`repo`** (全部子选项)
4. 点击 **"Generate token"**
5. 复制生成的 token (只显示一次！)

**2. 推送代码**
```bash
cd /home/admin/projects/crypto-dashboard
git push https://YOUR_TOKEN@github.com/ziwei-control/crypto-dashboard.git master
```

替换 `YOUR_TOKEN` 为你的实际 token。

---

## 🚀 推送后自动构建

推送成功后，GitHub Actions 会自动：

1. ✅ 检出代码
2. ✅ 安装 Node.js 和 Java
3. ✅ 安装依赖
4. ✅ 同步 Capacitor
5. ✅ 构建 APK
6. ✅ 上传 APK 为 artifact

---

## 📥 下载构建的 APK

### 方法 1: Actions 页面

1. 访问：https://github.com/ziwei-control/crypto-dashboard/actions
2. 点击最新的构建
3. 在 **"Artifacts"** 部分下载 `app-debug.apk`

### 方法 2: 创建 Release (推送标签时)

```bash
# 创建标签
git tag v1.0.0
git push origin v1.0.0
```

会自动创建 Release 并附加 APK 文件。

---

## 📋 GitHub Actions 工作流配置

文件位置：`.github/workflows/build-apk.yml`

```yaml
name: Build Android APK

on:
  push:
    branches: [ master, main ]
  pull_request:
    branches: [ master, main ]
  workflow_dispatch:  # 允许手动触发

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Set up Java
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
      
      - name: Install dependencies
        run: |
          npm install
          npm install -g @capacitor/cli
      
      - name: Sync Capacitor
        run: |
          npx cap sync android
      
      - name: Grant execute permission for gradlew
        run: chmod +x android/gradlew
      
      - name: Build APK with Gradle
        run: |
          cd android
          ./gradlew assembleDebug
      
      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: app-debug
          path: android/app/build/outputs/apk/debug/app-debug.apk
```

---

## 🧪 测试构建

推送后访问：
```
https://github.com/ziwei-control/crypto-dashboard/actions
```

查看构建状态和日志。

---

## 📞 常见问题

### Q: 推送失败 "Permission denied"
**A**: 需要添加 SSH 公钥到 GitHub，或使用 Personal Access Token。

### Q: 构建失败 "Java not found"
**A**: 工作流已自动安装 Java，检查构建日志。

### Q: APK 在哪里下载？
**A**: Actions 页面 → 最新构建 → Artifacts → app-debug.apk

### Q: 如何手动触发构建？
**A**: Actions 页面 → "Build Android APK" → "Run workflow"

---

## ✅ 总结

**项目位置**: `/home/admin/projects/crypto-dashboard/`

**下一步**:
1. 添加 SSH 公钥到 GitHub **或** 生成 Personal Access Token
2. 推送代码：`git push origin master`
3. 等待 GitHub Actions 自动构建
4. 下载 APK：Actions → Artifacts

**构建触发条件**:
- ✅ 推送到 master/main 分支
- ✅ 创建 Pull Request
- ✅ 手动触发 (workflow_dispatch)
- ✅ 推送标签 (自动创建 Release)
