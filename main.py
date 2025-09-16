from typing import Optional, Callable, Awaitable, Any
import os
import sys
import asyncio
import socket
import logging
import json
from datetime import datetime
import nest_asyncio
import httpx
import certifi
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Fix Windows encoding for emoji support
if sys.platform == "win32":
    import codecs
    import io
    try:
        # Type safe encoding fix
        if hasattr(sys.stdout, 'detach') and hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())  # type: ignore
        if hasattr(sys.stderr, 'detach') and hasattr(sys.stderr, 'buffer'):
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())  # type: ignore
    except (AttributeError, io.UnsupportedOperation):
        # Fallback untuk kasus di mana detach tidak tersedia
        pass

# Add src to path for new structure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from helper import extract_credentials, send_result_or_error
from core.bot_service import MentariBotCore
from models import LoginCredentials
from config import env_config, ConfigManager

# Setup agar bisa nested event loop di Windows
nest_asyncio.apply()

# Load variabel dari .env
load_dotenv()
TOKEN = env_config.telegram_token

# Initialize config manager
config_manager = ConfigManager()

# Load config dari file jika ada
try:
    if os.path.exists("bot_config.json"):
        with open("bot_config.json", 'r') as f:
            config_data = json.load(f)
            # Update config dengan data dari file
            if 'delay_between_requests' in config_data:
                config_manager.update_config(
                    delay_between_requests=config_data['delay_between_requests'],
                    delay_between_courses=config_data.get('delay_between_courses', 1.0),
                    headless_mode=config_data.get('headless_mode', True),
                    enable_screenshots=config_data.get('enable_screenshots', False),
                    debug_mode=config_data.get('debug_mode', False),
                    pause_on_error=config_data.get('pause_on_error', False)
                )
    else:
        # Default ke production mode untuk speed
        config_manager.switch_mode('production')
        print("🚀 Using production mode (fast) as default")
except Exception as e:
    print(f"⚠️  Error loading config, using defaults: {e}")
    config_manager.switch_mode('production')

# Get current settings
app_settings = config_manager.config

# Setup logging dengan encoding yang benar
logging.basicConfig(
    level=getattr(logging, env_config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(app_settings.log_dir, 'bot.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure log directory exists
os.makedirs(app_settings.log_dir, exist_ok=True)

# Initialize bot core service
bot_core = MentariBotCore(app_settings)

# Cek apakah koneksi internet / Telegram tersedia
def is_connected():
    try:
        socket.create_connection(("api.telegram.org", 443), timeout=5)
        return True
    except OSError:
        return False

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
        
    logger.info(f"User {update.effective_user.id} started the bot")
    await update.message.reply_text(
        "👋 *Selamat datang di Bot Pengecekan Forum Mentari UNPAM!*\n\n"
        "Untuk memulai, kirimkan *NIM* dan *Password* Anda dengan format berikut:\n\n"
        "`NIM: 241011400xxx`\n`Password: rahasiamu`\n\n"
        "🔎 Bot akan login dan mengecek status semua *forum diskusi* Anda.\n"
        "_Proses ini membutuhkan waktu 2–6 menit, tergantung banyaknya mata kuliah._\n\n"
        "📊 *Status yang akan ditampilkan:*\n"
        "✅ Sudah bergabung\n"
        "🟡 Tersedia tapi belum bergabung\n"
        "❌ Forum belum tersedia\n"
        "❔ Status tidak terdeteksi\n\n"
        "—\nMade with ❤️ by [@dell0x](https://t.me/dell0x)",
        parse_mode="Markdown"
    )

# Command /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
        
    await update.message.reply_text(
        "📖 *Bantuan Bot Forum Mentari*\n\n"
        "*Perintah yang tersedia:*\n"
        "/start - Memulai bot\n"
        "/help - Menampilkan bantuan\n"
        "/status - Status bot\n\n"
        "*Format kredensial:*\n"
        "`NIM: nomor_nim_anda`\n"
        "`Password: password_anda`\n\n"
        "*Catatan:*\n"
        "• Bot membutuhkan waktu 2-6 menit untuk proses\n"
        "• Pastikan NIM dan password benar\n"
        "• Jika ada masalah, hubungi [@dell0x](https://t.me/dell0x)",
        parse_mode="Markdown"
    )

# Command /status  
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
        
    status_msg = f"🤖 *Status Bot*\n\n"
    status_msg += f"📅 Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    status_msg += f"🌐 Koneksi: {'✅ Online' if is_connected() else '❌ Offline'}\n"
    status_msg += f"🔧 Status: Aktif dan siap digunakan"
    
    await update.message.reply_text(status_msg, parse_mode="Markdown")

# Handler untuk pesan berisi kredensial
async def handle_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message or not update.message.text:
        return
        
    user_id = update.effective_user.id
    text = update.message.text
    
    logger.info(f"User {user_id} sent credentials")
    
    if "nim" in text.lower() and "password" in text.lower():
        try:
            nim, pw = extract_credentials(text)
            logger.info(f"Processing login for NIM: {nim[:4]}****")
            
            # Kirim processing message
            processing_msg = await update.message.reply_text(
                "🔄 *Memproses permintaan...*\n\n"
                "Sedang mempersiapkan login ke sistem Mentari UNPAM. "
                "Proses ini akan memakan waktu beberapa menit.",
                parse_mode="Markdown"
            )
            
            # Create credentials object
            credentials = LoginCredentials(nim=nim, password=pw)
            
            # Process login and scrape using new bot core
            async def scrape_function(nim: str, password: str, progress_callback: Optional[Any] = None) -> str:
                return await bot_core.execute_full_scraping(credentials, None, progress_callback)
            
            await send_result_or_error(
                update, context, nim, pw, scrape_function, processing_msg
            )
            
        except ValueError as e:
            logger.warning(f"Invalid format from user {user_id}: {e}")
            await update.message.reply_text(
                f"⚠️ Format tidak valid:\n`{e}`", 
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Unexpected error for user {user_id}: {e}")
            await update.message.reply_text(
                f"⚠️ Terjadi kesalahan tidak terduga:\n`{e}`", 
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            "❌ *Format tidak dikenali.*\n\n"
            "Gunakan format yang benar:\n\n"
            "`NIM: 241011400xxx`\n"
            "`Password: rahasia`\n\n"
            "Ketik /help untuk bantuan lebih lanjut.",
            parse_mode="Markdown"
        )

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # Inform user about error
    if update and hasattr(update, 'message') and hasattr(update, 'message'):
        try:
            message = getattr(update, 'message', None)
            if message and hasattr(message, 'reply_text'):
                await message.reply_text(  # type: ignore
                    "⚠️ Terjadi kesalahan internal. Silakan coba lagi atau hubungi admin.",
                    parse_mode="Markdown"
                )
        except Exception:
            pass

# Callback handler untuk Mini App info
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries dari inline buttons"""
    query = update.callback_query
    
    if not query or not query.data:
        return
    
    await query.answer()
    
    if query.data == "miniapp_info":
        info_text = """
🚀 **Tentang Telegram Mini App**

**Apa itu Mini App?**
Mini App adalah aplikasi web yang terintegrasi langsung dalam Telegram, memberikan pengalaman native untuk join forum Mentari UNPAM.

✨ **Keunggulan:**
• **Instant Access** - Langsung join tanpa switch app
• **Seamless Login** - Otomatis menggunakan kredensial Anda
• **Fast Performance** - Optimized untuk mobile
• **Secure** - Data terenkripsi end-to-end

🎯 **Cara Menggunakan:**
1. Tap tombol "🚀 Join Forum..."
2. Mini App akan terbuka dalam Telegram
3. Konfirmasi join forum
4. Selesai! Anda akan otomatis bergabung

🔒 **Keamanan:**
Data login Anda dienkripsi dan hanya digunakan untuk otentikasi. Tidak ada data yang disimpan di server Mini App.

💡 **Tips:** Mini App bekerja optimal di Telegram versi terbaru.
"""
        
        try:
            await query.edit_message_text(
                info_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Failed to edit message: {e}")
            await query.message.reply_text(info_text, parse_mode="Markdown")
    
    elif query.data == "forum_join_guide":
        guide_text = """
🚀 **Cara Join Forum Mentari UNPAM Manual**

**📱 Via Mobile Browser:**
1. Buka browser di HP (Chrome/Safari)
2. Login ke https://mentari.unpam.ac.id
3. Masukkan NIM dan Password Anda
4. Pilih mata kuliah yang diinginkan
5. Klik "Forum Diskusi"
6. Pilih pertemuan yang tersedia
7. Klik "Bergabung dengan Forum"

**💻 Via Desktop:**
1. Buka https://mentari.unpam.ac.id di browser
2. Login dengan kredensial Anda
3. Navigate ke mata kuliah
4. Akses Forum Diskusi
5. Join pertemuan yang available

**⚡ Tips Cepat:**
• Bookmark halaman forum untuk akses cepat
• Login sekali akan tersimpan di browser
• Forum biasanya update pagi hari
• Jika error, coba refresh halaman

**🔍 Forum yang Terdeteksi Available:**
Bot sudah mendeteksi forum yang bisa di-join. Silakan akses manual sesuai panduan di atas.

💡 **Pro Tip:** Simpan shortcut Mentari UNPAM di homescreen HP untuk akses super cepat!
"""
        
        try:
            await query.edit_message_text(
                guide_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Failed to edit message: {e}")
            await query.message.reply_text(guide_text, parse_mode="Markdown")
    
    elif query.data.startswith("forum_info_"):
        # Extract forum details from callback data
        parts = query.data.split("_")
        if len(parts) >= 4:
            course_code = "_".join(parts[2:-1])
            meeting_number = parts[-1]
            
            forum_detail_text = f"""
📋 **Detail Forum Diskusi**

**📚 Course Code:** `{course_code}`
**📅 Pertemuan:** {meeting_number}
**🟡 Status:** Tersedia tapi belum bergabung

**🚀 Langkah Join Manual:**

1. **Login ke Mentari UNPAM**
   • https://mentari.unpam.ac.id
   • Gunakan NIM dan Password Anda

2. **Navigate ke Course**
   • Cari mata kuliah dengan code: `{course_code}`
   • Klik untuk masuk ke halaman course

3. **Akses Forum Diskusi**
   • Scroll ke bagian "Forum Diskusi"
   • Cari "Pertemuan {meeting_number}"
   • Klik tombol "Bergabung dengan Forum"

4. **Verifikasi**
   • Pastikan status berubah jadi "✅ Sudah bergabung"
   • Forum akan muncul di dashboard Anda

**💡 Tips:**
• Login di browser HP lebih praktis
• Bookmark halaman untuk akses cepat
• Forum diskusi biasanya update pagi hari

Selamat berdiskusi! 🎓
"""
            
            try:
                await query.edit_message_text(
                    forum_detail_text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.warning(f"Failed to edit message: {e}")
                await query.message.reply_text(forum_detail_text, parse_mode="Markdown")
    
    elif query.data == "demo_miniapp_local":
        demo_text = """
🔧 **Demo Mini App (Development)**

**🚨 Mengapa tidak bisa buka Mini App?**

Telegram Mini Apps memerlukan **HTTPS URL** untuk keamanan. URL `localhost:5000` tidak bisa diakses dari dalam Telegram.

**💡 Solusi Development:**

1. **Deploy ke Server HTTPS**
   • Deploy Mini App ke Vercel/Netlify/Railway
   • Dapatkan URL HTTPS (contoh: https://mentari-app.vercel.app)
   • Update URL di helper.py

2. **Test di Browser**
   • Buka: http://localhost:5000
   • Test functionality Mini App
   • Lihat interface dan features

3. **Alternatif sementara: Tunnel Service**
   • Install ngrok: `npm install -g ngrok`
   • Run: `ngrok http 5000`
   • Gunakan HTTPS URL yang diberikan

**🔍 Status Saat Ini:**
✅ Mini App Server: Running di localhost:5000  
✅ Bot Telegram: Active dan responsive
⚠️ HTTPS URL: Diperlukan untuk production

**🎯 Untuk Production:**
Setelah deploy ke HTTPS, Mini App akan berfungsi sempurna untuk join forum otomatis!
"""
        
        try:
            await query.edit_message_text(
                demo_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Failed to edit message: {e}")
            await query.message.reply_text(demo_text, parse_mode="Markdown")# Fungsi utama menjalankan bot
async def main():
    # Set Windows event loop policy
    if sys.platform.startswith("win") and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Check token
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN tidak ditemukan di file .env")
        print("❌ TELEGRAM_TOKEN tidak ditemukan. Buat file .env dan isi TELEGRAM_TOKEN.")
        return

    # Check internet connection
    if not is_connected():
        logger.error("Tidak bisa terhubung ke Telegram")
        print("🚫 Tidak bisa terhubung ke Telegram. Periksa koneksi internet.")
        return

    try:
        # Build application dengan konfigurasi yang benar untuk v22.2
        app = Application.builder().token(TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("status", status_command))
        app.add_handler(CallbackQueryHandler(handle_callback_query))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_credentials))
        
        # Add error handler
        app.add_error_handler(error_handler)

        logger.info("Bot Telegram Mentari UNPAM started successfully")
        print("🚀 Bot Telegram Mentari UNPAM aktif...", flush=True)
        print("📝 Log disimpan di 'bot.log'", flush=True)
        print("⏹️  Tekan Ctrl+C untuk menghentikan bot", flush=True)
        
        # Run bot
        if app.run_polling:
            await app.run_polling(allowed_updates=Update.ALL_TYPES)  # type: ignore
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ Gagal menjalankan bot: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\n👋 Bot dihentikan oleh pengguna")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"💥 Error fatal: {e}")
