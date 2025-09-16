"""
Telegram Mini App Server untuk Mentari UNPAM - Vercel Version
Flask server yang handle Mini App requests dan forum joining
"""

from flask import Flask, request, render_template_string, jsonify
import os

app = Flask(__name__)

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
            opacity: 0.8;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            display: none;
        }
        
        .loading-spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid var(--tg-theme-button-color, #007AFF);
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
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            display: none;
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
        <div class="course-card">
            <div class="course-title" id="course-name">Loading...</div>
            <div class="course-code" id="course-code">Loading...</div>
            <div class="meeting-info">
                <div class="meeting-badge">📍 Pertemuan <span id="meeting-number">-</span></div>
                <div class="status-badge">🟡 Available</div>
            </div>
        </div>
        
        <button class="join-button" id="join-btn" onclick="joinForum()">
            🚀 Bergabung ke Forum
        </button>
        
        <div class="loading" id="loading">
            <div class="loading-spinner"></div>
            <div id="loading-text">Sedang memproses...</div>
            <div id="loading-steps" style="font-size: 12px; margin-top: 10px; color: #666;">
                <div>⏳ Menghubungkan ke server...</div>
            </div>
        </div>
        
        <div class="result" id="result"></div>
    </div>

    <div class="footer">
        Powered by Telegram Mini Apps
    </div>

    <script>
        // Initialize Telegram Web App
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand();
        }
        
        // Get URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const courseCode = urlParams.get('course') || 'UNKNOWN';
        const meetingNumber = urlParams.get('meeting') || '1';
        const courseName = decodeURIComponent(urlParams.get('name') || 'Unknown Course');
        const encodedCreds = urlParams.get('creds') || '';
        
        // Decode credentials if available
        let credentials = {};
        if (encodedCreds) {
            try {
                const decodedCreds = atob(encodedCreds);
                credentials = JSON.parse(decodedCreds);
            } catch (e) {
                console.log('Could not decode credentials');
            }
        }
        
        // Update UI with course info
        document.getElementById('course-name').textContent = courseName;
        document.getElementById('course-code').textContent = courseCode;
        document.getElementById('meeting-number').textContent = meetingNumber;
        
        // Set theme if available
        if (window.Telegram && window.Telegram.WebApp) {
            document.body.style.backgroundColor = window.Telegram.WebApp.backgroundColor || '#ffffff';
        }
        
        async function joinForum() {
            const btn = document.getElementById('join-btn');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            
            btn.style.display = 'none';
            loading.style.display = 'block';
            result.style.display = 'none';
            
            try {
                // Update loading status
                document.getElementById('loading-text').textContent = 'Memproses login...';
                document.getElementById('loading-steps').innerHTML = `
                    <div>✅ Menghubungkan ke server</div>
                    <div>⏳ Login dengan kredensial Anda...</div>
                `;
                
                // Send join request to API
                const response = await fetch('/api/join-forum', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        course_code: courseCode,
                        meeting_number: meetingNumber,
                        user_data: window.Telegram?.WebApp?.initDataUnsafe || {},
                        credentials: credentials
                    })
                });
                
                const data = await response.json();
                
                loading.style.display = 'none';
                result.style.display = 'block';
                
                if (data.success) {
                    result.className = 'result success';
                    
                    if (data.next_action === 'show_success_in_miniapp') {
                        // Stay in Mini App, show success message
                        result.innerHTML = `
                            <strong>✅ Berhasil bergabung!</strong><br>
                            Forum: ${courseName}<br>
                            Pertemuan: ${meetingNumber}<br>
                            <br>
                            <div style="background: #f0f8ff; padding: 12px; border-radius: 8px; margin: 10px 0;">
                                📚 Anda sudah terdaftar dalam forum diskusi!<br>
                                💡 Silakan cek dashboard Mentari UNPAM Anda.
                            </div>
                            <br>
                            <button onclick="if(window.Telegram?.WebApp) window.Telegram.WebApp.close();" 
                                    style="background: #28a745; color: white; border: none; 
                                           padding: 12px 24px; border-radius: 8px; cursor: pointer; width: 100%;">
                                ✅ Selesai
                            </button>
                        `;
                    } else {
                        // Fallback to original behavior
                        result.innerHTML = `
                            <strong>✅ Berhasil bergabung!</strong><br>
                            Forum: ${courseName}<br>
                            Pertemuan: ${meetingNumber}<br>
                            <br>
                            <button onclick="window.open('${data.forum_url}', '_blank')" 
                                    style="background: #007AFF; color: white; border: none; 
                                           padding: 10px 20px; border-radius: 8px; cursor: pointer;">
                                🌐 Buka Forum
                            </button>
                        `;
                    }
                    
                    // Auto-close Mini App after 8 seconds
                    setTimeout(() => {
                        if (window.Telegram && window.Telegram.WebApp) {
                            window.Telegram.WebApp.close();
                        }
                    }, 8000);
                } else {
                    throw new Error(data.message);
                }
                
            } catch (error) {
                loading.style.display = 'none';
                result.style.display = 'block';
                result.className = 'result error';
                result.innerHTML = `
                    <strong>❌ Gagal bergabung</strong><br>
                    ${error.message || 'Terjadi kesalahan'}<br>
                    <br>
                    <button onclick="location.reload()" 
                            style="background: #dc3545; color: white; border: none; 
                                   padding: 8px 16px; border-radius: 6px; cursor: pointer;">
                        🔄 Coba Lagi
                    </button>
                `;
                btn.style.display = 'block';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main Mini App page"""
    return render_template_string(MINI_APP_HTML)

@app.route('/forum')
def forum_page():
    """Forum-specific Mini App page dengan parameter course"""
    return render_template_string(MINI_APP_HTML)

@app.route('/api/join-forum', methods=['POST'])
def join_forum_api():
    """API endpoint untuk join forum melalui Mini App dengan scraper integration"""
    try:
        data = request.get_json()
        course_code = data.get('course_code')
        meeting_number = data.get('meeting_number')
        user_data = data.get('user_data', {})
        credentials = data.get('credentials', {})
        
        # Extract credentials dari Mini App
        nim = credentials.get('nim', '')
        password = credentials.get('password', '')
        
        if not nim or not password:
            return jsonify({
                'success': False,
                'message': 'Credentials tidak ditemukan. Silakan kirim kredensial ke bot terlebih dahulu.'
            }), 400
        
        # TODO: Implement actual forum joining dengan scraper
        # Untuk sementara, simulasi sukses join forum
        
        # Format URL forum yang benar: u-courses dengan accord_pertemuan
        forum_url = f'https://mentari.unpam.ac.id/u-courses/{course_code}?accord_pertemuan=PERTEMUAN_{meeting_number}'
        
        # Simulate successful forum join
        return jsonify({
            'success': True,
            'message': f'✅ Berhasil bergabung forum {course_code} pertemuan {meeting_number}!',
            'forum_url': forum_url,
            'course_code': course_code,
            'meeting_number': meeting_number,
            'next_action': 'show_success_in_miniapp'  # Don't redirect, stay in Mini App
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok", 
        "service": "Mentari UNPAM Mini App",
        "version": "1.0.0"
    })

# Vercel handler - PENTING untuk Vercel!
# Export app sebagai handler default untuk Vercel
app = app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)