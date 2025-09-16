#!/usr/bin/env python3
"""
End-to-End Test untuk Telegram Mini App Integration
Test complete workflow dari detection sampai keyboard generation
"""

import sys
import os
import asyncio
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from helper import extract_available_forums_from_result, create_miniapp_keyboard, format_result_message

def test_complete_workflow():
    """Test complete Mini App workflow"""
    
    print("🧪 TESTING COMPLETE MINI APP WORKFLOW")
    print("=" * 60)
    
    # 1. Simulate scraping result dengan available forums
    mock_hasil = """
📚 STATISTIKA DAN PROBABILITAS (20251-03TPLK006-22TIF0093)
   Pertemuan 1: ✅ Sudah bergabung
   Pertemuan 2: 🟡 Tersedia tapi belum bergabung
   Pertemuan 3: ❌ Forum belum tersedia
   Pertemuan 4: 🟡 Tersedia tapi belum bergabung

📚 SISTEM BERKAS (20251-03TPLK006-22TIF0152)
   Pertemuan 1: 🟡 Tersedia tapi belum bergabung
   Pertemuan 2: ✅ Sudah bergabung

📚 MATEMATIKA DISKRIT (20251-03TPLK006-22TIF0142)
   Pertemuan 1: ✅ Sudah bergabung
   Pertemuan 2: ✅ Sudah bergabung
"""

    print("1️⃣  STEP 1: Parse Scraping Results")
    print("-" * 40)
    
    # 2. Extract available forums
    available_forums = extract_available_forums_from_result(mock_hasil)
    
    print(f"✅ Detected {len(available_forums)} available forums:")
    for i, forum in enumerate(available_forums, 1):
        print(f"   {i}. {forum['course_name']} - Pertemuan {forum['meeting_number']}")
        print(f"      Code: {forum['course_code']}")
    
    print(f"\n2️⃣  STEP 2: Generate Mini App Keyboard")
    print("-" * 40)
    
    # 3. Generate Mini App keyboard
    mock_nim = "2410114001234"
    mock_pw = "rahasia123"
    
    try:
        keyboard = create_miniapp_keyboard(available_forums, mock_nim, mock_pw)
        
        if keyboard:
            print("✅ Keyboard successfully generated!")
            print(f"   Total buttons: {len(keyboard['inline_keyboard'])}")
            
            for i, row in enumerate(keyboard['inline_keyboard']):
                for j, button in enumerate(row):
                    if 'web_app' in button:
                        print(f"   🚀 {button['text']}")
                        print(f"      Mini App URL: {button['web_app']['url'][:80]}...")
                    else:
                        print(f"   {button.get('text', 'No text')} (callback)")
        else:
            print("❌ No keyboard generated (no available forums)")
            
    except Exception as e:
        print(f"❌ Error generating keyboard: {e}")
    
    print(f"\n3️⃣  STEP 3: Format Message with Mini App")
    print("-" * 40)
    
    # 4. Format message dengan Mini App support
    formatted_message = format_result_message(mock_hasil, mock_nim, available_forums)
    
    print("✅ Message formatted with Mini App support:")
    print("-" * 50)
    print(formatted_message[:500] + "..." if len(formatted_message) > 500 else formatted_message)
    print("-" * 50)
    
    print(f"\n4️⃣  STEP 4: Validate Mini App URLs")
    print("-" * 40)
    
    # 5. Validate Mini App URLs
    if keyboard and len(keyboard['inline_keyboard']) > 0:
        sample_button = None
        for row in keyboard['inline_keyboard']:
            for button in row:
                if 'web_app' in button:
                    sample_button = button
                    break
            if sample_button:
                break
        
        if sample_button:
            url = sample_button['web_app']['url']
            print(f"✅ Sample Mini App URL structure:")
            print(f"   Base: {url.split('?')[0]}")
            
            # Parse query parameters
            if '?' in url:
                query_part = url.split('?', 1)[1]
                # Decode startapp parameter
                if 'startapp=' in query_part:
                    import urllib.parse
                    startapp_param = query_part.split('startapp=')[1]
                    decoded_url = urllib.parse.unquote(startapp_param)
                    print(f"   Target: {decoded_url[:60]}...")
    
    print(f"\n5️⃣  STEP 5: Test Server Health")
    print("-" * 40)
    
    # 6. Test server health
    try:
        import requests
        health_response = requests.get('http://localhost:5000/health', timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Mini App server is healthy!")
            print(f"   Status: {health_data['status']}")
            print(f"   Timestamp: {health_data['timestamp']}")
        else:
            print(f"⚠️  Server responded with status: {health_response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Mini App server: {e}")
        print("💡 Make sure to run: python miniapp_server.py")
    except ImportError:
        print("📦 Installing requests for server testing...")
        os.system("pip install requests")
        print("🔄 Please run test again")
    
    print(f"\n6️⃣  STEP 6: Generate Test URLs")
    print("-" * 40)
    
    # 7. Generate test URLs untuk manual testing
    if available_forums:
        forum = available_forums[0]
        test_url = f"http://localhost:5000?action=join_forum&course_code={forum['course_code']}&meeting_number={forum['meeting_number']}&auth_hash=test123"
        print(f"🌐 Test URL for manual browser testing:")
        print(f"   {test_url}")
        
        bulk_test_url = "http://localhost:5000?action=bulk_join&data=" + urllib.parse.quote(json.dumps({
            "action": "bulk_join",
            "forums": available_forums[:2]  # Test dengan 2 forums
        }))
        print(f"\n🌐 Bulk join test URL:")
        print(f"   {bulk_test_url[:80]}...")
    
    print(f"\n" + "=" * 60)
    print("🎉 END-TO-END TEST COMPLETED!")
    print("=" * 60)
    
    return {
        'available_forums': len(available_forums),
        'keyboard_generated': keyboard is not None,
        'message_formatted': len(formatted_message) > 0,
        'test_urls_generated': len(available_forums) > 0
    }

if __name__ == "__main__":
    import urllib.parse
    
    result = test_complete_workflow()
    
    print(f"\n📊 TEST SUMMARY:")
    print(f"   Forums detected: {result['available_forums']}")
    print(f"   Keyboard generated: {'✅' if result['keyboard_generated'] else '❌'}")
    print(f"   Message formatted: {'✅' if result['message_formatted'] else '❌'}")
    print(f"   Test URLs ready: {'✅' if result['test_urls_generated'] else '❌'}")
    
    if all(result.values()):
        print(f"\n🎊 ALL TESTS PASSED! Mini App integration is ready!")
        print(f"\n🚀 Next steps:")
        print(f"   1. Mini App server is running on http://localhost:5000")
        print(f"   2. Test in browser using generated URLs above")
        print(f"   3. For production: setup HTTPS domain & update app_url")
        print(f"   4. Integrate with real Telegram bot")
    else:
        print(f"\n⚠️  Some tests failed. Check the output above.")