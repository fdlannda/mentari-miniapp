
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
