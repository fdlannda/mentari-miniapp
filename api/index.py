from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Mini App</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
    </head>
    <body>
        <h1>🎓 Test Mini App</h1>
        <p>Mini App berhasil dimuat!</p>
        <button onclick="alert('Test berhasil!')">Test Button</button>
        
        <script>
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.ready();
                window.Telegram.WebApp.expand();
            }
        </script>
    </body>
    </html>
    '''

@app.route('/api/test')
def test():
    return {'status': 'ok', 'message': 'API works!'}

if __name__ == '__main__':
    app.run(debug=True)