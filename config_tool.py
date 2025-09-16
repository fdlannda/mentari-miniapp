#!/usr/bin/env python3
"""
Simple Config Tool - Tool mudah untuk mengatur konfigurasi bot
Usage: python config_tool.py [command] [options]

Commands:
  set-mode [production|development|debug]  - Set mode operasi
  set-delay [request_delay] [course_delay] - Set delay settings
  toggle [setting_name]                    - Toggle boolean setting
  show                                     - Show current config
  fast                                     - Quick setup for maximum speed
  safe                                     - Quick setup for safe operation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.bot_controller import ModeController

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    controller = ModeController()
    command = sys.argv[1].lower()
    
    if command == 'set-mode':
        if len(sys.argv) < 3:
            print("❌ Mode required. Available: production, development, debug")
            return
        mode = sys.argv[2].lower()
        controller.set_mode(mode)
    
    elif command == 'set-delay':
        if len(sys.argv) < 4:
            print("❌ Both request_delay and course_delay required")
            print("Example: python config_tool.py set-delay 0.5 0.7")
            return
        try:
            request_delay = float(sys.argv[2])
            course_delay = float(sys.argv[3])
            controller.update_delays(request_delay, course_delay)
        except ValueError:
            print("❌ Delays must be numbers")
    
    elif command == 'toggle':
        if len(sys.argv) < 3:
            print("❌ Setting name required")
            print("Available: headless_mode, enable_screenshots, debug_mode, pause_on_error")
            return
        setting = sys.argv[2]
        controller.toggle_setting(setting)
    
    elif command == 'show':
        controller.show_current_config()
    
    elif command == 'fast':
        print("🚀 Setting up for MAXIMUM SPEED...")
        controller.set_mode('production')
        controller.update_delays(0.4, 0.6)  # Super fast
        print("✅ Bot configured for maximum speed!")
    
    elif command == 'safe':
        print("🛡️  Setting up for SAFE OPERATION...")
        controller.set_mode('development')
        controller.update_delays(1.5, 2.0)  # Conservative
        print("✅ Bot configured for safe operation!")
    
    elif command == 'help':
        print(__doc__)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python config_tool.py help' for usage")

if __name__ == "__main__":
    main()