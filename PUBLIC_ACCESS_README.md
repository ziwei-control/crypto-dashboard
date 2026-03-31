# 🌐 Crypto Projects Dashboard 公网访问指南

## ✅ 准备工作已完成

- ✅ Dashboard 网页已创建
- ✅ 本地 HTTP 服务器已启动（端口 8000）
- ✅ 公网隧道脚本已创建

---

## 🚀 启动公网访问

### 方法 1：一键启动（推荐）

```bash
cd /root/.copaw/crypto_projects
./start_public.sh
```

**输出示例：**
```
=============================================================================
🚀 Crypto Projects Dashboard - 公网访问启动
=============================================================================

[1/2] 检查本地 HTTP 服务器...
✅ 本地服务器已在运行 (端口 8000)
[2/2] 测试本地服务...
✅ 本地服务正常 (HTTP 200)

=============================================================================
🌐 本地服务已就绪，启动公网隧道...
=============================================================================

提示：
  - 隧道启动后，会显示一个公网 URL
  - 复制该 URL 在浏览器中访问
  - 在 URL 后加上 /dashboard.html 访问仪表板
  - 按 Ctrl+C 可关闭隧道

=============================================================================

Forwarding HTTP traffic from https://abcde1234.serveo.net
```

**访问地址：** `https://abcde1234.serveo.net/dashboard.html`

---

### 方法 2：手动启动隧道

```bash
cd /root/.copaw/crypto_projects
./serveo_tunnel.sh
```

或者直接使用 SSH：
```bash
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:localhost:8000 serveo.net
```

---

### 方法 3：使用其他隧道服务

#### 使用 localtunnel
```bash
# 安装（如果需要）
npm install -g localtunnel

# 启动隧道
lt --port 8000 --subdomain crypto-dashboard
```
访问：`https://crypto-dashboard.loca.lt/dashboard.html`

#### 使用 ngrok
```bash
# 启动隧道
ngrok http 8000
```

---

## 📋 管理命令

### 检查服务状态
```bash
# 检查本地服务器
netstat -tuln | grep 8000

# 测试本地访问
curl -I http://localhost:8000/dashboard.html

# 查看服务器日志
tail -f /tmp/http_server.log
```

### 停止服务
```bash
# 停止本地服务器
pkill -f "python3 -m http.server 8000"

# 或手动查找并 kill
ps aux | grep "python3 -m http.server 8000"
kill <PID>
```

### 重启服务
```bash
cd /root/.copaw/crypto_projects
pkill -f "python3 -m http.server 8000"
nohup python3 -m http.server 8000 > /tmp/http_server.log 2>&1 &
```

---

## 📱 访问说明

### 本地访问
```
http://localhost:8000/dashboard.html
```

### 公网访问（通过 Serveo）
```
https://<随机名称>.serveo.net/dashboard.html
```

示例：
```
https://abcde1234.serveo.net/dashboard.html
https://xyz789.serveo.net/dashboard.html
```

---

## ⚠️ 注意事项

1. **隧道是临时的**
   - 关闭 SSH 连接后，URL 会失效
   - 每次重新启动，URL 会变化

2. **保持连接运行**
   - 隧道需要保持终端窗口打开
   - 或者使用 `nohup` 后台运行：
     ```bash
     nohup ./serveo_tunnel.sh > /tmp/serveo.log 2>&1 &
     ```

3. **安全性**
   - 公网访问可能被他人看到
   - 页面中不要显示敏感信息（API Key、私钥等）

4. **流量限制**
   - Serveo 免费版可能有并发限制
   - 建议使用 localtunnel 作为备用方案

---

## 🔍 故障排查

### 问题：隧道启动失败
```bash
# 检查网络连接
ping serveo.net

# 检查 SSH 客户端
which ssh

# 测试 SSH 连接
ssh -o ConnectTimeout=5 serveo.net echo "OK"
```

### 问题：页面无法访问
```bash
# 检查本地服务器
netstat -tuln | grep 8000

# 检查文件是否存在
ls -lh dashboard.html

# 查看服务器日志
tail -20 /tmp/http_server.log
```

### 问题：隧道连接断开
- Serveo 有时会自动断开空闲连接
- 使用 `ServerAliveInterval=60` 保持心跳
- 或者使用 `autossh` 自动重连：
  ```bash
  apt install autossh
  autossh -M 0 -o "ServerAliveInterval 60" -o "ServerAliveCountMax 3" -R 80:localhost:8000 serveo.net
  ```

---

## 📊 页面内容预览

访问公网 URL 后，您将看到：

- ✅ 部署状态：部署成功
- 📊 项目统计：59 个脚本、6 个运行脚本
- 🧪 测试结果：4/6 通过
- 📋 功能模块：8 个立即可用 + 3 个需要配置
- 🚀 快速开始：一键复制命令
- 🎯 示例输出：Alpha Hunter 和 News Market Analyzer
- 🔗 API 数据源：6 个集成 API

---

**🎉 现在您可以运行 `./start_public.sh` 启动公网访问了！**

如有问题，请查看故障排查部分。