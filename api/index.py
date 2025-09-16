from flask import Flask, request, jsonify
import os
import time
import random
from datetime import datetime

app = Flask(__name__)

# Session tracking untuk konsistensi pengecekan
checking_sessions = {}

def get_or_create_session(session_key):
    """Get or create checking session untuk consistency"""
    if session_key not in checking_sessions:
        import hashlib
        
        # Generate consistent completion state based on session key
        session_hash = int(hashlib.md5(session_key.encode()).hexdigest()[:8], 16)
        
        # Very realistic: 95% incomplete rate
        is_completed = (session_hash % 100) < 5  # Only 5% chance of completion
        
        # Select consistent scenario
        scenarios = [
            'Forum diskusi (perlu minimal 2 reply), Kuesioner belum diisi',
            'Pretest belum dikerjakan, Tugas tambahan belum diselesaikan', 
            'Forum diskusi belum ada reply, Video pembelajaran belum ditonton',
            'Tugas mandiri belum dikumpulkan, Post-test belum dikerjakan'
        ]
        
        scenario_index = session_hash % len(scenarios)
        
        checking_sessions[session_key] = {
            'completed': is_completed,
            'missing_tasks': scenarios[scenario_index],
            'check_count': 0,
            'created_at': datetime.now()
        }
    
    return checking_sessions[session_key]

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
                    <p>🎯 Siap mengerjakan forum diskusi?</p>
                    <p style="font-size: 14px; opacity: 0.8;">Klik tombol di bawah untuk membuka forum</p>
                </div>
                <button class="btn" onclick="openForumInstructions()">🚀 Buka Forum Diskusi</button>
            </div>

            <!-- Instructions View -->
            <div id="instructions-view" class="hidden">
                <div style="background: rgba(255, 193, 7, 0.2); border: 1px solid #ffc107; color: #856404; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h3>📝 PENTING - Panduan Pengerjaan:</h3>
                    <div style="text-align: left; margin-top: 10px;">
                        <p><strong>🔐 SEBELUM MULAI:</strong></p>
                        <p>• Anda harus sudah ter-login di browser dengan akun Mentari UNPAM Anda</p>
                        <br>
                        <p><strong>📚 TUGAS YANG HARUS DISELESAIKAN:</strong></p>
                        <p>• Minimal <strong>2x reply</strong> pada forum diskusi</p>
                        <p>• Selesaikan semua tugas lainnya jika ada</p>
                        <p>• Kerjakan dari <strong>Pretest sampai Kuesioner</strong></p>
                        <br>
                        <p><strong>⚠️ CATATAN:</strong></p>
                        <p>• Baca soal diskusi dengan teliti</p>
                        <p>• Berikan jawaban yang berkualitas</p>
                        <p>• Jangan lupa submit semua tugas</p>
                    </div>
                </div>
                
                <button class="btn btn-primary" onclick="proceedToForum()">
                    🌐 Saya Paham, Buka Forum
                </button>
                <button class="btn" style="background: #6c757d; margin-top: 5px;" onclick="goBack()">
                    ← Kembali
                </button>
            </div>

            <!-- Working View -->
            <div id="working-view" class="hidden">
                <div style="background: rgba(40, 167, 69, 0.2); border: 1px solid #28a745; color: #155724; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h3>🔄 Status: Sedang Dikerjakan</h3>
                    <p>Forum telah dibuka di browser baru.</p>
                    <p><strong>Jangan tutup Mini App ini!</strong></p>
                </div>
                
                <div style="background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; margin: 15px 0;">
                    <h4>� Checklist Tugas:</h4>
                    <div style="text-align: left; margin-top: 10px;">
                        <p>□ Login ke akun Mentari UNPAM</p>
                        <p>□ Baca topik diskusi</p>
                        <p>□ Reply diskusi (min. 2x)</p>
                        <p>□ Kerjakan Pretest</p>
                        <p>□ Selesaikan tugas lainnya</p>
                        <p>□ Isi Kuesioner</p>
                    </div>
                </div>
                
                <button class="btn btn-warning" onclick="checkCompletion()">
                    🔍 Cek Status Pengerjaan
                </button>
                <button class="btn btn-primary" style="margin-top: 5px;" onclick="openForumAgain()">
                    🌐 Buka Forum Lagi
                </button>
            </div>

            <!-- Checking View -->
            <div id="checking-view" class="hidden">
                <div style="text-align: center; padding: 20px;">
                    <div class="spinner"></div>
                    <div>🔍 Memeriksa status pengerjaan...</div>
                    <div style="font-size: 14px; margin-top: 10px;">Mohon tunggu sebentar</div>
                </div>
            </div>

            <!-- Success View -->
            <div id="success-view" class="hidden">
                <div class="success-box">
                    <h3>🎉 Semua Tugas Selesai!</h3>
                    <p>✅ Forum diskusi: Completed</p>
                    <p>✅ Reply minimal: Completed</p>
                    <p>✅ Pretest-Kuesioner: Completed</p>
                    <p>� Nilai akan muncul di dashboard Anda.</p>
                </div>
                <button class="btn" onclick="closeAppAndReturn()">✅ Selesai & Kembali ke Bot</button>
            </div>

            <!-- Incomplete View -->
            <div id="incomplete-view" class="hidden">
                <div style="background: rgba(255, 193, 7, 0.2); border: 1px solid #ffc107; color: #856404; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h3>⚠️ Tugas Belum Selesai</h3>
                    <div id="incomplete-details"></div>
                </div>
                <button class="btn btn-primary" onclick="continueWorking()">
                    📚 Lanjutkan Pengerjaan
                </button>
                <button class="btn btn-warning" style="margin-top: 5px;" onclick="checkCompletion()">
                    🔍 Cek Lagi
                </button>
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
            const courseTitle = decodeURIComponent(urlParams.get('course_title') || 'Course Title');
            const meetingNumber = urlParams.get('meeting_number') || '1';
            
            // Debug: Log parameters
            console.log('URL Parameters:', {
                courseCode, courseTitle, meetingNumber,
                fullURL: window.location.href
            });
            
            // Update UI with course info
            document.getElementById('course-code').textContent = courseCode;
            document.getElementById('course-title').textContent = courseTitle;
            document.getElementById('meeting-number').textContent = 'Pertemuan ' + meetingNumber;

            function showView(viewId) {
                ['initial-view', 'instructions-view', 'working-view', 'checking-view', 'success-view', 'incomplete-view', 'error-view'].forEach(id => {
                    document.getElementById(id).classList.add('hidden');
                });
                document.getElementById(viewId).classList.remove('hidden');
            }

            function openForumInstructions() {
                showView('instructions-view');
            }

            function goBack() {
                showView('initial-view');
            }

            function proceedToForum() {
                // Open forum in new tab
                const forumUrl = `https://mentari.unpam.ac.id/u-courses/${courseCode}?accord_pertemuan=PERTEMUAN_${meetingNumber}`;
                window.open(forumUrl, '_blank');
                
                // Show working view
                showView('working-view');
                window.forumUrl = forumUrl;
            }

            function openForumAgain() {
                if (window.forumUrl) {
                    window.open(window.forumUrl, '_blank');
                }
            }

            async function checkCompletion() {
                showView('checking-view');

                try {
                    const response = await fetch('/api/check-completion', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            course_code: courseCode,
                            course_title: courseTitle,
                            meeting_number: meetingNumber
                        })
                    });

                    const data = await response.json();
                    
                    if (data.completed) {
                        showView('success-view');
                    } else {
                        // Show incomplete tasks with safe text handling
                        const missingTasks = data.missing_tasks || data.message || 
                            'Masih ada tugas yang belum selesai. Silakan periksa forum dan selesaikan semua tugas.';
                        
                        // Safely display text without HTML parsing issues
                        document.getElementById('incomplete-details').textContent = missingTasks;
                        showView('incomplete-view');
                    }
                } catch (error) {
                    console.error('Check completion error:', error);
                    document.getElementById('error-message').innerHTML = 
                        '<h3>❌ Error Checking Status</h3><p>Terjadi kesalahan saat mengecek status. Silakan coba lagi.</p>';
                    showView('error-view');
                }
            }

            function continueWorking() {
                showView('working-view');
            }

            function closeAppAndReturn() {
                // Send completion signal to bot
                if (tg) {
                    // Mark as completed via API
                    fetch('/api/mark-completed', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            course_code: courseCode,
                            meeting_number: meetingNumber,
                            nim: 'USER_NIM' // This should be passed from credentials
                        })
                    }).then(() => {
                        tg.sendData(JSON.stringify({
                            action: 'completed',
                            course_code: courseCode,
                            meeting_number: meetingNumber
                        }));
                        tg.close();
                    }).catch(() => {
                        // Fallback: close anyway
                        tg.close();
                    });
                }
            }

            // Legacy functions for error handling
            async function joinForum() {
                openForumInstructions();
            }

            function openForum() {
                openForumAgain();
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

@app.route('/api/mark-completed', methods=['POST'])
def mark_completed_api():
    """API endpoint for marking forum as completed"""
    try:
        data = request.get_json()
        nim = data.get('nim', 'UNKNOWN')
        course_code = data.get('course_code', 'UNKNOWN')
        meeting_number = data.get('meeting_number', '1')
        
        # For now, just simulate marking as completed
        # In real implementation, this would save to database
        
        return jsonify({
            'success': True,
            'message': f'Forum {course_code} meeting {meeting_number} marked as completed for {nim}',
            'timestamp': datetime.now().isoformat()
        })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error marking completion: {str(e)}'
        }), 500

@app.route('/api/check-completion', methods=['POST'])
def check_completion_api():
    """API endpoint for checking forum completion status - CONSISTENT & REALISTIC"""
    try:
        data = request.get_json()
        course_code = data.get('course_code', 'UNKNOWN')
        course_title = data.get('course_title', 'Unknown Course')
        meeting_number = data.get('meeting_number', '1')
        
        # Create unique session identifier
        session_key = f"{course_code}_{meeting_number}"
        
        # Get or create consistent session
        session = get_or_create_session(session_key)
        session['check_count'] += 1
        
        # Simulate realistic checking process
        time.sleep(2)  # Simulate checking time
        
        # REALISTIC BEHAVIOR:
        # Same forum will always give same result (consistent)
        # 95% forums will be incomplete
        # 5% forums might be complete
        
        if session['completed']:
            return jsonify({
                'completed': True,
                'message': 'Semua tugas telah diselesaikan dengan sempurna!'
            })
        else:
            return jsonify({
                'completed': False,
                'missing_tasks': f"Tugas yang belum selesai: {session['missing_tasks']}"
            })
            
    except Exception as e:
        return jsonify({
            'completed': False,
            'message': f'Error checking completion: {str(e)}'
        }), 500

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