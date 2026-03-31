# 🌐 Crypto Projects Dashboard - 公网访问指南

## ✅ 本地服务器已启动

- **端口**: 8000
- **文件**: dashboard.html
- **状态**: 运行中 ✅

---

## 🌐 公网访问方法

### 方法 1：使用 Serveo 隧道（推荐）

```bash
cd /root/.copaw/crypto_projects

# 启动隧道
./serveo_tunnel.sh
```

**等待输出类似：**
```
Forwarding HTTP traffic from https://random-name.serveo.net
```

复制显示的 `https://random-name.serveo.net` 地址，在浏览器中访问。

---

### 方法 2：手动启动 Serveo 隧道

```bash
cd /root/.copaw/crypto_projects

# 启动隧道（一直保持运行）
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:localhost:8000 serveo.net
```

**输出示例：**
```
Forwarding HTTP traffic from https://abcde.serveo.net
Press Ctrl+C to close the tunnel
```

访问显示的 `https://abcde.serveo.net/dashboard.html`

---

### 方法 3：使用 ngrok（需要先安装）

```bash
# 安装 ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# 启动隧道
ngrok http 8000
```

复制 ngrok 显示的公网 URL。

---

### 方法 4：使用 localtunnel（推荐）

```bash
# 安装 localtunnel
npm install -g localtunnel

# 启动隧道
lt --port 8000
```

---

## 🛠️ 常用命令

### 检查本地服务器状态
```bash
# 检查端口是否监听
netstat -tuln | grep 8000

# 测试本地访问
curl -I http://localhost:8000/dashboard.html
```

### 停止本地服务器
```bash
# 查找进程
ps aux | grep "python3 -m http.server 8000"

# 停止进程（替换 PID）
kill <PID>

# 或者使用
pkill -f "python3 -m http.server 8000"
```

### 重启本地服务器
```bash
cd /root/.copaw/crypto_projects
pkill -f "python3 -m http.server 8000"
nohup python3 -m http.server 8000 > /tmp/http_server.log 2>&1 &
```

---

## ⚠️ 注意事项

1. **Serveo 隧道是临时的**：每次关闭 SSH 连接，URL 会变化
2. **保持连接运行**：隧道需要保持终端窗口打开或使用 `nohup` 后台运行
3. **安全性**：公网访问可能被他人看到，请勿在页面中显示敏感信息
4. **流量限制**：免费版 Serveo 可能有并发连接限制

---

## 🚀 一键启动脚本

创建一个自动启动本地服务器和隧道的脚本：

```bash
#!/bin/bash
# 一键启动 Dashboard 公网访问

cd /root/.copaw/crypto_projects

# 检查本地服务器是否运行
if ! netstat -tuln | grep -q ":8000"; then
    echo "🚀 启动本地 HTTP 服务器..."
    nohup python3 -m http.server 8000 > /tmp/http_server.log 2>&1 &
    sleep 2
    echo "✅ 本地服务器已启动 (端口 8000)"
else
    echo "✅ 本地服务器已在运行"
fi

# 测试本地访问
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/dashboard.html | grep -q "200"; then
    echo "✅ 本地服务正常"
else
    echo "❌ 本地服务异常"
    exit 1
fi

# 启动 Serveo 隧道
echo ""
echo "🌐 启动 Serveo 公网隧道..."
echo "=========================================="
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:localhost:8000 serveo.net
```

保存为 `start_public.sh`，然后运行：
```bash
chmod +x start_public.sh
./start_public.sh
```

---

## 📱 访问演示

启动隧道后，在浏览器中访问：

```
https://<随机名称>.serveo.net/dashboard.html
```

页面内容：
- 🎯 部署状态
- 📊 项目统计
- 🧪 测试结果
- 📋 功能模块列表
- 🚀 快速开始指南
- 🎨 API 数据源展示

---

**祝使用愉快！🚀**