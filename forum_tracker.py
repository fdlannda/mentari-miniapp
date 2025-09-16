"""
Forum Completion Tracker
Simple file-based system to track user forum completion status
"""

import json
import os
from datetime import datetime
from typing import Dict, List

COMPLETION_FILE = "data/forum_completions.json"

def ensure_data_dir():
    """Ensure data directory exists"""
    os.makedirs("data", exist_ok=True)

def load_completions() -> Dict:
    """Load completion data from file"""
    ensure_data_dir()
    try:
        if os.path.exists(COMPLETION_FILE):
            with open(COMPLETION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_completions(data: Dict):
    """Save completion data to file"""
    ensure_data_dir()
    try:
        with open(COMPLETION_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving completions: {e}")

def mark_forum_completed(nim: str, course_code: str, meeting_number: str):
    """Mark a forum as completed for a user"""
    completions = load_completions()
    
    if nim not in completions:
        completions[nim] = []
    
    completion_record = {
        'course_code': course_code,
        'meeting_number': meeting_number,
        'completed_at': datetime.now().isoformat(),
        'status': 'completed'
    }
    
    # Check if already exists, if yes update, if no add
    existing_index = None
    for i, record in enumerate(completions[nim]):
        if (record.get('course_code') == course_code and 
            record.get('meeting_number') == meeting_number):
            existing_index = i
            break
    
    if existing_index is not None:
        completions[nim][existing_index] = completion_record
    else:
        completions[nim].append(completion_record)
    
    save_completions(completions)

def get_user_completions(nim: str) -> List[Dict]:
    """Get all completions for a user"""
    completions = load_completions()
    return completions.get(nim, [])

def is_forum_completed(nim: str, course_code: str, meeting_number: str) -> bool:
    """Check if a specific forum is completed by user"""
    user_completions = get_user_completions(nim)
    
    for completion in user_completions:
        if (completion.get('course_code') == course_code and 
            completion.get('meeting_number') == meeting_number and
            completion.get('status') == 'completed'):
            return True
    
    return False

def get_completion_stats(nim: str) -> Dict:
    """Get completion statistics for a user"""
    user_completions = get_user_completions(nim)
    completed_count = len([c for c in user_completions if c.get('status') == 'completed'])
    
    return {
        'total_completed': completed_count,
        'completions': user_completions,
        'last_completion': user_completions[-1] if user_completions else None
    }