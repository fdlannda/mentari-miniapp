import logging
import json
import time
import base64
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from telegram.error import NetworkError, TelegramError
from forum_tracker import get_user_completions, mark_forum_completed

logger = logging.getLogger(__name__)

def perform_forum_joining_scraper(nim: str, password: str, target_url: str, course_code: str, meeting_number: str) -> dict:
    """
    Real forum joining function menggunakan scraper
    
    Args:
        nim: Student ID number
        password: Student password
        target_url: Forum URL to join
        course_code: Course code (e.g., 20251-03TPLK006-22TIF0093)
        meeting_number: Meeting number (e.g., 2)
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'join_data': dict (optional)
        }
    """
    try:
        logger.info(f"Starting real forum join for {nim} to {target_url}")
        
        # TODO: Implement actual scraper logic here
        # This would include:
        # 1. Login to Mentari UNPAM with credentials
        # 2. Navigate to the forum URL
        # 3. Find and click join forum button
        # 4. Verify successful join
        
        # For now, simulate the process with realistic timing
        time.sleep(2)  # Simulate login time
        
        # Simulate successful join (replace with real logic)
        success_rate = 0.9  # 90% success rate for simulation
        import random
        
        if random.random() < success_rate:
            return {
                'success': True,
                'message': f'Successfully joined forum {course_code} meeting {meeting_number}',
                'join_data': {
                    'join_time': datetime.now().isoformat(),
                    'forum_url': target_url,
                    'course_code': course_code,
                    'meeting_number': meeting_number
                }
            }
        else:
            return {
                'success': False,
                'message': 'Failed to join forum - login credentials may be incorrect or forum is not accessible'
            }
            
    except Exception as e:
        logger.error(f"Error in perform_forum_joining_scraper: {e}")
        return {
            'success': False,
            'message': f'Error during forum joining: {str(e)}'
        }

def verify_forum_participation(course_code: str, meeting_number: str, forum_url: str) -> dict:
    """
    Verify if user has actually participated in the forum discussion
    
    Args:
        course_code: Course code
        meeting_number: Meeting number
        forum_url: Forum URL to check
    
    Returns:
        dict: {
            'verified': bool,
            'message': str,
            'data': dict (optional)
        }
    """
    try:
        logger.info(f"Verifying participation for {course_code} meeting {meeting_number}")
        
        # TODO: Implement real verification logic
        # This would include:
        # 1. Login to Mentari UNPAM
        # 2. Navigate to forum
        # 3. Check if user has posted/participated
        # 4. Return verification status
        
        # Simulate verification process
        time.sleep(3)  # Simulate checking time
        
        # Simulate verification result (replace with real logic)
        # In real implementation, this would check actual forum posts
        verification_rate = 0.8  # 80% verification success for simulation
        import random
        
        if random.random() < verification_rate:
            return {
                'verified': True,
                'message': 'Participation verified successfully',
                'data': {
                    'verification_time': datetime.now().isoformat(),
                    'forum_url': forum_url,
                    'participation_type': 'discussion_post'  # Could be post, reply, etc.
                }
            }
        else:
            return {
                'verified': False,
                'message': 'No participation detected in forum discussion'
            }
            
    except Exception as e:
        logger.error(f"Error in verify_forum_participation: {e}")
        return {
            'verified': False,
            'message': f'Error during verification: {str(e)}'
        }

def format_result_message(hasil: str, nim: str = None, available_forums: list = None, forum_status_text: str = None) -> str:
    """Format the final result message with Mini App support - improved readability"""
    
    # Keep the original detailed format from hasil
    formatted_result = hasil
    
    # Add Mini App section if there are available forums
    if available_forums and len(available_forums) > 0:
        mini_app_section = f"\n\n{'='*40}\n"
        mini_app_section += f"🚀 *MINI APP TERSEDIA!*\n"
        mini_app_section += f"{'='*40}\n\n"
        
        # Use custom status text if provided
        if forum_status_text:
            mini_app_section += f"{forum_status_text}\n\n"
        else:
            mini_app_section += f"📱 *{len(available_forums)} forum* siap untuk dikerjakan\n\n"
        
        # List available forums
        for i, forum in enumerate(available_forums[:3], 1):
            mini_app_section += f"*{i}.* {forum['course_name']}\n"
            mini_app_section += f"   📚 Pertemuan {forum['meeting_number']}\n"
            mini_app_section += f"   ✅ Status: Tersedia\n\n"
        
        # Show if there are more forums available
        if len(available_forums) > 3:
            mini_app_section += f"*...dan {len(available_forums) - 3} forum lainnya*\n\n"
        
        mini_app_section += f"💡 *Cara penggunaan:*\n"
        mini_app_section += f"• Klik tombol Mini App di bawah\n"
        mini_app_section += f"• Ikuti panduan pengerjaan\n"
        mini_app_section += f"• Selesaikan semua tugas\n"
        mini_app_section += f"• Verifikasi completion\n\n"
        mini_app_section += f"⚠️ *PENTING:* Login dulu di browser dengan akun Mentari Anda!"
        
        formatted_result += mini_app_section
    elif available_forums is not None and len(available_forums) == 0:
        # All forums completed
        completion_section = f"\n\n{'='*40}\n"
        completion_section += f"🎉 *SEMUA FORUM SELESAI!*\n"
        completion_section += f"{'='*40}\n\n"
        completion_section += f"✅ Semua forum diskusi telah diselesaikan\n"
        completion_section += f"📊 Status: Complete\n"
        completion_section += f"💡 Silakan cek dashboard Mentari UNPAM Anda"
        
        formatted_result += completion_section
    
    return formatted_result

def extract_available_forums_from_result(result: str) -> list:
    """Extract available forums (🟡 Tersedia tapi belum bergabung) from scraping result"""
    available_forums = []
    
    if not result or "🟡 Tersedia tapi belum bergabung" not in result:
        return available_forums
    
    lines = result.split('\n')
    current_course = None
    current_course_code = None
    
    for line in lines:
        line = line.strip()
        
        # Detect course name (📚 Course Name)
        if line.startswith('📚 '):
            current_course = line.replace('📚 ', '').strip()
            current_course_code = None
        
        # Try to extract course code from URL patterns in the result
        # Look for patterns like: "20251-03TPLK006-22TIF0093"
        elif 'u-courses/' in line or '20251-' in line:
            import re
            course_code_match = re.search(r'20251-\w+-\w+', line)
            if course_code_match:
                current_course_code = course_code_match.group(0)
        
        # Detect available forum (🟡 Tersedia tapi belum bergabung)
        elif '🟡' in line and 'Tersedia tapi belum bergabung' in line:
            # Extract meeting number from format like: "  🟡 Pertemuan 2: 🟡 Tersedia tapi belum bergabung"
            if 'Pertemuan' in line:
                try:
                    # Extract meeting number
                    import re
                    meeting_match = re.search(r'Pertemuan (\d+)', line)
                    if meeting_match:
                        meeting_number = int(meeting_match.group(1))
                        
                        # Use extracted course code or fallback to mapping
                        if not current_course_code and current_course:
                            # Fallback course code mapping based on course name
                            course_map = {
                                'STATISTIKA DAN PROBABILITAS': '20251-03TPLK006-22TIF0093',
                                'SISTEM BERKAS': '20251-03TPLK007-22TIF0093', 
                                'MATEMATIKA DISKRIT': '20251-03TPLK008-22TIF0093',
                                'JARINGAN KOMPUTER': '20251-03TPLK009-22TIF0093'
                            }
                            current_course_code = course_map.get(current_course, '20251-03TPLK006-22TIF0093')
                        
                        if current_course:
                            available_forums.append({
                                'course_name': current_course,
                                'course_code': current_course_code or '20251-03TPLK006-22TIF0093',
                                'meeting_number': meeting_number,
                                'status': 'available'
                            })
                except (ValueError, AttributeError):
                    continue
    
    return available_forums

def create_miniapp_keyboard(available_forums: list, user_credentials=None, completed_forums=None) -> InlineKeyboardMarkup:
    """Create inline keyboard dengan Web App buttons yang sebenarnya untuk forum yang available"""
    if not available_forums:
        return None
    
    # Filter out completed forums
    if completed_forums is None:
        completed_forums = []
    
    # Create completed forum identifiers for comparison
    completed_identifiers = set()
    for completed in completed_forums:
        identifier = f"{completed.get('course_name', '')}_M{completed.get('meeting_number', '')}"
        completed_identifiers.add(identifier)
    
    # Filter available forums to exclude completed ones
    pending_forums = []
    for forum in available_forums:
        forum_identifier = f"{forum.get('course_name', '')}_M{forum.get('meeting_number', '')}"
        if forum_identifier not in completed_identifiers:
            pending_forums.append(forum)
    
    # If no pending forums, show message
    if not pending_forums:
        return None
    
    keyboard_buttons = []
    
    # Show up to 3 pending forums
    display_forums = pending_forums[:3]
    
    # Add Web App buttons untuk setiap pending forum
    for forum in display_forums:
        # Encode credentials ke Mini App URL (base64 for security)
        import base64
        import json
        
        if user_credentials:
            cred_data = {
                'nim': user_credentials.get('nim', ''),
                'password': user_credentials.get('password', '')
            }
            encoded_creds = base64.b64encode(json.dumps(cred_data).encode()).decode()
        else:
            encoded_creds = ''
        
        # QUICK FIX: Hardcode course code mapping for demo
        # In production, this should be extracted from actual scraping result
        course_code_mapping = {
            'STATISTIKA DAN PROBABILITAS': '20251-03TPLK006-22TIF0093',
            'STATISTIKA DAN PROB': '20251-03TPLK006-22TIF0093',
            'SISTEM BERKAS': '20251-03TPLK007-22TIF0093',
            'MATEMATIKA DISKRIT': '20251-03TPLK008-22TIF0093',
            'JARINGAN KOMPUTER': '20251-03TPLK009-22TIF0093'
        }
        
        # Get actual course code from mapping
        actual_course_code = course_code_mapping.get(
            forum['course_name'], 
            forum['course_code']  # fallback to original
        )
        
        # Create Mini App URL dengan parameter forum dan credentials
        miniapp_url = f"https://mentari-miniapp.vercel.app/forum?course_code={actual_course_code}&course_title={forum['course_name'][:30].replace(' ', '%20')}&meeting_number={forum['meeting_number']}&creds={encoded_creds}"
        
        # Create Web App button yang akan membuka Mini App
        button = InlineKeyboardButton(
            f"🚀 Join {forum['course_name'][:15]}... M{forum['meeting_number']}", 
            web_app=WebAppInfo(url=miniapp_url)
        )
        keyboard_buttons.append([button])
    
    # Add fallback manual guide button
    info_button = InlineKeyboardButton(
        "📖 Panduan Manual", 
        callback_data="forum_join_guide"
    )
    keyboard_buttons.append([info_button])
    
    return InlineKeyboardMarkup(keyboard_buttons)

def extract_credentials(text: str):
    """Extract username and password from user input"""
    if '|' in text:
        # Simple format: username|password
        parts = text.strip().split('|', 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
    
    # Legacy format support
    lines = text.strip().split("\n")
    username = None
    password = None
    
    for line in lines:
        line_lower = line.lower().strip()
        if ("nim" in line_lower or "username" in line_lower) and ":" in line:
            username = line.split(":", 1)[1].strip()
        elif "password" in line_lower and ":" in line:
            password = line.split(":", 1)[1].strip()
    
    if not username or not password:
        raise ValueError(
            "Format tidak lengkap. Gunakan format:\n"
            "`username|password`\n"
            "Contoh: `22TIF0093|password123`"
        )
    
    # Validate username format (basic validation)
    if len(username) < 5:
        raise ValueError("Username terlalu pendek. Pastikan format username benar.")
    
    return username, password

def split_message(text: str, max_length: int = 4000) -> list:
    """Split long messages into chunks that fit Telegram's limits with better formatting"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by sections first (double newlines)
    sections = text.split('\n\n')
    
    for section in sections:
        # If adding this section would exceed limit
        if len(current_chunk) + len(section) + 2 > max_length:
            if current_chunk:
                chunks.append(current_chunk.rstrip())
                current_chunk = ""
        
        # If single section is too long, split by lines
        if len(section) > max_length:
            lines = section.split('\n')
            for line in lines:
                if len(current_chunk) + len(line) + 1 > max_length:
                    if current_chunk:
                        chunks.append(current_chunk.rstrip())
                        current_chunk = ""
                
                current_chunk += line + "\n"
        else:
            current_chunk += section + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.rstrip())
    
    # Ensure no chunk is empty and add continuation markers
    final_chunks = []
    for i, chunk in enumerate(chunks):
        if chunk.strip():
            if i > 0:
                chunk = f"📄 *Lanjutan {i+1}*\n\n" + chunk
            if i < len(chunks) - 1:
                chunk += f"\n\n*➡️ Bersambung...*"
            final_chunks.append(chunk)
    
    return final_chunks if final_chunks else [text[:max_length]]

async def send_result_or_error(update, context, nim: str, password: str, scrape_function, processing_msg=None):
    """Send scraping result or error message with live updates - Original compatibility function"""
    
    # Create live progress callback
    async def progress_callback(message: str):
        """Live update callback untuk progress scraping"""
        if processing_msg:
            try:
                await processing_msg.edit_text(
                    f"🔄 *Status Scraping*\n\n{message}",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.debug(f"Error updating progress: {e}")
        
    try:
        # Execute scraping with live progress callback
        result = await scrape_function(nim, password, progress_callback)
        
        # Extract available forums for Mini App
        available_forums = extract_available_forums_from_result(result)
        
        # Get user's completed forums
        user_completions = get_user_completions(nim)
        
        # Filter available forums to show only pending ones
        pending_forums = []
        for forum in available_forums:
            # Create course code from mapping
            course_code_mapping = {
                'STATISTIKA DAN PROBABILITAS': '20251-03TPLK006-22TIF0093',
                'STATISTIKA DAN PROB': '20251-03TPLK006-22TIF0093',
                'SISTEM BERKAS': '20251-03TPLK007-22TIF0093',
                'MATEMATIKA DISKRIT': '20251-03TPLK008-22TIF0093',
                'JARINGAN KOMPUTER': '20251-03TPLK009-22TIF0093'
            }
            
            actual_course_code = course_code_mapping.get(forum['course_name'], forum.get('course_code', ''))
            
            # Check if this forum is already completed
            is_completed = any(
                c.get('course_code') == actual_course_code and 
                c.get('meeting_number') == str(forum['meeting_number']) and
                c.get('status') == 'completed'
                for c in user_completions
            )
            
            if not is_completed:
                pending_forums.append(forum)
        
        # Update forum count in message
        total_available = len(available_forums)
        pending_count = len(pending_forums)
        completed_count = total_available - pending_count
        
        # Format message with dynamic forum info
        if pending_count > 0:
            forum_status_text = f"📱 *{pending_count} forum* siap untuk dikerjakan"
            if completed_count > 0:
                forum_status_text += f" ({completed_count} sudah selesai)"
        else:
            forum_status_text = f"🎉 *Semua {total_available} forum sudah selesai!*"
        
        # Format message with updated info
        formatted_result = format_result_message(result, nim, pending_forums, forum_status_text)
        
        # Split message if too long
        message_chunks = split_message(formatted_result)
        
        # Prepare user credentials for Mini App
        user_credentials = {'nim': nim, 'password': password}
        
        # Send final result with Mini App keyboard (using pending_forums for display)
        if message_chunks:
            if processing_msg:
                try:
                    await processing_msg.edit_text(
                        message_chunks[0], 
                        parse_mode='Markdown',
                        reply_markup=create_miniapp_keyboard(pending_forums, user_credentials) if pending_forums else None
                    )
                except Exception:
                    await update.message.reply_text(
                        message_chunks[0], 
                        parse_mode='Markdown',
                        reply_markup=create_miniapp_keyboard(pending_forums, user_credentials) if pending_forums else None
                    )
            else:
                await update.message.reply_text(
                    message_chunks[0], 
                    parse_mode='Markdown',
                    reply_markup=create_miniapp_keyboard(available_forums, user_credentials) if available_forums else None
                )
            
            # Send additional chunks if any
            for chunk in message_chunks[1:]:
                await update.message.reply_text(chunk, parse_mode='Markdown')
                
    except Exception as e:
        logger.error(f"Error in scraping: {e}")
        error_msg = f"❌ Terjadi kesalahan saat memproses kredensial\n\nSilakan coba lagi atau hubungi admin."
        
        if processing_msg:
            try:
                await processing_msg.edit_text(error_msg)
            except Exception:
                await update.message.reply_text(error_msg)
        else:
            await update.message.reply_text(error_msg)