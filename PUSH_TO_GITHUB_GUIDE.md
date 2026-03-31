# 📤 推送到 GitHub 指南

## ✅ 已完成的步骤

### Git 初始化和提交

| 步骤 | 状态 |
|------|------|
| Git 仓库初始化 | ✅ 完成 |
| 添加 PWA 文件 | ✅ 完成 |
| 添加 Android 配置 | ✅ 完成 |
| 添加 GitHub Actions workflow | ✅ 完成 |
| Git 提交 | ✅ 完成 |

---

## 🚀 推送到 GitHub 的步骤

### 步骤 1：创建 GitHub 仓库

1. **访问 GitHub**
   ```
   https://github.com/new
   ```

2. **创建新仓库**
   ```
   Repository name: crypto-dashboard
   Description: Crypto Projects Dashboard - PWA with Android APK
   选择: Public 或 Private
   不要: Initialize with README
   点击: "Create repository"
   ```

3. **复制仓库 URL**
   ```
   类似: https://github.com/your-username/crypto-dashboard.git
   ```

---

### 步骤 2：推送代码到 GitHub

在终端执行以下命令：

```bash
cd /root/.copaw/crypto_projects

# 添加远程仓库（替换为您的仓库 URL）
git remote add origin https://github.com/your-username/crypto-dashboard.git

# 推送到 GitHub
git push -u origin master
```

**如果需要认证：**
```bash
git push -u origin master
```
然后输入您的 GitHub 用户名和密码（或个人访问令牌）

---

### 步骤 3：验证推送

访问您的 GitHub 仓库页面，应该能看到：
- README.md
- .github/workflows/build-apk.yml
- manifest.json
- dashboard_pwa.html
- icons/
- android/

---

## 🔐 GitHub 认证方式

### 方式 1：HTTPS + 密码

```bash
git push -u origin master
Username: <your-github-username>
Password: <your-github-personal-access-token>
```

**注意：** GitHub 不再支持密码，需要使用个人访问令牌（Personal Access Token）。

### 方式 2：SSH 密钥

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 添加密钥到 GitHub
# 复制 ~/.ssh/id_ed25519.pub 的内容到 GitHub Settings → SSH keys

# 使用 SSH 推送
git remote set-url origin git@github.com:your-username/crypto-dashboard.git
git push -u origin master
```

### 方式 3：GitHub CLI（推荐）

```bash
# 认证
gh auth login

# 推送到 GitHub
gh repo create crypto-dashboard --public --source=. --remote=origin
git push -u origin master
```

---

## 📋 GitHub Actions 自动构建

推送代码后，GitHub Actions 会自动构建 APK。

### 触发构建

推送代码后会自动触发：
```bash
git add .
git commit -m "Update code"
git push
```

### 查看构建进度

1. **访问 GitHub 仓库**
2. **点击 "Actions" 标签**
3. **查看 "Build Android APK" workflow**
4. **等待构建完成**

### 下载 APK

1. **在 GitHub Actions 页面**
2. **点击最新的 workflow run**
3. **滚动到 "Artifacts" 部分**
4. **下载 "app-debug.apk" 或 "app-release.apk"**

---

## 📱 下载并安装 APK

### 从 GitHub Actions 下载

1. **访问 Actions 页面**
   ```
   https://github.com/your-username/crypto-dashboard/actions
   ```

2. **选择最新的 workflow run**

3. **下载 Artifacts**
   - app-debug.apk (调试版本)
   - app-release.apk (发布版本)

### 安装到手机

1. **传输 APK 到手机**
   - USB 数据线
   - 邮件
   - 云盘

2. **安装 APK**
   - 点击 APK 文件
   - 允许未知来源安装
   - 等待安装完成

---

## 🔧 配置说明

### GitHub Token（如需）

如果遇到认证问题，使用个人访问令牌：

1. **生成 Token**
   ```
   GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   Generate new token (classic)
   勾选: repo, workflow
   生成并复制 token
   ```

2. **使用 Token**
   ```
   git push -u origin master
   Username: your-github-username
   Password: your-personal-access-token
   ```

---

## 📊 推送命令总结

### 完整命令

```bash
# 1. 进入项目目录
cd /root/.copaw/crypto_projects

# 2. 添加远程仓库（替换为您的仓库 URL）
git remote add origin https://github.com/your-username/crypto-dashboard.git

# 3. 推送到 GitHub
git push -u origin master

# 4. 或者使用 GitHub CLI
gh auth login
gh repo create crypto-dashboard --public --source=. --remote=origin
git push -u origin master
```

---

## ✅ 检查清单

### 推送前检查

- [x] Git 仓库已初始化
- [x] 所有 PWA 文件已添加
- [x] Android 配置已添加
- [x] GitHub Actions workflow 已添加
- [x] Git 提交已完成
- [ ] GitHub 仓库已创建
- [ ] 远程仓库 URL 已配置
- [ ] 推送到 GitHub

### 推送后检查

- [ ] GitHub 仓库已更新
- [ ] GitHub Actions 已触发
- [ ] APK 构建成功
- [ ] APK 可以下载
- [ ] APK 可安装到手机

---

## 🎯 下一步

推送成功后：

1. **查看 GitHub Actions 构建**
   ```
   https://github.com/your-username/crypto-dashboard/actions
   ```

2. **等待构建完成**
   - 通常需要 5-10 分钟

3. **下载 APK**
   - 从 Actions 页面下载

4. **安装到手机**
   - 传输并安装 APK

---

## 💡 替代方案

如果无法推送到 GitHub，可以使用：

### 方案 A：GitLab

```bash
# 创建 GitLab 仓库
# 推送到 GitLab
git remote add origin https://gitlab.com/your-username/crypto-dashboard.git
git push -u origin master
```

### 方案 B：直接使用在线构建工具

```
https://www.pwabuilder.com
输入: https://crypto-dashboard.loca.lt/dashboard_pwa.html
```

---

**🎉 所有文件已准备完成并提交！现在只需要推送到 GitHub，GitHub Actions 会自动构建 APK！**