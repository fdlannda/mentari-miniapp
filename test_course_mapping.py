#!/usr/bin/env python3
"""
Test script untuk simulate course code generation dari available_forums
"""

def test_course_code_generation():
    """Test course code mapping logic from helper.py - UPDATED LOGIC"""
    
    # Simulate course data dengan mapping yang BENAR
    course_names = [
        'STATISTIKA DAN PROBABILITAS',
        'JARINGAN KOMPUTER', 
        'SISTEM BERKAS',
        'MATEMATIKA DISKRIT'
    ]
    
    print("=== TEST COURSE CODE MAPPING LOGIC (UPDATED) ===\n")
    
    # Logic yang sama seperti di helper.py (UPDATED)
    course_map = {
        'STATISTIKA DAN PROBABILITAS': '20251-03TPLK006-22TIF0093',
        'SISTEM BERKAS': '20251-03TPLK006-22TIF0152', 
        'MATEMATIKA DISKRIT': '20251-03TPLK006-22TIF0142',
        'JARINGAN KOMPUTER': '20251-03TPLK006-22TIF0133'
    }
    
    # Generate available_forums dengan logic yang sudah diperbaiki
    available_forums = []
    for course_name in course_names:
        meeting_number = 2  # Example meeting
        
        # Always prioritize mapping over any extracted code
        final_course_code = course_map.get(course_name)
        
        # Only add if we have a valid mapping
        if final_course_code:
            available_forums.append({
                'course_name': course_name,
                'course_code': final_course_code,  # Now always correct!
                'meeting_number': meeting_number,
                'status': 'available'
            })
    
    print("STEP 1: Available Forums Generation (Fixed)")
    for forum in available_forums:
        print(f"  {forum['course_name']}: {forum['course_code']}")
    print()
    
    print("STEP 2: Mini App URL Generation")
    # Course code mapping for Mini App (same as above, for consistency)
    course_code_mapping = {
        'STATISTIKA DAN PROBABILITAS': '20251-03TPLK006-22TIF0093',
        'STATISTIKA DAN PROB': '20251-03TPLK006-22TIF0093',
        'SISTEM BERKAS': '20251-03TPLK006-22TIF0152',
        'MATEMATIKA DISKRIT': '20251-03TPLK006-22TIF0142',
        'JARINGAN KOMPUTER': '20251-03TPLK006-22TIF0133'
    }
    
    for forum in available_forums:
        # Get actual course code from mapping (should always exist now)
        actual_course_code = course_code_mapping.get(forum['course_name'])
        
        # Skip if no mapping found (safety check)
        if not actual_course_code:
            print(f"WARNING: No course code mapping for: {forum['course_name']}")
            continue
        
        # Generate Mini App URL
        miniapp_url = f"https://mentari-miniapp.vercel.app/forum?course_code={actual_course_code}&course_title={forum['course_name'][:30].replace(' ', '%20')}&meeting_number={forum['meeting_number']}"
        
        print(f"Course: {forum['course_name']}")
        print(f"  Original Code: {forum['course_code']} ✅")
        print(f"  Mapped Code: {actual_course_code} ✅") 
        print(f"  Meeting: {forum['meeting_number']}")
        print(f"  Status: {'CONSISTENT' if forum['course_code'] == actual_course_code else 'INCONSISTENT'}")
        print(f"  Mini App URL: {miniapp_url}")
        print("-" * 70)

if __name__ == "__main__":
    test_course_code_generation()