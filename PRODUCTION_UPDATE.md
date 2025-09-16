
# Production Configuration Update

# File: helper.py
# Update line ~165:

config = MiniAppConfig(
    bot_token=env_config.telegram_token,
    app_url=os.getenv('MINIAPP_URL', 'https://mentari-miniapp.yourdomain.com'),
    app_name=os.getenv('MINIAPP_BOT_NAME', 'mentari_unpam')
)

# File: .env (add these lines):
MINIAPP_URL=https://mentari-miniapp.yourdomain.com
MINIAPP_BOT_NAME=mentari_unpam
