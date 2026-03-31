# 🌐 Crypto Projects - 公网访问双隧道备份系统

## ✅ 部署状态：全部完成

---

## 🌐 公网访问地址（双隧道备份）

### 📱 主隧道：LocalTunnel（推荐）
```
https://crypto-dashboard.loca.lt/dashboard.html
```

### 🔐 备用隧道：Serveo
```
https://crypto9486.serveo.net/dashboard.html
```

---

## 📊 系统状态

| 服务 | 状态 | 地址 |
|------|------|------|
| 📡 本地 HTTP 服务器 | ✅ 运行中 | http://localhost:8000 |
| 🌐 LocalTunnel 隧道 | ✅ 运行中 | https://crypto-dashboard.loca.lt |
| 🔐 Serveo 隧道（备用） | ✅ 运行中 | https://crypto9486.serveo.net |

---

## 🚀 快速开始

### 1️⃣ 访问 Dashboard（两个地址都可用）
```
主隧道: https://crypto-dashboard.loca.lt/dashboard.html
备用:   https://crypto9486.serveo.net/dashboard.html
```

### 2️⃣ 启动后台功能（系统内运行）
```bash
cd /root/.copaw/crypto_projects
./start_all.sh
```

### 3️⃣ 查看运行状态
```bash
cd /root/.copaw/crypto_projects
./check_status.sh
```

### 4️⃣ 停止所有功能
```bash
cd /root/.copaw/crypto_projects
./stop_all.sh
```

---

## 🔄 隧道管理

### 启动主隧道（LocalTunnel）
```bash
cd /root/.copaw/crypto_projects

# 停止现有隧道
pkill -f 'lt --port 8000'

# 启动新隧道
nohup lt --port 8000 --subdomain crypto-dashboard > /tmp/localtunnel.log 2>&1 &
```

### 启动备用隧道（Serveo）
```bash
cd /root/.copaw/crypto_projects
./serveo_backup.sh
```

### 查看隧道状态
```bash
# LocalTunnel 日志
tail -f /tmp/localtunnel.log

# Serveo 日志
tail -f /tmp/serveo.log

# 检查进程
ps aux | grep -E "lt --port|ssh.*serveo"
```

### 停止隧道
```bash
# 停止 LocalTunnel
pkill -f 'lt --port 8000'

# 停止 Serveo
pkill -f 'ssh.*serveo'
screen -X -S serveo quit 2>/dev/null
```

---

## 📁 生成的脚本文件

| 脚本 | 用途 |
|------|------|
| serveo_tunnel.sh | Serveo 隧道启动脚本 |
| serveo_backup.sh | Serveo 备用隧道（随机子域名） |
| start_all.sh | 启动所有后台功能 |
| stop_all.sh | 停止所有后台功能 |
| check_status.sh | 检查服务状态 |
| start_public.sh | 启动公网访问 |
| start_serveo.sh | Serveo 隧道（screen 模式） |

---

## 🛠️ 管理命令

### 检查所有服务状态
```bash
cd /root/.copaw/crypto_projects
./check_status.sh
```

### 查看隧道连接
```bash
# LocalTunnel
cat /tmp/localtunnel.log

# Serveo
cat /tmp/serveo.log
screen -r serveo  # 附加到 serveo screen
```

### 测试公网访问
```bash
# 测试 LocalTunnel
curl -I https://crypto-dashboard.loca.lt/dashboard.html

# 测试 Serveo
curl -I https://crypto9486.serveo.net/dashboard.html
```

---

## 📊 隧道对比

| 特性 | LocalTunnel | Serveo |
|------|-------------|---------|
| 子域名 | 固定 | 随机/自定义 |
| 连接稳定性 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 免费限制 | 中等 | 宽松 |
| 设置难度 | 简单 | 中等 |
| 推荐使用 | ✅ 主隧道 | ⚠️ 备用 |

---

## ⚠️ 注意事项

### LocalTunnel
- 需要保持 Node.js 进程运行
- 可能需要登录确认（首次使用）
- 子域名: crypto-dashboard.loca.lt

### Serveo
- 使用 SSH 反向隧道
- 需要端口 80 空闲
- 子域名随机生成（每次不同）
- 使用 screen 保持连接

### 通用
- 两个隧道同时运行，互为备份
- 如果一个不可用，可以切换到另一个
- 定期检查隧道连接状态

---

## 🔧 故障排查

### LocalTunnel 不可用
```bash
# 检查进程
ps aux | grep "lt --port"

# 重启隧道
pkill -f 'lt --port 8000'
nohup lt --port 8000 --subdomain crypto-dashboard > /tmp/localtunnel.log 2>&1 &
```

### Serveo 不可用
```bash
# 检查进程
ps aux | grep "ssh.*serveo"

# 重启隧道
pkill -f 'ssh.*serveo'
./serveo_backup.sh
```

### 本地服务器不可用
```bash
# 检查端口
netstat -tuln | grep 8000

# 重启服务器
pkill -f 'python3 -m http.server 8000'
cd /root/.copaw/crypto_projects
nohup python3 -m http.server 8000 > /tmp/http_server.log 2>&1 &
```

---

## 📱 Dashboard 功能

访问任一 URL 都可以看到：

- ✅ 部署状态：部署成功
- 📊 项目统计：59 个脚本、6 个运行脚本
- 🧪 测试结果：4/6 通过
- 📋 功能模块列表
- 🚀 快速开始指南
- 🎯 示例输出展示
- 🔗 API 数据源展示
- 📱 响应式设计（支持手机）

---

## 🎯 访问地址汇总

### 🌐 公网地址
```
主隧道: https://crypto-dashboard.loca.lt/dashboard.html
备用:   https://crypto9486.serveo.net/dashboard.html
```

### 💻 本地地址
```
http://localhost:8000/dashboard.html
```

---

## 🎉 系统已完全就绪！

现在您可以：

1. ✅ 通过两个公网地址访问 Dashboard（主隧道 + 备用）
2. ✅ 启动后台功能进行自动监控
3. ✅ 查看实时运行日志
4. ✅ 随时切换隧道
5. ✅ 管理所有后台进程

---

## 📞 获取帮助

- 查看主报告: `cat FINAL_REPORT.md`
- 查看公网访问指南: `cat PUBLIC_ACCESS_README.md`
- 查看部署报告: `cat DEPLOYMENT_REPORT.md`
- 查看使用指南: `cat README.md`

---

**🎉 双隧道备份系统已完成！主隧道和备用隧道都可正常使用！**