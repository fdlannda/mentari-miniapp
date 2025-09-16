# 🤖 Mentari UNPAM Bot - Advanced Edition

Bot Telegram canggih untuk monitoring status forum diskusi di e-learning Mentari UNPAM dengan arsitektur yang modular dan powerful.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Playwright](https://img.shields.io/badge/Playwright-Latest-green.svg)](https://playwright.dev)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-v7.0-blue.svg)](https://core.telegram.org/bots/api)

## ✨ Features

### 🎯 Core Features
- **🔐 Auto Login**: Login otomatis ke sistem Mentari UNPAM dengan penanganan CAPTCHA
- **📊 Forum Monitoring**: Deteksi status forum diskusi untuk semua mata kuliah
- **🚀 Multi-Mode Operation**: Production, Development, dan Debug mode
- **📱 Telegram Interface**: Interface yang user-friendly melalui Telegram Bot
- **🔄 Real-time Progress**: Progress tracking real-time saat proses scraping

### 🛠️ Advanced Features
- **🎥 Visual Analysis**: Screenshot dan video recording untuk debugging
- **⚡ Smart Detection**: Enhanced selector dengan fallback mechanism
- **🔧 Modular Architecture**: Clean separation of concerns
- **📈 Performance Optimized**: Adaptive delays dan retry mechanisms
- **🎨 Rich Formatting**: Pesan hasil yang informatif dan mudah dibaca

### 🔍 Detection Capabilities
- ✅ **Sudah bergabung**: Forum yang sudah diikuti
- 🟡 **Tersedia tapi belum bergabung**: Forum tersedia tapi belum join
- ❌ **Forum belum tersedia**: Forum belum dibuka oleh dosen
- ❔ **Status tidak terdeteksi**: Status yang tidak dapat diidentifikasi

## 🏗️ Arsitektur

```
📁 Project Structure
├── 🎮 scripts/                 # Scripts untuk management
│   └── bot_controller.py       # Advanced mode controller
├── 📚 src/                     # Source code utama
│   ├── 🧠 core/                # Core business logic
│   │   └── bot_service.py      # Main bot service
│   ├── ⚙️ config/              # Configuration management
│   │   └── __init__.py         # App settings & environment
│   ├── 📋 models/              # Data models & types
│   │   └── __init__.py         # Core data structures
│   └── 🔧 services/            # Service layer
│       ├── auth_service.py     # Authentication service
│       ├── forum_scraper.py    # Forum scraping service
│       ├── captcha_solver.py   # CAPTCHA solving service
│       └── result_formatter.py # Result formatting service
├── 📖 docs/                    # Documentation
├── 📊 data/                    # Data files
│   └── courses.json            # Course configuration
├── 🖼️ screenshots/             # Analysis screenshots
├── 🎬 recordings/              # Session recordings
└── 📄 Core Files
    ├── main.py                 # Telegram bot entry point
    ├── helper.py               # Telegram helpers
    └── requirements.txt        # Dependencies
```

## 🚀 Quick Start

### 1. 📥 Installation

```bash
# Clone repository
git clone <repository_url>
cd Unmentari

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. ⚙️ Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env dengan credentials Anda
# TELEGRAM_TOKEN=your_telegram_bot_token
# CAPTCHA_API_KEY=your_2captcha_api_key
```

### 3. 🎮 Operation Modes

#### 🏃‍♂️ Production Mode (Recommended untuk daily use)
```bash
python scripts/bot_controller.py production
python scripts/bot_controller.py run
```
**Features**: Fast execution, headless browser, minimal resource usage

#### 👁️ Development Mode (Untuk analisis)
```bash
python scripts/bot_controller.py development  
python scripts/bot_controller.py run
```
**Features**: Visible browser, screenshots, video recording, monitoring

#### 🐛 Debug Mode (Untuk troubleshooting)
```bash
python scripts/bot_controller.py debug
python scripts/bot_controller.py run
```
**Features**: Manual pauses, detailed logging, step-by-step analysis

### 4. 📋 Mode Management

```bash
# Lihat status saat ini
python scripts/bot_controller.py status

# Lihat mode yang tersedia
python scripts/bot_controller.py modes

# Konfigurasi custom
python scripts/bot_controller.py config

# Reset ke default
python scripts/bot_controller.py reset
```

## 🎯 Usage

### 📱 Telegram Commands

1. **Start bot**: `/start`
2. **Send credentials**: 
   ```
   NIM: 20220123456
   Password: yourpassword
   ```
3. **Receive results**: Bot akan mengirim laporan lengkap status forum

### 📊 Sample Output

```
📚 LAPORAN STATUS FORUM DISKUSI
════════════════════════════════════════

📚 STATISTIKA DAN PROBABILITAS
  ✅ Pertemuan 1: Sudah bergabung
  🟡 Pertemuan 2: Tersedia tapi belum bergabung
  ❌ Pertemuan 3: Forum belum tersedia

📚 SISTEM BERKAS
  ✅ Pertemuan 1: Sudah bergabung
  ✅ Pertemuan 2: Sudah bergabung

════════════════════════════════════════
📊 RINGKASAN STATUS:
✅ Sudah bergabung: 3
🟡 Tersedia belum gabung: 1
❌ Belum tersedia: 1
📈 Tingkat keberhasilan: 100.0%
⏱️ Waktu eksekusi: 45.2 detik
```

## 🔧 Advanced Configuration

### 📝 Course Configuration

Edit `data/courses.json` untuk mengubah mata kuliah yang di-monitor:

```json
[
  {
    "code": "course-code-here",
    "name": "NAMA MATA KULIAH",
    "meetings": [1, 2, 3, 4, 5]
  }
]
```

### 🎛️ Mode Customization

```bash
# Interactive configuration
python scripts/bot_controller.py config

# Pilihan yang tersedia:
# - Headless/Headed mode
# - Screenshot capture
# - Video recording  
# - Performance delays
# - Error handling
```

### 📁 Output Files

- **Screenshots**: `screenshots/forum_*.png` - Visual evidence
- **Videos**: `recordings/session_*.webm` - Full sessions  
- **Logs**: `data/logs/bot.log` - Detailed logging
- **Config**: `bot_config.json` - Current settings

## 🛠️ Development

### 🏗️ Core Components

1. **MentariBotCore**: Main orchestrator
2. **MentariLoginService**: Authentication handling
3. **ForumScraperService**: Forum status detection
4. **ResultFormatterService**: Output formatting
5. **CaptchaSolverService**: CAPTCHA automation

### 🔄 Service Flow

```
User Input → Telegram Bot → MentariBotCore 
    ↓
LoginService → CAPTCHA Solver → Auth Success
    ↓  
ScraperService → Forum Detection → Status Analysis
    ↓
FormatterService → Rich Output → User Response
```

### 🎯 Extension Points

- **New Authentication Methods**: Extend `auth_service.py`
- **Enhanced Detection**: Modify `forum_scraper.py` selectors
- **Custom Output Formats**: Update `result_formatter.py`
- **Additional Services**: Add to `src/services/`

## 🐛 Troubleshooting

### Common Issues

1. **Login Fails**:
   ```bash
   python scripts/bot_controller.py debug
   # Check screenshots for CAPTCHA or form issues
   ```

2. **Detection Issues**:
   ```bash
   python scripts/bot_controller.py development
   # Enable screenshots to see page content
   ```

3. **Performance Problems**:
   ```bash
   python scripts/bot_controller.py production
   # Use headless mode for better performance
   ```

### 📊 Diagnostic Tools

- **Status Check**: `python scripts/bot_controller.py status`
- **Mode Switch**: Change mode untuk different debugging levels
- **Screenshot Analysis**: Check visual evidence in screenshots/
- **Log Analysis**: Review detailed logs in data/logs/

## 📈 Performance Tips

1. **Production Use**: Always use production mode untuk daily monitoring
2. **Development**: Use development mode untuk analysis dan improvements
3. **Debugging**: Use debug mode hanya untuk investigating issues
4. **Network**: Ensure stable internet connection untuk consistent results
5. **Resources**: Close unnecessary applications saat running debug mode

## 🔐 Security

- ✅ Credentials encrypted in transit
- ✅ No credential storage in logs
- ✅ Environment variable isolation
- ✅ Secure API key management
- ✅ Browser sandbox isolation

## 📄 License

This project is for educational purposes only. Please comply with your institution's terms of service.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 🙋‍♂️ Support

Untuk pertanyaan, issues, atau suggestions:

1. **Issues**: Open GitHub issue dengan detail lengkap
2. **Screenshots**: Include screenshots jika ada UI problems
3. **Logs**: Attach relevant log files untuk debugging
4. **Configuration**: Share mode dan settings yang digunakan

---

**Happy monitoring! 🚀**
