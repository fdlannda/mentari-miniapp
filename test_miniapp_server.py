#!/usr/bin/env python3
"""
Simple test untuk Flask Mini App Server
Test server tanpa bot integration
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, render_template_string, jsonify
from flask_cors import CORS
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Create Flask app
app = Flask(__name__)
CORS(app)

# Mini App HTML (same as unified version)
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
        
        .test-info {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 16px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="test-info">
            🧪 <strong>Test Mode</strong><br>
            Server berjalan di localhost:5000
        </div>
        
        <div class="header">
            <h1>🎓 Join Forum</h1>
            <p>Bergabung dengan forum Mentari UNPAM</p>
        </div>
        
        <div class="forum-info">
            <h3 id="courseCode">20251-03TPLK006-22TIF0093</h3>
            <p id="meetingInfo">Meeting 1 - Test Forum</p>
        </div>
        
        <button id="joinButton" class="join-button" onclick="joinForum()">
            🚀 Join Forum Sekarang
        </button>
        
        <div id="status" class="status" style="display: none;"></div>
        
        <div class="footer">
            <p>🤖 Mentari UNPAM Bot - Mini App (Test)</p>
        </div>
    </div>

    <script>
        // Mock Telegram Web App untuk testing
        if (typeof window.Telegram === 'undefined') {
            window.Telegram = {
                WebApp: {
                    ready: () => console.log('Mock: WebApp ready'),
                    expand: () => console.log('Mock: WebApp expand'),
                    close: () => console.log('Mock: WebApp close'),
                    initData: 'test_init_data',
                    BackButton: {
                        show: () => console.log('Mock: Back button show')
                    },
                    onEvent: (event, callback) => {
                        console.log('Mock: Event listener added:', event);
                    }
                }
            };
        }
        
        // Initialize
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();
        
        // Parse URL parameters (dengan defaults untuk test)
        const urlParams = new URLSearchParams(window.location.search);
        const courseCode = urlParams.get('course_code') || '20251-03TPLK006-22TIF0093';
        const meetingNumber = urlParams.get('meeting_number') || '1';
        const authHash = urlParams.get('auth_hash') || 'test_hash';
        
        // Display forum information
        document.getElementById('courseCode').textContent = courseCode;
        document.getElementById('meetingInfo').textContent = 
            `Meeting ${meetingNumber} - Test untuk join forum`;
        
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
                        telegram_data: window.Telegram.WebApp.initData || 'test_data'
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    statusDiv.className = 'status success';
                    statusDiv.textContent = '✅ Berhasil bergabung dengan forum!';
                    joinButton.innerHTML = '✅ Forum Joined';
                    
                    // Mock close after success
                    setTimeout(() => {
                        console.log('Mock: Closing Mini App');
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
        
        console.log('🧪 Mini App Test Mode - Ready!');
    </script>
</body>
</html>
"""

@app.route('/')
def mini_app():
    """Mini App main page"""
    print("📱 Mini App page accessed")
    return render_template_string(MINI_APP_HTML)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'miniapp-test-server',
        'mode': 'test'
    })

@app.route('/api/join-forum', methods=['POST'])
def api_join_forum():
    """API endpoint untuk join forum (test version)"""
    try:
        data = request.json
        course_code = data.get('course_code')
        meeting_number = data.get('meeting_number')
        auth_hash = data.get('auth_hash')
        telegram_data = data.get('telegram_data')
        
        print(f"🔗 Join forum request: {course_code} Meeting {meeting_number}")
        print(f"   Auth Hash: {auth_hash}")
        print(f"   Telegram Data: {telegram_data}")
        
        # Simulate processing time
        import time
        time.sleep(1)
        
        # Simulate success (untuk testing)
        success = True
        
        if success:
            print(f"✅ Successfully joined forum: {course_code} Meeting {meeting_number}")
            return jsonify({
                'success': True,
                'message': f'Successfully joined {course_code} Meeting {meeting_number}',
                'mode': 'test'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to join forum'})
            
    except Exception as e:
        print(f"❌ Join forum API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("🧪 MINI APP TEST SERVER")
    print("=" * 40)
    print("🌐 Starting Flask server...")
    print("🔗 Access: http://localhost:5000")
    print("🧪 Health: http://localhost:5000/health")
    print("=" * 40)
    print("📝 Press Ctrl+C to stop")
    print()
    
    # Run Flask server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )