"""
Telegram Mini App Server untuk Mentari UNPAM
Flask server yang handle Mini App requests dan forum joining
"""

from flask import Flask, request, render_template_string, jsonify
from flask_cors import CORS
import hashlib
import hmac
import json
import time
import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import bot services
from core.bot_service import MentariBotCore
from models import LoginCredentials
from config import env_config, ConfigManager

app = Flask(__name__)
CORS(app)

# Initialize config
config_manager = ConfigManager()
config_manager.switch_mode('production')  # Fast mode for Mini App

# Bot service for forum operations
bot_service = MentariBotCore(config_manager.config)

# HTML template untuk Mini App
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
            padding: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: var(--tg-theme-secondary-bg-color, #f1f1f1);
            padding: 20px 15px;
            text-align: center;
            border-bottom: 1px solid var(--tg-theme-hint-color, #cccccc);
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: var(--tg-theme-button-color, #007AFF);
            margin-bottom: 5px;
        }
        
        .subtitle {
            font-size: 14px;
            color: var(--tg-theme-hint-color, #999999);
        }
        
        .container {
            flex: 1;
            padding: 20px 15px;
            max-width: 400px;
            margin: 0 auto;
            width: 100%;
        }
        
        .course-card {
            background: var(--tg-theme-secondary-bg-color, #f8f9fa);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid var(--tg-theme-hint-color, #e0e0e0);
        }
        
        .course-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--tg-theme-text-color, #000000);
        }
        
        .course-code {
            font-size: 12px;
            color: var(--tg-theme-hint-color, #666666);
            background: var(--tg-theme-bg-color, #ffffff);
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
            margin-bottom: 12px;
        }
        
        .meeting-info {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 20px;
        }
        
        .meeting-badge {
            background: var(--tg-theme-button-color, #007AFF);
            color: var(--tg-theme-button-text-color, #ffffff);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }
        
        .status-badge {
            background: #FFA500;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
        }
        
        .join-button {
            width: 100%;
            padding: 16px;
            background: var(--tg-theme-button-color, #007AFF);
            color: var(--tg-theme-button-text-color, #ffffff);
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 15px;
        }
        
        .join-button:hover {
            opacity: 0.9;
        }
        
        .join-button:disabled {
            background: var(--tg-theme-hint-color, #cccccc);
            cursor: not-allowed;
        }
        
        .bulk-button {
            background: #28a745;
            margin-bottom: 10px;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 30px;
        }
        
        .loading-spinner {
            border: 3px solid var(--tg-theme-hint-color, #f3f3f3);
            border-top: 3px solid var(--tg-theme-button-color, #007AFF);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-weight: 500;
        }
        
        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .footer {
            text-align: center;
            padding: 15px;
            font-size: 12px;
            color: var(--tg-theme-hint-color, #999999);
            border-top: 1px solid var(--tg-theme-hint-color, #e0e0e0);
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">📚 Mentari UNPAM</div>
        <div class="subtitle">Forum Discussion Mini App</div>
    </div>

    <div class="container">
        <div id="single-forum" style="display: none;">
            <div class="course-card">
                <div class="course-title" id="course-name">Loading...</div>
                <div class="course-code" id="course-code">Loading...</div>
                <div class="meeting-info">
                    <div class="meeting-badge">📍 Pertemuan <span id="meeting-number">-</span></div>
                    <div class="status-badge">🟡 Available</div>
                </div>
            </div>
            
            <button class="join-button" id="join-single-btn" onclick="joinSingleForum()">
                🚀 Bergabung ke Forum
            </button>
        </div>

        <div id="bulk-forums" style="display: none;">
            <div class="course-card">
                <div class="course-title">📋 Multiple Forums Available</div>
                <div class="course-code">Bulk Join Operation</div>
                <div id="forums-list"></div>
            </div>
            
            <button class="join-button bulk-button" id="join-bulk-btn" onclick="joinBulkForums()">
                ⚡ Join Semua Forum
            </button>
        </div>
        
        <div class="loading" id="loading">
            <div class="loading-spinner"></div>
            <p>⏳ Sedang memproses...</p>
        </div>
        
        <div id="result"></div>
    </div>

    <div class="footer">
        🔒 Secure • 🚀 Fast • 📱 Native
    </div>

    <script>
        // Initialize Telegram Web App
        if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand();
            
            // Set theme
            if (window.Telegram.WebApp.colorScheme === 'dark') {
                document.body.style.setProperty('--tg-theme-bg-color', '#1a1a1a');
                document.body.style.setProperty('--tg-theme-text-color', '#ffffff');
                document.body.style.setProperty('--tg-theme-secondary-bg-color', '#2a2a2a');
            }
        }
        
        // Parse URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const action = urlParams.get('action');
        
        // Initialize UI based on action
        if (action === 'bulk_join') {
            initBulkJoin();
        } else {
            initSingleJoin();
        }
        
        function initSingleJoin() {
            const courseCode = urlParams.get('course_code');
            const meetingNumber = urlParams.get('meeting_number');
            const forumUrl = urlParams.get('forum_url');
            
            if (!courseCode || !meetingNumber) {
                showError('Invalid parameters');
                return;
            }
            
            // Extract course name from course code (simplified)
            const courseName = courseCode.includes('22TIF0093') ? 'STATISTIKA DAN PROBABILITAS' :
                              courseCode.includes('22TIF0152') ? 'SISTEM BERKAS' :
                              courseCode.includes('22TIF0142') ? 'MATEMATIKA DISKRIT' :
                              courseCode.includes('22TIF0133') ? 'JARINGAN KOMPUTER' :
                              'Unknown Course';
            
            document.getElementById('course-name').textContent = courseName;
            document.getElementById('course-code').textContent = courseCode;
            document.getElementById('meeting-number').textContent = meetingNumber;
            document.getElementById('single-forum').style.display = 'block';
        }
        
        function initBulkJoin() {
            try {
                const forumsData = urlParams.get('data');
                const forums = JSON.parse(decodeURIComponent(forumsData));
                
                let forumsList = '';
                forums.forums.forEach(forum => {
                    forumsList += `
                        <div style="margin: 8px 0; padding: 8px; background: var(--tg-theme-bg-color, #fff); border-radius: 6px;">
                            <div style="font-weight: 500; font-size: 14px;">${forum.course_name}</div>
                            <div style="font-size: 12px; color: var(--tg-theme-hint-color, #666);">Pertemuan ${forum.meeting_number}</div>
                        </div>
                    `;
                });
                
                document.getElementById('forums-list').innerHTML = forumsList;
                document.getElementById('bulk-forums').style.display = 'block';
            } catch (e) {
                showError('Invalid bulk data');
            }
        }
        
        async function joinSingleForum() {
            const btn = document.getElementById('join-single-btn');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            
            btn.style.display = 'none';
            loading.style.display = 'block';
            
            try {
                const courseCode = urlParams.get('course_code');
                const meetingNumber = urlParams.get('meeting_number');
                const authHash = urlParams.get('auth_hash');
                
                const response = await fetch('/api/join-forum', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        action: 'join_single',
                        course_code: courseCode,
                        meeting_number: parseInt(meetingNumber),
                        auth_hash: authHash
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showSuccess(`✅ Berhasil bergabung ke forum!\\n\\n📚 ${data.course_name}\\n🎯 Pertemuan ${meetingNumber}\\n\\n🎉 Selamat! Anda sekarang dapat berpartisipasi dalam diskusi.`);
                    
                    // Auto close after 3 seconds
                    setTimeout(() => {
                        if (window.Telegram?.WebApp) {
                            window.Telegram.WebApp.close();
                        }
                    }, 3000);
                } else {
                    showError(data.error || 'Gagal bergabung ke forum');
                    btn.style.display = 'block';
                }
                
            } catch (error) {
                showError('Network error: ' + error.message);
                btn.style.display = 'block';
            }
            
            loading.style.display = 'none';
        }
        
        async function joinBulkForums() {
            const btn = document.getElementById('join-bulk-btn');
            const loading = document.getElementById('loading');
            
            btn.style.display = 'none';
            loading.style.display = 'block';
            
            try {
                // Simulate bulk join (implement actual logic)
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                showSuccess('✅ Berhasil bergabung ke semua forum!\\n\\n🎉 Anda sekarang dapat berpartisipasi dalam semua diskusi yang tersedia.');
                
                setTimeout(() => {
                    if (window.Telegram?.WebApp) {
                        window.Telegram.WebApp.close();
                    }
                }, 3000);
                
            } catch (error) {
                showError('Gagal bergabung ke forum: ' + error.message);
                btn.style.display = 'block';
            }
            
            loading.style.display = 'none';
        }
        
        function showSuccess(message) {
            const result = document.getElementById('result');
            result.innerHTML = `<div class="result success">${message}</div>`;
        }
        
        function showError(message) {
            const result = document.getElementById('result');
            result.innerHTML = `<div class="result error">❌ ${message}</div>`;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def miniapp():
    """Main Mini App page"""
    return render_template_string(MINI_APP_HTML)

@app.route('/forum')
def forum_page():
    """Forum-specific Mini App page dengan parameter course"""
    course_code = request.args.get('course', 'UNKNOWN')
    meeting_number = request.args.get('meeting', '1')
    course_name = request.args.get('name', 'Unknown Course')
    
    # Create specialized HTML untuk forum spesifik ini
    forum_html = MINI_APP_HTML.replace(
        'Mentari UNPAM - Join Forum',
        f'Join Forum - {course_name} M{meeting_number}'
    ).replace(
        '<div class="course-code">UNKNOWN-CODE</div>',
        f'<div class="course-code">{course_code}</div>'
    ).replace(
        '<div class="meeting-number">Pertemuan 1</div>',
        f'<div class="meeting-number">Pertemuan {meeting_number}</div>'
    ).replace(
        '<div class="course-name">Default Course</div>',
        f'<div class="course-name">{course_name}</div>'
    )
    
    return render_template_string(forum_html)

@app.route('/api/join-forum', methods=['POST'])
def join_forum():
    """API endpoint untuk join forum"""
    try:
        data = request.get_json()
        action = data.get('action')
        course_code = data.get('course_code')
        meeting_number = data.get('meeting_number')
        auth_hash = data.get('auth_hash')
        
        # Verify auth hash (simplified for demo)
        if not auth_hash:
            return jsonify({'success': False, 'error': 'Authentication required'})
        
        # Simulate forum join process
        # In real implementation, this would:
        # 1. Decrypt credentials from auth_hash
        # 2. Login to Mentari UNPAM
        # 3. Navigate to specific forum
        # 4. Perform join action
        
        course_names = {
            '20251-03TPLK006-22TIF0093': 'STATISTIKA DAN PROBABILITAS',
            '20251-03TPLK006-22TIF0152': 'SISTEM BERKAS',
            '20251-03TPLK006-22TIF0142': 'MATEMATIKA DISKRIT',
            '20251-03TPLK006-22TIF0133': 'JARINGAN KOMPUTER'
        }
        
        course_name = course_names.get(course_code, 'Unknown Course')
        
        # Simulate processing delay
        time.sleep(2)
        
        return jsonify({
            'success': True,
            'course_name': course_name,
            'meeting_number': meeting_number,
            'message': f'Successfully joined {course_name} - Meeting {meeting_number}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/verify-auth', methods=['POST'])
def verify_auth():
    """Verify authentication hash"""
    try:
        data = request.get_json()
        auth_hash = data.get('auth_hash')
        
        # Implement actual auth verification here
        # For demo, always return success
        
        return jsonify({'valid': True})
        
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)})

if __name__ == '__main__':
    print("🚀 Starting Telegram Mini App Server...")
    print("📱 Mini App URL: http://localhost:5000")
    print("🔒 For production, use HTTPS with SSL certificate")
    print("📝 Update app_url in helper.py to point to your domain")
    print()
    
    # Check if in production mode
    if os.getenv('FLASK_ENV') == 'production':
        print("🌐 Running in PRODUCTION mode")
        app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')
    else:
        print("🧪 Running in DEVELOPMENT mode")
        app.run(host='127.0.0.1', port=5000, debug=True)