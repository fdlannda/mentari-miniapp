"""
Telegram Mini App Integration untuk Mentari UNPAM
Modul untuk mengintegrasikan Mentari UNPAM sebagai Telegram Mini App
"""

import json
import hashlib
import hmac
import time
from urllib.parse import urlencode, quote, parse_qs
from typing import Dict, List, Optional
from dataclasses import dataclass


def verify_telegram_auth(init_data: str, bot_token: str) -> bool:
    """
    Verify Telegram Mini App authentication data
    
    Args:
        init_data: Data from Telegram.WebApp.initData
        bot_token: Bot token untuk verification
        
    Returns:
        True jika authentication valid
    """
    if not init_data or not bot_token:
        return False
        
    try:
        # Parse init data
        parsed_data = parse_qs(init_data)
        
        # Get hash from data
        if 'hash' not in parsed_data:
            return False
            
        received_hash = parsed_data['hash'][0]
        
        # Remove hash from data untuk verification
        auth_data = {k: v[0] for k, v in parsed_data.items() if k != 'hash'}
        
        # Create data string untuk HMAC
        data_check_string = '\n'.join([f'{k}={v}' for k, v in sorted(auth_data.items())])
        
        # Create secret key
        secret_key = hmac.new(
            b"WebAppData", 
            bot_token.encode(), 
            hashlib.sha256
        ).digest()
        
        # Calculate expected hash
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(received_hash, expected_hash)
        
    except Exception as e:
        print(f"Auth verification error: {e}")
        return False


@dataclass
class MiniAppConfig:
    """Konfigurasi Telegram Mini App"""
    bot_token: str
    app_url: str  # URL mini app (e.g., https://mentari-miniapp.yourdomain.com)
    app_name: str = "mentari_unpam"
    theme: str = "dark"


class TelegramMiniAppGenerator:
    """Generator untuk Telegram Mini App URLs dan integration"""
    
    def __init__(self, config: MiniAppConfig):
        self.config = config
        self.bot_token = config.bot_token
        
    def generate_webapp_url(self, course_code: str, meeting_number: int, 
                           forum_url: str, user_credentials: Dict[str, str]) -> str:
        """
        Generate Telegram Mini App URL untuk join forum specific
        
        Args:
            course_code: Kode mata kuliah (e.g., "20251-03TPLK006-22TIF0093")
            meeting_number: Nomor pertemuan
            forum_url: URL forum yang akan di-join
            user_credentials: Credentials yang akan di-pass ke mini app
        
        Returns:
            URL untuk membuka Mini App dengan context specific
        """
        
        # Data yang akan di-pass ke Mini App
        app_data = {
            "action": "join_forum",
            "course_code": course_code,
            "meeting_number": meeting_number,
            "forum_url": forum_url,
            "timestamp": int(time.time()),
            # Credentials di-encrypt untuk security
            "auth_hash": self._generate_auth_hash(user_credentials)
        }
        
        # Encode data sebagai query parameters
        query_params = urlencode(app_data)
        
        # Generate Mini App URL
        mini_app_url = f"{self.config.app_url}?{query_params}"
        
        # Create Telegram WebApp URL
        webapp_url = f"https://t.me/{self.config.app_name}?startapp={quote(mini_app_url)}"
        
        return webapp_url
    
    def _generate_auth_hash(self, credentials: Dict[str, str]) -> str:
        """Generate secure hash untuk credentials"""
        data = json.dumps(credentials, sort_keys=True)
        return hmac.new(
            self.bot_token.encode(), 
            data.encode(), 
            hashlib.sha256
        ).hexdigest()
    
    def create_inline_keyboard_with_miniapp(self, course_code: str, meeting_number: int,
                                          forum_url: str, user_credentials: Dict[str, str]) -> Dict:
        """
        Create inline keyboard dengan Mini App button
        
        Returns:
            Telegram InlineKeyboard markup dengan Web App button
        """
        
        webapp_url = self.generate_webapp_url(
            course_code, meeting_number, forum_url, user_credentials
        )
        
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": f"🚀 Join Forum Pertemuan {meeting_number}",
                        "web_app": {
                            "url": webapp_url
                        }
                    }
                ],
                [
                    {
                        "text": "📚 Lihat Detail Mata Kuliah",
                        "callback_data": f"course_detail_{course_code}"
                    }
                ]
            ]
        }
        
        return keyboard
    
    def generate_bulk_join_url(self, available_forums: List[Dict]) -> str:
        """
        Generate Mini App URL untuk join multiple forums sekaligus
        
        Args:
            available_forums: List forum yang tersedia untuk di-join
        """
        
        app_data = {
            "action": "bulk_join",
            "forums": available_forums,
            "timestamp": int(time.time())
        }
        
        query_params = urlencode({"data": json.dumps(app_data)})
        mini_app_url = f"{self.config.app_url}/bulk?{query_params}"
        webapp_url = f"https://t.me/{self.config.app_name}?startapp={quote(mini_app_url)}"
        
        return webapp_url


class MiniAppResponseHandler:
    """Handler untuk response dari Mini App"""
    
    @staticmethod
    def create_success_message(course_name: str, meeting_number: int) -> str:
        """Create success message setelah join forum via Mini App"""
        return f"""
✅ **Berhasil Bergabung!**

📚 **{course_name}**
🎯 **Pertemuan {meeting_number}**

✨ Anda telah berhasil bergabung ke forum diskusi melalui Mini App!

🎉 **Next Steps:**
• Aktif berpartisipasi dalam diskusi
• Baca materi yang dibagikan
• Submit tugas sesuai deadline

💡 **Tip:** Bookmark forum ini untuk akses cepat di masa depan
"""
    
    @staticmethod
    def create_error_message(error_type: str, details: str = "") -> str:
        """Create error message untuk Mini App failures"""
        error_messages = {
            "auth_failed": "❌ **Authentication Failed**\n\nSilakan login ulang melalui bot",
            "forum_not_found": "❌ **Forum Tidak Ditemukan**\n\nForum mungkin sudah ditutup atau URL berubah",
            "already_joined": "ℹ️ **Sudah Bergabung**\n\nAnda sudah menjadi member forum ini",
            "network_error": "🌐 **Koneksi Bermasalah**\n\nCoba lagi dalam beberapa saat",
            "unknown": "❓ **Error Tidak Dikenal**\n\nSilakan hubungi admin untuk bantuan"
        }
        
        base_message = error_messages.get(error_type, error_messages["unknown"])
        
        if details:
            base_message += f"\n\n**Detail:** {details}"
            
        return base_message


# Mini App HTML Template (untuk development/testing)
MINI_APP_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mentari UNPAM - Join Forum</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: var(--tg-theme-bg-color, #ffffff);
            color: var(--tg-theme-text-color, #000000);
        }}
        .container {{
            max-width: 400px;
            margin: 0 auto;
        }}
        .course-info {{
            background: var(--tg-theme-secondary-bg-color, #f1f1f1);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .join-button {{
            width: 100%;
            padding: 15px;
            background: var(--tg-theme-button-color, #007AFF);
            color: var(--tg-theme-button-text-color, #ffffff);
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
        }}
        .join-button:hover {{
            opacity: 0.8;
        }}
        .loading {{
            display: none;
            text-align: center;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="course-info">
            <h3 id="course-name">📚 Loading...</h3>
            <p id="meeting-info">🎯 Pertemuan: Loading...</p>
        </div>
        
        <button class="join-button" id="join-btn" onclick="joinForum()">
            🚀 Bergabung ke Forum
        </button>
        
        <div class="loading" id="loading">
            <p>⏳ Sedang memproses...</p>
        </div>
        
        <div id="result"></div>
    </div>

    <script>
        // Initialize Telegram Web App
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();
        
        // Parse URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const courseCode = urlParams.get('course_code');
        const meetingNumber = urlParams.get('meeting_number');
        const forumUrl = urlParams.get('forum_url');
        
        // Update UI
        document.getElementById('course-name').textContent = `📚 ${{courseCode}}`;
        document.getElementById('meeting-info').textContent = `🎯 Pertemuan: ${{meetingNumber}}`;
        
        async function joinForum() {{
            const joinBtn = document.getElementById('join-btn');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            
            joinBtn.style.display = 'none';
            loading.style.display = 'block';
            
            try {{
                // Simulate forum join process
                // In real implementation, this would call Mentari UNPAM API
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                result.innerHTML = `
                    <div style="background: #4CAF50; color: white; padding: 15px; border-radius: 10px; text-align: center;">
                        ✅ Berhasil bergabung ke forum!<br>
                        <small>Anda akan diarahkan kembali ke chat...</small>
                    </div>
                `;
                
                // Close Mini App and return to chat
                setTimeout(() => {{
                    window.Telegram.WebApp.close();
                }}, 2000);
                
            }} catch (error) {{
                result.innerHTML = `
                    <div style="background: #f44336; color: white; padding: 15px; border-radius: 10px; text-align: center;">
                        ❌ Gagal bergabung ke forum<br>
                        <small>${{error.message}}</small>
                    </div>
                `;
                joinBtn.style.display = 'block';
            }}
            
            loading.style.display = 'none';
        }}
    </script>
</body>
</html>
"""