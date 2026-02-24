# 论文分析系统 - 部署指南

## 📋 准备清单

### VPS 要求

- **操作系统**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **配置**: 最低 2 核 4GB，推荐 4 核 8GB
- **存储**: 最低 20GB，推荐 50GB+
- **网络**: 稳定的公网 IP

### 软件要求

- Docker 20.10+
- Docker Compose 2.0+
- Git
- Nginx (可选)

---

## 🚀 一键部署脚本

### 1. 安装 Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker-compose --version
```

### 2. 克隆项目

```bash
# 创建项目目录
sudo mkdir -p /opt/paper-analysis
sudo chown $USER:$USER /opt/paper-analysis

# 克隆代码
cd /opt/paper-analysis
git clone <your-repo-url> .
cd deploy
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
nano .env
```

重要配置项：

```env
# ⚠️ 必须修改！生成一个随机密钥
SECRET_KEY=$(openssl rand -hex 32)

# LLM API 配置
LLM_API_KEY=your-deepseek-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# 域名
DOMAIN=papers.velorislab.com
```

### 4. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 5. 配置域名和 SSL

#### 方式 1：使用容器内的 Nginx（推荐）

```bash
# 获取 SSL 证书
sudo apt install certbot

# 使用 standalone 模式获取证书
sudo certbot certonly --standalone -d papers.velorislab.com

# 复制证书到项目目录
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/papers.velorislab.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/papers.velorislab.com/privkey.pem ssl/
sudo chown $USER:$USER ssl/*

# 启动生产环境（包含 Nginx）
docker-compose --profile production up -d
```

#### 方式 2：使用外部 Nginx

```bash
# 安装 Nginx
sudo apt install nginx certbot python3-certbot-nginx

# 创建配置文件
sudo nano /etc/nginx/sites-available/papers
```

Nginx 配置：

```nginx
server {
    listen 80;
    server_name papers.velorislab.com;
    
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name papers.velorislab.com;

    ssl_certificate /etc/letsencrypt/live/papers.velorislab.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/papers.velorislab.com/privkey.pem;

    client_max_body_size 100M;

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location / {
        proxy_pass http://localhost:4321;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/papers /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 获取 SSL 证书
sudo certbot --nginx -d papers.velorislab.com
```

---

## 🔧 配置优化

### 1. 防火墙设置

```bash
# Ubuntu UFW
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable
```

### 2. 设置自动重启

编辑 `/etc/systemd/system/paper-analysis.service`:

```ini
[Unit]
Description=Paper Analysis System
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/paper-analysis/web
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl enable paper-analysis
sudo systemctl start paper-analysis
```

### 3. 日志轮转

创建 `/etc/logrotate.d/paper-analysis`:

```
/opt/paper-analysis/web/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

### 4. 自动备份

创建备份脚本 `/opt/paper-analysis/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/paper-analysis/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
docker cp huginn-backend:/app/data/paper_analysis.db \
    $BACKUP_DIR/db_$DATE.db

# 备份上传文件
docker cp huginn-backend:/app/uploads \
    $BACKUP_DIR/uploads_$DATE

# 压缩
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz \
    $BACKUP_DIR/db_$DATE.db \
    $BACKUP_DIR/uploads_$DATE

# 清理旧备份（保留 7 天）
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +7 -delete

# 清理临时文件
rm -rf $BACKUP_DIR/db_$DATE.db $BACKUP_DIR/uploads_$DATE
```

```bash
# 添加到 crontab
chmod +x /opt/paper-analysis/backup.sh
crontab -e
# 每天凌晨 3 点备份
0 3 * * * /opt/paper-analysis/backup.sh
```

---

## 📊 监控和维护

### 1. 健康检查

```bash
# 检查所有容器状态
docker-compose ps

# 检查服务健康
curl http://localhost:8000/health
curl http://localhost:4321

# 查看资源使用
docker stats
```

### 2. 查看日志

```bash
# 实时日志
docker-compose logs -f

# 特定服务日志
docker-compose logs -f backend
docker-compose logs -f nginx

# 最近 100 行
docker-compose logs --tail=100
```

### 3. 常用命令

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend

# 停止服务
docker-compose stop

# 完全清理（⚠️ 会删除数据）
docker-compose down -v

# 更新镜像
docker-compose pull
docker-compose up -d --build
```

---

## 🐛 故障排查

### 问题 1: 数据库锁定

```bash
# 进入容器
docker exec -it huginn-backend bash

# 检查数据库
sqlite3 data/paper_analysis.db "PRAGMA integrity_check;"

# 如果损坏，从备份恢复
docker cp /opt/paper-analysis/backups/latest.db huginn-backend:/app/data/paper_analysis.db
docker-compose restart backend
```

### 问题 4: 磁盘空间不足

```bash
# 检查磁盘使用
df -h

# 清理 Docker 资源
docker system prune -a
docker volume prune

# 清理日志
sudo journalctl --vacuum-time=7d
```

### 问题 5: SSL 证书过期

```bash
# 手动续期
sudo certbot renew

# 重新加载 Nginx
sudo systemctl reload nginx
```

---

## 🔒 安全建议

1. **修改默认端口**：不要暴露 8000 端口到公网
2. **使用强密码**：SECRET_KEY 必须是随机的 32 字符以上
3. **限制上传大小**：防止恶意文件占用存储
4. **定期更新**：及时更新 Docker 镜像和系统
5. **启用 HTTPS**：强制使用 SSL 加密
6. **配置防火墙**：只开放必要的端口
7. **监控日志**：定期检查异常访问

---

## 📈 性能优化

### 1. 数据库优化

切换到 PostgreSQL（生产推荐）：

```yaml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: paper_analysis
    POSTGRES_USER: paper
    POSTGRES_PASSWORD: ${DB_PASSWORD}
  volumes:
    - postgres_data:/var/lib/postgresql/data

backend:
  environment:
    - DATABASE_URL=postgresql+asyncpg://paper:${DB_PASSWORD}@postgres/paper_analysis
```

---

## ✅ 部署检查清单

- [ ] Docker 和 Docker Compose 已安装
- [ ] 环境变量已配置（SECRET_KEY, LLM_API_KEY）
- [ ] 域名 DNS 已解析到服务器 IP
- [ ] SSL 证书已获取并配置
- [ ] 防火墙规则已设置
- [ ] 自动备份脚本已配置
- [ ] 日志轮转已设置
- [ ] 监控告警已配置（可选）
- [ ] 所有服务健康检查通过
- [ ] 已测试文件上传和论文分析功能

---

## 📞 支持

遇到问题？

1. 查看日志：`docker-compose logs -f`
2. 检查文档：`/docs/` 目录
3. 提交 Issue

---

**祝部署顺利！🎉**
