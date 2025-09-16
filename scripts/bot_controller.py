#!/usr/bin/env python3
"""
Advanced Mode Controller untuk Bot Mentari UNPAM
Sistem manajemen konfigurasi yang powerful dan user-friendly dengan ConfigManager
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from config import AppSettings, ConfigManager
from core.bot_service import MentariBotCore
from models import LoginCredentials


class ModeController:
    """Advanced controller untuk mengelola mode operasi bot dengan ConfigManager"""
    
    def __init__(self):
        self.config_file = "bot_config.json"
        self.config_manager = ConfigManager()
        self.load_current_config()
    
    def load_current_config(self):
        """Load konfigurasi saat ini dari file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                settings = self._dict_to_settings(config_data)
                self.config_manager.config = settings
            else:
                # Start with production mode sebagai default
                self.config_manager.switch_mode('production')
                self.save_current_config()
        except Exception as e:
            print(f"⚠️  Error loading config: {e}")
            self.config_manager.switch_mode('production')
    
    def save_current_config(self):
        """Save konfigurasi saat ini ke file"""
        try:
            config_data = self._settings_to_dict(self.config_manager.config)
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving config: {e}")
    
    def _settings_to_dict(self, settings: AppSettings) -> Dict[str, Any]:
        """Convert AppSettings to dictionary"""
        return {
            'debug_mode': settings.debug_mode,
            'headless_mode': settings.headless_mode,
            'enable_screenshots': settings.enable_screenshots,
            'enable_video_recording': settings.enable_video_recording,
            'pause_on_error': settings.pause_on_error,
            'detailed_logging': settings.detailed_logging,
            'delay_between_requests': settings.delay_between_requests,
            'delay_between_courses': settings.delay_between_courses,
            'max_retries': settings.max_retries,
            'screenshot_dir': settings.screenshot_dir,
            'video_dir': settings.video_dir,
            'log_dir': settings.log_dir,
            'data_dir': settings.data_dir
        }
    
    def _dict_to_settings(self, data: Dict[str, Any]) -> AppSettings:
        """Convert dictionary to AppSettings"""
        return AppSettings(
            debug_mode=data.get('debug_mode', False),
            headless_mode=data.get('headless_mode', True),
            enable_screenshots=data.get('enable_screenshots', False),
            enable_video_recording=data.get('enable_video_recording', False),
            pause_on_error=data.get('pause_on_error', False),
            detailed_logging=data.get('detailed_logging', False),
            delay_between_requests=data.get('delay_between_requests', 0.6),
            delay_between_courses=data.get('delay_between_courses', 0.8),
            max_retries=data.get('max_retries', 3),
            screenshot_dir=data.get('screenshot_dir', 'screenshots'),
            video_dir=data.get('video_dir', 'recordings'),
            log_dir=data.get('log_dir', 'logs'),
            data_dir=data.get('data_dir', 'data')
        )
    
    def set_mode(self, mode: str):
        """Set mode operasi bot menggunakan ConfigManager"""
        try:
            old_mode = self.config_manager.get_current_mode()
            self.config_manager.switch_mode(mode)
            self.save_current_config()
            
            print(f"✅ Mode berhasil diubah dari {old_mode} ke {self.config_manager.get_current_mode()}")
            self.show_current_config()
            
        except ValueError as e:
            print(f"❌ Error: {e}")
            print("Available modes: production, development, debug")
    
    def update_delays(self, request_delay: float = None, course_delay: float = None):
        """Update delay settings untuk performance tuning"""
        updates = {}
        if request_delay is not None:
            updates['delay_between_requests'] = request_delay
        if course_delay is not None:
            updates['delay_between_courses'] = course_delay
        
        if updates:
            try:
                self.config_manager.update_config(**updates)
                self.save_current_config()
                print(f"✅ Delay settings updated:")
                if request_delay is not None:
                    print(f"   Request delay: {request_delay}s")
                if course_delay is not None:
                    print(f"   Course delay: {course_delay}s")
            except Exception as e:
                print(f"❌ Error updating delays: {e}")
    
    def toggle_setting(self, setting_name: str):
        """Toggle boolean setting"""
        current_value = getattr(self.config_manager.config, setting_name, None)
        if isinstance(current_value, bool):
            try:
                self.config_manager.update_config(**{setting_name: not current_value})
                self.save_current_config()
                print(f"✅ {setting_name}: {current_value} → {not current_value}")
            except Exception as e:
                print(f"❌ Error toggling {setting_name}: {e}")
        else:
            print(f"❌ {setting_name} is not a boolean setting")
    
    def show_current_config(self):
        """Tampilkan konfigurasi saat ini"""
        config_summary = self.config_manager.get_config_summary()
        print(f"\n📋 Current Mode: {config_summary['mode']}")
        print("⚙️  Configuration:")
        print(f"   Headless: {config_summary['headless']}")
        print(f"   Screenshots: {config_summary['screenshots']}")
        print(f"   Debug: {config_summary['debug']}")
        print(f"   Pause on Error: {config_summary['pause_on_error']}")
        print(f"   Request Delay: {config_summary['delay_requests']}s")
        print(f"   Course Delay: {config_summary['delay_courses']}s\n")
    
    def get_current_settings(self) -> AppSettings:
        """Dapatkan settings yang sedang aktif"""
        return self.config_manager.config


def main():
    """Main function untuk mode controller"""
    controller = ModeController()
    
    if len(sys.argv) < 2:
        print("🤖 MENTARI BOT - MODE CONTROLLER")
        print("=" * 45)
        controller.show_current_config()
        
        print("📋 PERINTAH YANG TERSEDIA:")
        print("  python bot_controller.py [mode]     - Set mode: production, development, debug")
        print("  python bot_controller.py show       - Lihat konfigurasi saat ini")
        print("  python config_tool.py [command]     - Tool konfigurasi lengkap")
        return
    
    command = sys.argv[1].lower()
    
    if command in ['production', 'development', 'debug']:
        controller.set_mode(command)
        
    elif command == 'show':
        controller.show_current_config()
        
    else:
        print(f"❌ Perintah tidak dikenal: {command}")
        print("Available commands: production, development, debug, show")


if __name__ == "__main__":
    main()
    main()
