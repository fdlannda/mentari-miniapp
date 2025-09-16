#!/usr/bin/env python3
"""
Production Deployment Script untuk Telegram Mini App
Script untuk setup dan deploy Mini App ke production
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def create_production_config():
    """Create production configuration files"""
    
    print("🔧 Creating production configuration...")
    
    # nginx.conf template
    nginx_config = """
# Nginx configuration untuk Mini App production
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Certificate paths (update dengan path yang sesuai)
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (jika diperlukan future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Static files (jika ada)
    location /static/ {
        alias /var/www/miniapp/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
"""
    
    with open("nginx_miniapp.conf", "w") as f:
        f.write(nginx_config)
    
    # systemd service file
    systemd_service = """
[Unit]
Description=Mentari UNPAM Mini App Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/miniapp
Environment=PATH=/var/www/miniapp/venv/bin
Environment=FLASK_ENV=production
ExecStart=/var/www/miniapp/venv/bin/python miniapp_server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    
    with open("miniapp.service", "w") as f:
        f.write(systemd_service)
    
    # requirements.txt untuk production
    requirements = """
flask==3.1.2
flask-cors==6.0.1
gunicorn==23.0.0
requests==2.32.5
python-telegram-bot==22.2
playwright==1.50.0
asyncio
"""
    
    with open("requirements_production.txt", "w") as f:
        f.write(requirements)
    
    # Docker Dockerfile
    dockerfile = """
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements_production.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_production.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 miniapp && chown -R miniapp:miniapp /app
USER miniapp

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:5000/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "miniapp_server:app"]
"""
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile)
    
    # Docker Compose
    docker_compose = """
version: '3.8'

services:
  miniapp:
    build: .
    container_name: mentari_miniapp
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
      - CAPTCHA_API_KEY=${CAPTCHA_API_KEY}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: mentari_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx_miniapp.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - miniapp
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(docker_compose)
    
    print("✅ Production configuration files created:")
    print("   📄 nginx_miniapp.conf")
    print("   📄 miniapp.service") 
    print("   📄 requirements_production.txt")
    print("   📄 Dockerfile")
    print("   📄 docker-compose.yml")

def create_deployment_guide():
    """Create step-by-step deployment guide"""
    
    guide = """
# 🚀 Telegram Mini App - Production Deployment Guide

## 📋 Prerequisites

### 1. Domain & SSL
- Domain: `mentari-miniapp.yourdomain.com`
- SSL Certificate (Let's Encrypt recommended)
- DNS A record pointing to server IP

### 2. Server Requirements
- Ubuntu 20.04+ / CentOS 7+
- Python 3.9+
- Nginx
- 2GB RAM minimum
- 10GB storage

## 🛠️ Deployment Methods

### Method 1: Docker (Recommended)

```bash
# 1. Clone repository
git clone <your-repo>
cd mentari-miniapp

# 2. Create environment file
cp .env.example .env
# Edit .env dengan credentials yang sesuai

# 3. Update domain di nginx_miniapp.conf
sed -i 's/your-domain.com/mentari-miniapp.yourdomain.com/g' nginx_miniapp.conf

# 4. Setup SSL certificates
mkdir ssl
# Copy certificate.crt dan private.key ke ssl/

# 5. Deploy dengan Docker Compose
docker-compose up -d

# 6. Verify deployment
curl https://mentari-miniapp.yourdomain.com/health
```

### Method 2: Manual Installation

```bash
# 1. Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements_production.txt

# 3. Install Playwright browsers
playwright install chromium

# 4. Setup systemd service
sudo cp miniapp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable miniapp
sudo systemctl start miniapp

# 5. Setup Nginx
sudo cp nginx_miniapp.conf /etc/nginx/sites-available/miniapp
sudo ln -s /etc/nginx/sites-available/miniapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 6. Setup SSL dengan Let's Encrypt
sudo certbot --nginx -d mentari-miniapp.yourdomain.com
```

## 🔧 Configuration

### 1. Update Bot Configuration

Edit `helper.py`:
```python
config = MiniAppConfig(
    bot_token=env_config.telegram_token,
    app_url="https://mentari-miniapp.yourdomain.com",  # Update this
    app_name="mentari_unpam"
)
```

### 2. Environment Variables

Create `.env` file:
```bash
TELEGRAM_TOKEN=your_bot_token
CAPTCHA_API_KEY=your_2captcha_key
MENTARI_BASE_URL=https://mentari.unpam.ac.id
FLASK_ENV=production
```

### 3. Bot Father Setup

1. Contact @BotFather
2. `/setmenubutton` your_bot_name
3. Set Web App URL: `https://mentari-miniapp.yourdomain.com`

## 🧪 Testing

### 1. Health Check
```bash
curl https://mentari-miniapp.yourdomain.com/health
```

### 2. Mini App Test
```bash
curl "https://mentari-miniapp.yourdomain.com?action=join_forum&course_code=test&meeting_number=1&auth_hash=test"
```

### 3. Telegram Integration Test
1. Send credentials to bot
2. Check for Mini App buttons
3. Test join functionality

## 📊 Monitoring

### 1. Logs
```bash
# Docker
docker-compose logs -f miniapp

# Systemd
sudo journalctl -u miniapp -f
```

### 2. Performance
```bash
# Check server status
systemctl status miniapp nginx

# Monitor resources
htop
df -h
```

### 3. SSL Certificate
```bash
# Check certificate expiry
openssl x509 -in ssl/certificate.crt -text -noout | grep "Not After"
```

## 🔐 Security

### 1. Firewall Setup
```bash
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 2. Fail2Ban (Optional)
```bash
sudo apt install fail2ban
# Configure untuk protect against brute force
```

### 3. Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Mini App
git pull
docker-compose down && docker-compose up -d
```

## 🎯 Production Checklist

- [ ] Domain configured dengan SSL
- [ ] Bot credentials dalam .env
- [ ] Mini App server running
- [ ] Nginx configured dan running
- [ ] Health endpoint responding
- [ ] Bot Father Web App URL updated
- [ ] Test dengan real Telegram bot
- [ ] Monitoring setup
- [ ] Backup procedures in place
- [ ] Security measures implemented

## 🆘 Troubleshooting

### Common Issues

1. **SSL Certificate Error**
   ```bash
   sudo certbot renew --dry-run
   ```

2. **Mini App Not Loading**
   - Check Telegram requires HTTPS
   - Verify domain DNS
   - Check server logs

3. **Bot Not Showing Buttons**
   - Verify app_url in helper.py
   - Check bot credentials
   - Test forum detection logic

### Support
- Check logs: `docker-compose logs miniapp`
- Test health: `curl domain.com/health`
- Verify SSL: `curl -I https://domain.com`

---

🎉 **Deployment Complete!** 
Your Telegram Mini App is now live and ready for production use!
"""
    
    with open("DEPLOYMENT_GUIDE.md", "w", encoding='utf-8') as f:
        f.write(guide)
    
    print("✅ Deployment guide created: DEPLOYMENT_GUIDE.md")

def update_production_config():
    """Update bot configuration untuk production"""
    
    print("🔧 Updating bot configuration for production...")
    
    # Create production helper update
    production_update = """
# Production Configuration Update

# File: helper.py
# Update line ~165:

config = MiniAppConfig(
    bot_token=env_config.telegram_token,
    app_url=os.getenv('MINIAPP_URL', 'https://mentari-miniapp.yourdomain.com'),
    app_name=os.getenv('MINIAPP_BOT_NAME', 'mentari_unpam')
)

# File: .env (add these lines):
MINIAPP_URL=https://mentari-miniapp.yourdomain.com
MINIAPP_BOT_NAME=mentari_unpam
"""
    
    with open("PRODUCTION_UPDATE.md", "w", encoding='utf-8') as f:
        f.write(production_update)
    
    print("✅ Production update guide created: PRODUCTION_UPDATE.md")

def main():
    """Main deployment preparation function"""
    
    print("🚀 TELEGRAM MINI APP - PRODUCTION DEPLOYMENT PREP")
    print("=" * 60)
    
    create_production_config()
    print()
    create_deployment_guide()
    print()
    update_production_config()
    
    print("\n" + "=" * 60)
    print("🎉 DEPLOYMENT PREPARATION COMPLETED!")
    print("=" * 60)
    
    print("\n📁 Generated Files:")
    print("   📄 nginx_miniapp.conf - Nginx configuration")
    print("   📄 miniapp.service - Systemd service") 
    print("   📄 requirements_production.txt - Python dependencies")
    print("   📄 Dockerfile - Container configuration")
    print("   📄 docker-compose.yml - Multi-service setup")
    print("   📄 DEPLOYMENT_GUIDE.md - Step-by-step deployment")
    print("   📄 PRODUCTION_UPDATE.md - Configuration updates")
    
    print("\n🎯 Next Steps:")
    print("   1. Get domain & SSL certificate")
    print("   2. Setup server (Ubuntu 20.04+ recommended)")
    print("   3. Follow DEPLOYMENT_GUIDE.md")
    print("   4. Update app_url in helper.py")
    print("   5. Test dengan real Telegram bot")
    
    print("\n🔗 Quick Links:")
    print("   📚 Full Guide: DEPLOYMENT_GUIDE.md")
    print("   🐳 Docker: docker-compose up -d")
    print("   🔧 Manual: Follow systemd + nginx steps")
    print("   🧪 Test: curl https://your-domain.com/health")

if __name__ == "__main__":
    main()