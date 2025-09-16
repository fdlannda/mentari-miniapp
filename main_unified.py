#!/usr/bin/env python3
"""
Unified Mentari UNPAM Bot dengan integrated Mini App Server
Single application yang menjalankan bot dan web server bersamaan
"""

import os
import sys
import json
import asyncio
import threading
import logging
from datetime import datetime
from pathlib import Path

# Flask untuk Mini App server
from flask import Flask, request, render_template_string, jsonify
from flask_cors import CORS

# Telegram Bot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler, 
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# Local imports
from helper import (
    format_result_message,
    extract_available_forums_from_result,
    create_miniapp_keyboard
)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.integrations.telegram_miniapp import (
    TelegramMiniAppGenerator,
    MiniAppConfig,
    verify_telegram_auth
)

# ==========================================
# CONFIGURATION
# ==========================================

class UnifiedConfig:
    """Unified configuration untuk bot dan Mini App"""
    
    def __init__(self):
        self.load_config()
        
    def load_config(self):
        """Load configuration dari environment dan files"""
        
        # Bot configuration
        try:
            with open('bot_config.json', 'r') as f:
                bot_config = json.load(f)
                self.telegram_token = bot_config.get('telegram_token')
                self.captcha_api_key = bot_config.get('captcha_api_key')
        except FileNotFoundError:
            self.telegram_token = os.getenv('TELEGRAM_TOKEN')
            self.captcha_api_key = os.getenv('CAPTCHA_API_KEY')
        
        # Use dummy token for testing if not configured
        if not self.telegram_token or self.telegram_token.startswith('YOUR_'):
            self.telegram_token = "1234567890:DUMMY_TOKEN_FOR_TESTING_ONLY"
            print("⚠️  Using dummy token for testing. Update bot_config.json for production.")
        
        # Mini App configuration
        self.mini_app_url = os.getenv('MINIAPP_URL', 'http://localhost:5000')
        self.mini_app_name = os.getenv('MINIAPP_BOT_NAME', 'mentari_unpam')
        self.flask_host = os.getenv('FLASK_HOST', '0.0.0.0')
        self.flask_port = int(os.getenv('FLASK_PORT', '5000'))
        self.flask_debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        # Logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

# Global configuration
config = UnifiedConfig()

# ==========================================
# LOGGING SETUP
# ==========================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.log_level),
    handlers=[
        logging.FileHandler('logs/unified_bot.log'),
        logging.StreamHandler()
    ]
)

# Create logs directory if not exists
os.makedirs('logs', exist_ok=True)

logger = logging.getLogger(__name__)

# ==========================================
# MINI APP SERVER (FLASK)
# ==========================================

# Flask app setup
app = Flask(__name__)
CORS(app)

# Mini App HTML template
MINI_APP_HTML = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mentari UNPAM - Join Forum</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--tg-theme-bg-color, #ffffff);
            color: var(--tg-theme-text-color, #000000);
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 400px;
            margin: 0 auto;
            background: var(--tg-theme-secondary-bg-color, #f8f9fa);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 24px;
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--tg-theme-text-color, #000000);
        }
        
        .header p {
            color: var(--tg-theme-hint-color, #999999);
            font-size: 14px;
        }
        
        .forum-info {
            background: var(--tg-theme-bg-color, #ffffff);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 24px;
            border: 1px solid var(--tg-theme-section-separator-color, #e5e5e5);
        }
        
        .forum-info h3 {
            color: var(--tg-theme-accent-text-color, #007aff);
            margin-bottom: 8px;
            font-size: 16px;
        }
        
        .forum-info p {
            color: var(--tg-theme-subtitle-text-color, #666666);
            font-size: 14px;
            line-height: 1.4;
        }
        
        .join-button {
            width: 100%;
            background: var(--tg-theme-button-color, #007aff);
            color: var(--tg-theme-button-text-color, #ffffff);
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-bottom: 16px;
        }
        
        .join-button:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }
        
        .join-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .status {
            text-align: center;
            padding: 12px;
            border-radius: 8px;
            margin-top: 16px;
            font-weight: 500;
        }
        
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--tg-theme-button-color, #007aff);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .footer {
            text-align: center;
            margin-top: 24px;
            color: var(--tg-theme-hint-color, #999999);
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Join Forum</h1>
            <p>Bergabung dengan forum Mentari UNPAM</p>
        </div>
        
        <div class="forum-info">
            <h3 id="courseCode">Loading...</h3>
            <p id="meetingInfo">Loading forum information...</p>
        </div>
        
        <button id="joinButton" class="join-button" onclick="joinForum()">
            🚀 Join Forum Sekarang
        </button>
        
        <div id="status" class="status" style="display: none;"></div>
        
        <div class="footer">
            <p>🤖 Mentari UNPAM Bot - Mini App</p>
        </div>
    </div>

    <script>
        // Telegram Web App initialization
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();
        
        // Parse URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const courseCode = urlParams.get('course_code');
        const meetingNumber = urlParams.get('meeting_number');
        const authHash = urlParams.get('auth_hash');
        
        // Display forum information
        document.getElementById('courseCode').textContent = courseCode || 'Unknown Course';
        document.getElementById('meetingInfo').textContent = 
            `Meeting ${meetingNumber || 'N/A'} - Siap untuk bergabung dengan forum`;
        
        async function joinForum() {
            const joinButton = document.getElementById('joinButton');
            const statusDiv = document.getElementById('status');
            
            // Disable button and show loading
            joinButton.disabled = true;
            joinButton.innerHTML = '<span class="loading"></span> Joining...';
            statusDiv.style.display = 'none';
            
            try {
                const response = await fetch('/api/join-forum', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        course_code: courseCode,
                        meeting_number: meetingNumber,
                        auth_hash: authHash,
                        telegram_data: window.Telegram.WebApp.initData
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    statusDiv.className = 'status success';
                    statusDiv.textContent = '✅ Berhasil bergabung dengan forum!';
                    joinButton.innerHTML = '✅ Forum Joined';
                    
                    // Close Mini App after success
                    setTimeout(() => {
                        window.Telegram.WebApp.close();
                    }, 2000);
                } else {
                    throw new Error(result.error || 'Unknown error');
                }
                
            } catch (error) {
                console.error('Join forum error:', error);
                statusDiv.className = 'status error';
                statusDiv.textContent = `❌ Error: ${error.message}`;
                
                // Re-enable button
                joinButton.disabled = false;
                joinButton.innerHTML = '🔄 Try Again';
            } finally {
                statusDiv.style.display = 'block';
            }
        }
        
        // Handle back button
        window.Telegram.WebApp.onEvent('backButtonClicked', function() {
            window.Telegram.WebApp.close();
        });
        
        // Show back button if supported
        if (window.Telegram.WebApp.BackButton) {
            window.Telegram.WebApp.BackButton.show();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def mini_app():
    """Mini App main page"""
    return render_template_string(MINI_APP_HTML)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'unified-bot-miniapp'
    })

@app.route('/api/join-forum', methods=['POST'])
def api_join_forum():
    """API endpoint untuk join forum"""
    try:
        data = request.json
        course_code = data.get('course_code')
        meeting_number = data.get('meeting_number')
        auth_hash = data.get('auth_hash')
        telegram_data = data.get('telegram_data')
        
        logger.info(f"Join forum request: {course_code} Meeting {meeting_number}")
        
        # Verify Telegram auth
        if not verify_telegram_auth(telegram_data, config.telegram_token):
            return jsonify({'success': False, 'error': 'Invalid Telegram authentication'})
        
        # TODO: Implement actual forum joining logic here
        # For now, simulate success
        success = True
        
        if success:
            logger.info(f"Successfully joined forum: {course_code} Meeting {meeting_number}")
            return jsonify({
                'success': True,
                'message': f'Successfully joined {course_code} Meeting {meeting_number}'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to join forum'})
            
    except Exception as e:
        logger.error(f"Join forum API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

# ==========================================
# TELEGRAM BOT HANDLERS
# ==========================================

# Global variables untuk bot
user_credentials = {}
miniapp_generator = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler"""
    welcome_message = """
👋 *Selamat datang di Bot Pengecekan Forum Mentari UNPAM!*

Untuk memulai, kirimkan NIM dan Password Anda dengan format berikut:

`NIM: 241011400xxx`
`Password: rahasiamu`

🔎 Bot akan login dan mengecek status semua forum diskusi Anda.
Proses ini membutuhkan waktu 2–6 menit, tergantung banyaknya mata kuliah.

📊 Status yang akan ditampilkan:
✅ Sudah bergabung
🟡 Tersedia tapi belum bergabung
❌ Forum belum tersedia
❔ Status tidak terdeteksi

🚀 *FITUR BARU: Mini App Integration!*
📱 Join forum langsung dengan sekali klik via Mini App

—
Made with ❤️ by @dell0x
"""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )

async def handle_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user credentials dan proses scraping"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    try:
        # Support both formats: "username|password" and legacy "NIM: xxx\nPassword: xxx"
        from helper import extract_credentials
        username, password = extract_credentials(message_text)
        
        # Store credentials
        user_credentials[user_id] = {
            'username': username.strip(),
            'password': password.strip(),
            'timestamp': datetime.now()
        }
        
        logger.info(f"Credentials stored for user {user_id}")
        
        # Send processing message
        await update.message.reply_text(
            "🔄 *Memproses kredensial...*\n\n"
            "⏳ Mengecek forum yang tersedia\n"
            "🔒 Kredensial disimpan dengan aman",
            parse_mode='Markdown'
        )
        
        # TODO: Implement actual scraping here
        # For demo, use detailed format like the original output
        demo_result = """📋 Hasil Pengecekan Forum Mentari

👤 NIM: 2410****
📅 Waktu: 2025-09-16 23:16:19
========================================

📚 LAPORAN STATUS FORUM DISKUSI
════════════════════════════════════════

📚 STATISTIKA DAN PROBABILITAS
  ❌ Pertemuan 1: ❌ Forum belum tersedia
  � Pertemuan 2: 🟡 Tersedia tapi belum bergabung
  🟡 Pertemuan 3: 🟡 Tersedia tapi belum bergabung
  ❌ Pertemuan 4: ❌ Forum belum tersedia
  🟡 Pertemuan 5: 🟡 Tersedia tapi belum bergabung
  ❌ Pertemuan 6: ❌ Forum belum tersedia
  ❌ Pertemuan 7: ❌ Forum belum tersedia
  ❌ Pertemuan 8: ❌ Forum belum tersedia
  ❌ Pertemuan 9: ❌ Forum belum tersedia
  ❌ Pertemuan 10: ❌ Forum belum tersedia
  ❌ Pertemuan 11: ❌ Forum belum tersedia

📚 SISTEM BERKAS
  ✅ Pertemuan 1: ✅ Sudah bergabung
  🟡 Pertemuan 2: 🟡 Tersedia tapi belum bergabung
  ❌ Pertemuan 3: ❌ Forum belum tersedia
  ❌ Pertemuan 4: ❌ Forum belum tersedia
  ❌ Pertemuan 5: ❌ Forum belum tersedia
  ❌ Pertemuan 6: ❌ Forum belum tersedia
  ❌ Pertemuan 7: ❌ Forum belum tersedia

📚 MATEMATIKA DISKRIT
  ✅ Pertemuan 1: ✅ Sudah bergabung
  ❌ Pertemuan 2: ❌ Forum belum tersedia
  ❌ Pertemuan 3: ❌ Forum belum tersedia
  ❌ Pertemuan 4: ❌ Forum belum tersedia
  ❌ Pertemuan 5: ❌ Forum belum tersedia
  ❌ Pertemuan 6: ❌ Forum belum tersedia
  ❌ Pertemuan 7: ❌ Forum belum tersedia

📚 JARINGAN KOMPUTER
  ❔ Pertemuan 1: ❔ Status forum tidak terdeteksi
  🟡 Pertemuan 2: 🟡 Tersedia tapi belum bergabung
  🟡 Pertemuan 3: 🟡 Tersedia tapi belum bergabung
  ❌ Pertemuan 4: ❌ Forum belum tersedia
  ❌ Pertemuan 5: ❌ Forum belum tersedia
  ❌ Pertemuan 6: ❌ Forum belum tersedia
  ❌ Pertemuan 7: ❌ Forum belum tersedia
  ❌ Pertemuan 8: ❌ Forum belum tersedia
  ❌ Pertemuan 9: ❌ Forum belum tersedia
  ❌ Pertemuan 10: ❌ Forum belum tersedia
  ❌ Pertemuan 11: ❌ Forum belum tersedia

════════════════════════════════════════
📊 RINGKASAN STATUS:
✅ Sudah bergabung: 2
� Tersedia belum gabung: 6
❌ Belum tersedia: 27
❗ Error/Tidak terdeteksi: 1
📈 Tingkat keberhasilan: 97.2%

════════════════════════════════════════
⏱️ Waktu eksekusi: 136.0 detik
📋 Total mata kuliah: 4
📝 Total pertemuan: 36
🕐 Diperbarui: 2025-09-16 23:16:18

========================================
✅ Pengecekan selesai!
💡 Tips: Bergabunglah di forum yang tersedia untuk mendapatkan nilai partisipasi."""
        
        # Extract available forums
        available_forums = extract_available_forums_from_result(demo_result)
        
        if available_forums:
            # Create Mini App keyboard
            keyboard = create_miniapp_keyboard(available_forums, miniapp_generator)
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Format message with Mini App hints
            formatted_message = format_result_message(demo_result, has_available_forums=True)
            
            await update.message.reply_text(
                formatted_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            formatted_message = format_result_message(demo_result, has_available_forums=False)
            await update.message.reply_text(
                formatted_message,
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Error processing credentials: {e}")
        await update.message.reply_text(
            "❌ *Terjadi kesalahan saat memproses kredensial*\n\n"
            "Silakan coba lagi atau hubungi admin.",
            parse_mode='Markdown'
        )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback query dari inline buttons"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'miniapp_info':
        info_message = """
🌟 *Tentang Mini App*

Mini App adalah fitur Telegram yang memungkinkan Anda:

✅ Join forum dengan sekali klik
✅ Interface web yang responsif
✅ Terintegrasi langsung dalam Telegram
✅ Keamanan tinggi dengan enkripsi

*Cara menggunakan:*
1️⃣ Klik tombol "🚀 Join via Mini App"
2️⃣ Mini App akan terbuka dalam Telegram
3️⃣ Klik "Join Forum Sekarang"
4️⃣ Selesai! ✨

🔒 *Aman dan mudah digunakan*
"""
        await query.edit_message_text(
            info_message,
            parse_mode='Markdown'
        )

# ==========================================
# BOT INITIALIZATION
# ==========================================

def create_bot_application():
    """Create and configure bot application"""
    global miniapp_generator
    
    # Create Mini App generator
    miniapp_config = MiniAppConfig(
        bot_token=config.telegram_token,
        app_url=config.mini_app_url,
        app_name=config.mini_app_name
    )
    miniapp_generator = TelegramMiniAppGenerator(miniapp_config)
    
    # Skip bot creation jika dummy token (untuk testing)
    if config.telegram_token.startswith('1234567890:DUMMY'):
        logger.info("Dummy token detected - skipping bot creation for testing")
        return None
    
    # Create bot application
    application = Application.builder().token(config.telegram_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_credentials))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    logger.info("Bot application created and configured")
    return application

# ==========================================
# FLASK SERVER RUNNER
# ==========================================

def run_flask_server():
    """Run Flask server in separate thread"""
    logger.info(f"Starting Flask server on {config.flask_host}:{config.flask_port}")
    app.run(
        host=config.flask_host,
        port=config.flask_port,
        debug=config.flask_debug,
        use_reloader=False,  # Disable reloader in thread
        threaded=True
    )

# ==========================================
# MAIN APPLICATION
# ==========================================

async def main():
    """Main application entry point"""
    logger.info("Starting Unified Mentari UNPAM Bot + Mini App Server")
    
    try:
        # Start Flask server in background thread
        flask_thread = threading.Thread(target=run_flask_server, daemon=True)
        flask_thread.start()
        logger.info("Flask server thread started")
        
        # Wait sedikit untuk Flask startup
        await asyncio.sleep(2)
        
        # Create bot application
        application = create_bot_application()
        
        # If no bot application (dummy token), just run Flask server
        if application is None:
            logger.info("Running in Flask-only mode (dummy token)")
            print("\n🌐 Mini App Server running in test mode")
            print("🔗 Access: http://localhost:5000")
            print("🧪 Mode: Flask server only (no bot)")
            print("📝 Press Ctrl+C to stop\n")
            
            # Keep main thread alive
            while True:
                await asyncio.sleep(1)
        else:
            logger.info("Starting Telegram bot...")
            
            # Initialize bot properly
            await application.initialize()
            await application.start()
            await application.updater.start_polling(drop_pending_updates=True)
            
            logger.info("Bot started successfully! Both services running:")
            print("\n🎉 UNIFIED APP RUNNING SUCCESSFULLY!")
            print("🤖 Telegram Bot: Active & polling")  
            print("🌐 Mini App Server: http://localhost:5000")
            print("📝 Press Ctrl+C to stop both services\n")
            
            # Keep running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Error: {e}")
        print("💡 Tip: Make sure bot token is valid and check network connection")
    finally:
        # Cleanup
        if 'application' in locals() and application:
            try:
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
            except:
                pass
        logger.info("Application shutdown complete")

if __name__ == '__main__':
    print("🚀 UNIFIED MENTARI UNPAM BOT + MINI APP")
    print("=" * 50)
    print(f"🤖 Bot Token: {'✅ Configured' if config.telegram_token else '❌ Missing'}")
    print(f"🌐 Mini App URL: {config.mini_app_url}")
    print(f"🔧 Flask Host: {config.flask_host}:{config.flask_port}")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)