#!/usr/bin/env python3
"""
Quick Setup & Run Script untuk Unified Mentari UNPAM Bot
Script untuk setup dan menjalankan aplikasi unified dengan mudah
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_requirements():
    """Check apakah semua requirements sudah terpenuhi"""
    print("🔍 Checking requirements...")
    
    missing_packages = []
    required_packages = [
        'flask',
        'flask_cors', 
        'telegram',
        'playwright'
    ]
    
    for package in required_packages:
        try:
            if package == 'flask_cors':
                __import__('flask_cors')
            else:
                __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package}")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        # Map back to pip package names
        pip_packages = []
        for pkg in missing_packages:
            if pkg == 'telegram':
                pip_packages.append('python-telegram-bot')
            elif pkg == 'flask_cors':
                pip_packages.append('flask-cors')
            else:
                pip_packages.append(pkg)
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + pip_packages)
    
    return len(missing_packages) == 0

def check_config():
    """Check configuration files"""
    print("\n🔧 Checking configuration...")
    
    config_ok = True
    
    # Check bot_config.json
    if not os.path.exists('bot_config.json'):
        print("   ❌ bot_config.json not found")
        config_ok = False
        
        # Create template
        template_config = {
            "telegram_token": "YOUR_BOT_TOKEN_HERE",
            "captcha_api_key": "YOUR_CAPTCHA_API_KEY_HERE"
        }
        
        with open('bot_config.json', 'w') as f:
            json.dump(template_config, f, indent=2)
        
        print("   📄 Created bot_config.json template")
        print("   ⚠️  Please update with your actual tokens!")
    else:
        print("   ✅ bot_config.json exists")
        
        # Validate config
        try:
            with open('bot_config.json', 'r') as f:
                config = json.load(f)
                
            if config.get('telegram_token', '').startswith('YOUR_'):
                print("   ⚠️  Please update telegram_token in bot_config.json")
                config_ok = False
            else:
                print("   ✅ telegram_token configured")
                
        except Exception as e:
            print(f"   ❌ Error reading bot_config.json: {e}")
            config_ok = False
    
    # Check required directories
    dirs_to_create = ['logs', 'data', 'src/integrations']
    for dir_path in dirs_to_create:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"   📁 Created directory: {dir_path}")
        else:
            print(f"   ✅ Directory exists: {dir_path}")
    
    return config_ok

def run_unified_bot():
    """Run the unified bot application"""
    print("\n🚀 Starting Unified Mentari UNPAM Bot...")
    print("=" * 60)
    print("🤖 Bot: Telegram polling active")
    print("🌐 Mini App: Web server on localhost:5000") 
    print("🔗 Access: http://localhost:5000")
    print("=" * 60)
    print("📝 Press Ctrl+C to stop")
    print()
    
    try:
        # Run unified application
        subprocess.run([sys.executable, 'main_unified.py'])
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error running bot: {e}")

def main():
    """Main setup and run function"""
    print("🎯 UNIFIED MENTARI UNPAM BOT - QUICK SETUP")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('main_unified.py'):
        print("❌ main_unified.py not found!")
        print("Please run this script from the project root directory.")
        return
    
    # Check requirements
    if not check_requirements():
        print("❌ Failed to install requirements")
        return
    
    # Check configuration
    if not check_config():
        print("\n❌ Configuration incomplete!")
        print("Please update bot_config.json with your actual tokens.")
        print("Then run this script again.")
        return
    
    print("\n✅ All checks passed!")
    
    # Ask user if ready to start
    response = input("\n🚀 Ready to start the unified bot? (y/n): ").lower()
    if response in ['y', 'yes']:
        run_unified_bot()
    else:
        print("👋 Setup complete. Run 'python main_unified.py' when ready.")

if __name__ == '__main__':
    main()