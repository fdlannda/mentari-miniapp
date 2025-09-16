# 🎯 UNIFIED MENTARI UNPAM BOT - PANDUAN LENGKAP

## 📋 Overview

**Aplikasi unified** menggabungkan Telegram Bot dan Mini App Server dalam **satu aplikasi tunggal** (`main_unified.py`), sehingga Anda tidak perlu menjalankan dua service terpisah.

### ❌ Sebelum (Separate Services):
```
Terminal 1: python main.py          # Bot service
Terminal 2: python miniapp_server.py # Mini App server
```

### ✅ Sekarang (Unified Application):
```
Terminal 1: python main_unified.py  # Bot + Mini App dalam satu aplikasi
```

---

## 🏗️ Architecture Unified

```
main_unified.py
├── 🤖 Telegram Bot (Async)
│   ├── Command handlers (/start)
│   ├── Message handlers (credentials)
│   ├── Callback handlers (Mini App info)
│   └── Mini App integration
│
└── 🌐 Flask Web Server (Thread)
    ├── Mini App interface (/)
    ├── Health endpoint (/health)
    ├── Join API (/api/join-forum)
    └── CORS support
```

**Benefits:**
- ✅ Satu aplikasi, satu proses
- ✅ Shared configuration & logging
- ✅ Easier deployment & monitoring
- ✅ Resource efficient

---

## 🚀 Quick Start

### Method 1: Automated Setup (Recommended)

```bash
# 1. Run automated setup
python run_unified.py

# Script will:
# - Check & install requirements
# - Create config template
# - Start unified application
```

### Method 2: Manual Setup

```bash
# 1. Install dependencies
pip install flask flask-cors python-telegram-bot playwright

# 2. Install Playwright browsers
playwright install chromium

# 3. Configure bot
# Edit bot_config.json dengan tokens Anda

# 4. Run unified application
python main_unified.py
```

---

## 🔧 Configuration

### bot_config.json
```json
{
  "telegram_token": "YOUR_BOT_TOKEN",
  "captcha_api_key": "YOUR_CAPTCHA_API_KEY"
}
```

### Environment Variables (Optional)
```bash
# Mini App settings
export MINIAPP_URL="https://your-domain.com"
export MINIAPP_BOT_NAME="mentari_unpam"

# Flask settings
export FLASK_HOST="0.0.0.0"
export FLASK_PORT="5000"
export FLASK_DEBUG="False"

# Logging
export LOG_LEVEL="INFO"
```

---

## 🧪 Testing Unified Application

### 1. Start Application
```bash
python main_unified.py
```

**Expected Output:**
```
🚀 UNIFIED MENTARI UNPAM BOT + MINI APP
==================================================
🤖 Bot Token: ✅ Configured
🌐 Mini App URL: https://localhost:5000
🔧 Flask Host: 0.0.0.0:5000
==================================================
2025-01-XX - INFO - Starting Unified Mentari UNPAM Bot + Mini App Server
2025-01-XX - INFO - Flask server thread started
2025-01-XX - INFO - Starting Telegram bot...
2025-01-XX - INFO - Bot application created and configured
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://[::1]:5000
```

### 2. Test Bot Functionality
```
1. Send /start ke bot
2. Send credentials: username|password  
3. Bot akan show Mini App buttons
4. Klik Mini App button untuk test
```

### 3. Test Mini App Directly
```bash
# Health check
curl http://localhost:5000/health

# Mini App interface
curl http://localhost:5000

# Response should show HTML interface
```

---

## 📁 File Structure Unified

```
📦 Project Root
├── main_unified.py           # 🎯 MAIN APPLICATION (Bot + Mini App)
├── run_unified.py           # 🚀 Quick setup & run script
├── bot_config.json          # 🔧 Bot configuration
├── helper.py                # 🛠️ Helper functions
├── src/integrations/        # 📚 Mini App logic
│   └── telegram_miniapp.py
├── logs/                    # 📝 Application logs
│   └── unified_bot.log
└── requirements.txt         # 📦 Dependencies
```

**Key Files:**
- `main_unified.py` - **Single application** yang menjalankan bot dan web server
- `run_unified.py` - **Automated setup** script dengan dependency checking
- `bot_config.json` - **Configuration** file untuk tokens

---

## 🔄 How It Works

### 1. Application Startup
```python
# main_unified.py startup sequence:
1. Load configuration (bot_config.json + env vars)
2. Initialize logging
3. Create Flask app dengan Mini App HTML
4. Start Flask server dalam background thread
5. Create Telegram bot application
6. Start bot polling
7. Both services run simultaneously
```

### 2. User Interaction Flow
```
User → Send credentials → Bot processes → Shows Mini App buttons
User → Click Mini App → Opens web interface → Join forum → Success
```

### 3. Mini App Integration
```python
# Dalam satu aplikasi:
- Bot detects available forums
- Generates Mini App URLs dengan HMAC security
- Flask server serves Mini App interface
- API endpoint handles forum joining
- Real-time updates via Telegram Web App API
```

---

## 🐳 Docker Deployment

### Updated Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y curl
COPY requirements_production.txt .
RUN pip install --no-cache-dir -r requirements_production.txt
RUN playwright install chromium

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 miniapp && chown -R miniapp:miniapp /app
USER miniapp

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run unified application
CMD ["python", "main_unified.py"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  unified-bot:
    build: .
    container_name: mentari_unified_bot
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
      - CAPTCHA_API_KEY=${CAPTCHA_API_KEY}
      - MINIAPP_URL=https://your-domain.com
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Deploy dengan Docker
```bash
# Build and run
docker-compose up -d

# Check logs  
docker-compose logs -f unified-bot

# Check health
curl http://localhost:5000/health
```

---

## 🔧 Production Configuration

### 1. Update URLs for Production
```python
# In main_unified.py, line ~60:
self.mini_app_url = "https://mentari-miniapp.yourdomain.com"
```

### 2. Environment Variables
```bash
# .env file
TELEGRAM_TOKEN=your_real_bot_token
CAPTCHA_API_KEY=your_captcha_key
MINIAPP_URL=https://mentari-miniapp.yourdomain.com
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
LOG_LEVEL=INFO
```

### 3. Bot Father Setup
```
1. Contact @BotFather
2. /setmenubutton your_bot_name
3. Set Mini App URL: https://mentari-miniapp.yourdomain.com
4. Test with real bot
```

---

## 🎯 Advantages of Unified Approach

### ✅ Pros
- **Single Process**: Easier management & monitoring
- **Shared Resources**: Common logging, config, error handling
- **Simplified Deployment**: One Docker container
- **Resource Efficient**: Lower memory & CPU usage
- **Easier Development**: Single codebase untuk debugging

### ⚠️ Considerations
- **Single Point of Failure**: Bot crash affects Mini App too
- **Threading Complexity**: Flask runs dalam thread
- **Resource Contention**: Heavy Mini App usage could affect bot

### 🎛️ When to Use Each

**Use Unified (`main_unified.py`) when:**
- Development & testing
- Small to medium usage
- Simple deployment requirements
- Resource constraints

**Use Separate Services when:**
- High traffic production
- Need independent scaling
- Microservices architecture
- Different deployment environments

---

## 🆘 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using port 5000
   netstat -an | findstr :5000
   
   # Change port in environment
   export FLASK_PORT=5001
   ```

2. **Bot Token Error**
   ```bash
   # Check bot_config.json
   cat bot_config.json
   
   # Verify token with BotFather
   ```

3. **Mini App Not Loading**
   ```bash
   # Test direct access
   curl http://localhost:5000
   
   # Check logs
   tail -f logs/unified_bot.log
   ```

4. **Import Errors**
   ```bash
   # Install missing packages
   pip install -r requirements.txt
   
   # Check Python path
   python -c "import sys; print(sys.path)"
   ```

---

## 🎉 Ready to Run!

### Quick Commands Summary

```bash
# Quick start (automated)
python run_unified.py

# Manual start
python main_unified.py

# Docker deployment
docker-compose up -d

# Health check
curl http://localhost:5000/health

# Stop application
Ctrl+C (manual) or docker-compose down (Docker)
```

---

**🎯 Result: Single unified application yang menjalankan Telegram Bot + Mini App Server bersamaan!** 🚀