from flask import Flask, request, jsonify
import os
import time
import random
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mentari UNPAM Mini App</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0; padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; min-height: 100vh;
            }
            .container { 
                max-width: 400px; margin: 0 auto; 
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px; padding: 20px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            .course-info {
                background: rgba(255, 255, 255, 0.2);
                padding: 15px; border-radius: 10px; margin-bottom: 20px;
                border-left: 4px solid #ffd700;
            }
            .btn {
                background: linear-gradient(45deg, #51cf66, #37b24d);
                color: white; border: none; padding: 12px 20px;
                border-radius: 8px; cursor: pointer; font-size: 14px;
                width: 100%; margin: 8px 0; transition: all 0.3s ease;
            }
            .btn:hover { transform: translateY(-2px); }
            .btn-primary { background: linear-gradient(45deg, #339af0, #1971c2); }
            .btn-warning { background: linear-gradient(45deg, #ffd43b, #fab005); color: #333; }
            .success-box { 
                background: rgba(76, 175, 80, 0.2); border: 1px solid #4caf50; 
                color: #4caf50; padding: 15px; border-radius: 8px; margin: 15px 0; 
            }
            .error-box { 
                background: rgba(244, 67, 54, 0.2); border: 1px solid #f44336; 
                color: #f44336; padding: 15px; border-radius: 8px; margin: 15px 0; 
            }
            .spinner { 
                border: 3px solid rgba(255,255,255,0.3); border-top: 3px solid white; 
                border-radius: 50%; width: 30px; height: 30px; 
                animation: spin 1s linear infinite; margin: 0 auto 15px; 
            }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .hidden { display: none !important; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎓 Forum Discussion Mini App</h2>
            
            <div class="course-info">
                <div style="font-size: 14px; opacity: 0.8; margin-bottom: 5px;" id="course-code">Loading...</div>
                <div style="font-size: 18px; font-weight: bold;" id="course-title">Loading...</div>
                <span style="background: #ff6b6b; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; display: inline-block; margin: 10px 5px 0 0;">
                    📚 <span id="meeting-number">-</span>
                </span>
                <span style="background: #51cf66; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; display: inline-block; margin: 10px 0 0 5px;">
                    ✅ Available
                </span>
            </div>

            <!-- Initial View -->
            <div id="initial-view">
                <div style="background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; margin: 15px 0; text-align: center;">
                    <p>🎯 Siap bergabung ke forum diskusi?</p>
                    <p style="font-size: 14px; opacity: 0.8;">Bot akan otomatis join forum untuk Anda</p>
                </div>
                <button class="btn" onclick="joinForum()">🚀 Bergabung ke Forum</button>
            </div>

            <!-- Loading View -->
            <div id="loading-view" class="hidden">
                <div style="text-align: center; padding: 20px;">
                    <div class="spinner"></div>
                    <div id="loading-text">Memproses...</div>
                </div>
            </div>

            <!-- Success View -->
            <div id="success-view" class="hidden">
                <div class="success-box">
                    <h3>🎉 Berhasil!</h3>
                    <p>✅ Anda sudah terdaftar dalam forum diskusi!</p>
                    <p>📚 Partisipasi Anda telah tercatat</p>
                    <p>💡 Silakan cek dashboard Mentari UNPAM Anda.</p>
                </div>
                <button class="btn btn-primary" onclick="openForum()">🌐 Buka Forum</button>
                <button class="btn" onclick="closeApp()">✅ Selesai</button>
            </div>

            <!-- Error View -->
            <div id="error-view" class="hidden">
                <div class="error-box" id="error-message"></div>
                <button class="btn" onclick="resetApp()">🔄 Coba Lagi</button>
            </div>
        </div>

        <script>
            const tg = window.Telegram?.WebApp;
            if (tg) {
                tg.ready();
                tg.expand();
            }

            // Get URL parameters
            const urlParams = new URLSearchParams(window.location.search);
            const courseCode = urlParams.get('course_code') || 'UNKNOWN-CODE';
            const courseTitle = urlParams.get('course_title') || 'Course Title';
            const meetingNumber = urlParams.get('meeting_number') || '1';
            
            // Update UI with course info
            document.getElementById('course-code').textContent = courseCode;
            document.getElementById('course-title').textContent = courseTitle;
            document.getElementById('meeting-number').textContent = 'Pertemuan ' + meetingNumber;

            function showView(viewId) {
                ['initial-view', 'loading-view', 'success-view', 'error-view'].forEach(id => {
                    document.getElementById(id).classList.add('hidden');
                });
                document.getElementById(viewId).classList.remove('hidden');
            }

            async function joinForum() {
                showView('loading-view');
                document.getElementById('loading-text').textContent = 'Bergabung ke forum...';

                try {
                    const response = await fetch('/api/join-forum', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            course_code: courseCode,
                            course_title: courseTitle,
                            meeting_number: meetingNumber
                        })
                    });

                    const data = await response.json();
                    
                    if (data.success) {
                        showView('success-view');
                        window.forumUrl = data.forum_url || `https://mentari.unpam.ac.id/u-courses/${courseCode}?accord_pertemuan=PERTEMUAN_${meetingNumber}`;
                    } else {
                        throw new Error(data.message || 'Gagal bergabung ke forum');
                    }
                } catch (error) {
                    document.getElementById('error-message').innerHTML = 
                        '<h3>❌ Gagal Join Forum</h3><p>' + error.message + '</p>';
                    showView('error-view');
                }
            }

            function openForum() {
                if (window.forumUrl) {
                    window.open(window.forumUrl, '_blank');
                }
            }

            function resetApp() {
                showView('initial-view');
            }

            function closeApp() {
                if (tg) tg.close();
            }
        </script>
    </body>
    </html>
    '''

@app.route('/forum')
def forum_page():
    """Forum page with parameters"""
    return index()

@app.route('/api/join-forum', methods=['POST'])
def join_forum_api():
    """API endpoint for joining forum"""
    try:
        data = request.get_json()
        course_code = data.get('course_code', 'UNKNOWN')
        course_title = data.get('course_title', 'Unknown Course')
        meeting_number = data.get('meeting_number', '1')
        
        # Simulate forum joining process
        time.sleep(1)  # Simulate processing time
        
        # Generate forum URL
        forum_url = f'https://mentari.unpam.ac.id/u-courses/{course_code}?accord_pertemuan=PERTEMUAN_{meeting_number}'
        
        # Simulate 95% success rate
        if random.random() < 0.95:
            return jsonify({
                'success': True,
                'message': f'✅ Berhasil bergabung forum {course_title} pertemuan {meeting_number}!',
                'forum_url': forum_url,
                'course_code': course_code,
                'meeting_number': meeting_number,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Gagal bergabung ke forum. Silakan coba lagi.'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/test')
def test():
    return {'status': 'ok', 'message': 'API works!'}

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok", 
        "service": "Mentari UNPAM Mini App",
        "version": "2.0.0"
    })

if __name__ == '__main__':
    app.run(debug=True)