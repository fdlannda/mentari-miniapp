#!/usr/bin/env python3
"""
Wrapper script untuk menjalankan bot_controller.py dengan path yang benar
"""

import os
import sys

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import and run bot controller
from scripts.bot_controller import ModeController

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Mentari UNPAM Bot Controller')
    parser.add_argument('action', choices=['status', 'production', 'development', 'debug', 'custom', 'reset', 'retry'], 
                        help='Action to perform')
    parser.add_argument('--value', type=int, help='Value untuk action retry (jumlah retry attempts)')
    
    args = parser.parse_args()
    controller = ModeController()
    
    if args.action == 'status':
        controller.show_current_status()
    elif args.action == 'production':
        controller.set_mode('production')
    elif args.action == 'development':
        controller.set_mode('development')
    elif args.action == 'debug':
        controller.set_mode('debug')
    elif args.action == 'custom':
        controller.custom_configure()
    elif args.action == 'reset':
        controller.reset_to_default()
    elif args.action == 'retry':
        if args.value is not None:
            controller.set_retry_count(args.value)
        else:
            print("❌ Gunakan --value untuk mengatur jumlah retry attempts")
            print("   Contoh: python run_bot_controller.py retry --value 5")
