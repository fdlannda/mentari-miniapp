"""
Simple Telegram Mini App Server untuk Mentari UNPAM - Vercel Version
Minimal Flask server yang handle Mini App requests
"""

from flask import Flask, request, jsonify
import os
import time
import random
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    """Main Mini App page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Forum Mini App</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f0f0f0; }
            .container { max-width: 400px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            .btn { background: #007AFF; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; width: 100%; margin: 10px 0; }
            .success { background: #28a745; }
            .error { background: #dc3545; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎓 Forum Discussion</h2>
            <div id="content">
                <p>Siap bergabung ke forum diskusi?</p>
                <button class="btn" onclick="joinForum()">🚀 Bergabung ke Forum</button>
            </div>
        </div>

        <script>
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.ready();
                window.Telegram.WebApp.expand();
            }

            async function joinForum() {
                const content = document.getElementById('content');
                content.innerHTML = '<p>⏳ Memproses...</p>';
                
                try {
                    const response = await fetch('/api/join', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'join' })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        content.innerHTML = `
                            <div style="background: #d4edda; padding: 15px; border-radius: 8px; color: #155724; margin: 10px 0;">
                                <h3>✅ Berhasil!</h3>
                                <p>Anda sudah terdaftar dalam forum diskusi!</p>
                            </div>
                            <button class="btn success" onclick="closeApp()">✅ Selesai</button>
                        `;
                    } else {
                        throw new Error(data.message || 'Gagal bergabung');
                    }
                } catch (error) {
                    content.innerHTML = `
                        <div style="background: #f8d7da; padding: 15px; border-radius: 8px; color: #721c24; margin: 10px 0;">
                            <h3>❌ Error</h3>
                            <p>${error.message}</p>
                        </div>
                        <button class="btn error" onclick="location.reload()">🔄 Coba Lagi</button>
                    `;
                }
            }

            function closeApp() {
                if (window.Telegram && window.Telegram.WebApp) {
                    window.Telegram.WebApp.close();
                }
            }
        </script>
    </body>
    </html>
    """

@app.route('/forum')
def forum_page():
    """Forum page dengan parameter"""
    return index()

@app.route('/api/join', methods=['POST'])
def join_api():
    """Simple join API"""
    try:
        # Simulate processing
        time.sleep(1)
        
        # Simulate 95% success rate
        if random.random() < 0.95:
            return jsonify({
                'success': True,
                'message': 'Successfully joined forum',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to join forum'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/health')
def health():
    """Health check"""
    return jsonify({
        "status": "ok",
        "service": "Simple Mini App",
        "version": "1.0.0"
    })

# For Vercel
if __name__ == '__main__':
    app.run(debug=True)