#!/usr/bin/env python3
"""
Test script untuk debug session isolation berdasarkan course code
"""

import hashlib

def test_session_keys():
    """Test session key generation untuk course codes berbeda"""
    
    test_courses = [
        "20251-03TPLK006-22TIF0093_2",  # STATISTIKA DAN PROBABILITAS Meeting 2
        "20251-03TPLK006-22TIF0152_2",  # SISTEM BERKAS Meeting 2
        "20251-03TPLK006-22TIF0142_2",  # MATEMATIKA DISKRIT Meeting 2
        "20251-03TPLK006-22TIF0133_2",  # JARINGAN KOMPUTER Meeting 2
        "20251-03TPLK006-22TIF0093_1",  # STATISTIKA DAN PROBABILITAS Meeting 1
    ]
    
    print("=== TEST SESSION KEY ISOLATION ===\n")
    
    for session_key in test_courses:
        # Generate session hash (sama seperti di API)
        session_hash = int(hashlib.md5(session_key.encode()).hexdigest()[:8], 16)
        hash_mod = session_hash % 100
        
        # Test completion rates
        pretest_done = hash_mod < 80
        forum_done = hash_mod < 15
        posttest_done = hash_mod < 8
        kuesioner_done = hash_mod < 3
        
        print(f"Session Key: {session_key}")
        print(f"Hash: {session_hash}")
        print(f"Hash % 100: {hash_mod}")
        print(f"Completion Status:")
        print(f"  - Pretest: {'✅' if pretest_done else '❌'} ({hash_mod} < 80)")
        print(f"  - Forum: {'✅' if forum_done else '❌'} ({hash_mod} < 15)")
        print(f"  - Posttest: {'✅' if posttest_done else '❌'} ({hash_mod} < 8)")
        print(f"  - Kuesioner: {'✅' if kuesioner_done else '❌'} ({hash_mod} < 3)")
        print("-" * 50)

if __name__ == "__main__":
    test_session_keys()