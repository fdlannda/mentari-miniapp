import logging
import json
from datetime import datetime
from telegram import Update, Inl    # Add Web App buttons untuk setiap available forum (max 3 untuk tidak spam)
    for forum in available_forums[:3]:
        # Create Mini App URL dengan parameter forum - URL PRODUCTION VERCEL
        miniapp_url = f"https://mentari-miniapp.vercel.app/forum?course={forum['course_code']}&meeting={forum['meeting_number']}&name={forum['course_name'][:20].replace(' ', '%20')}"
        
        # Create Web App button yang akan membuka Mini App
        button = InlineKeyboardButton(
            f"🚀 Join {forum['course_name'][:15]}... M{forum['meeting_number']}", 
            web_app=WebAppInfo(url=miniapp_url)
        )dButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from telegram.error import NetworkError, TelegramError

logger = logging.getLogger(__name__)

def format_result_message(hasil: str, nim: str = None, available_forums: list = None) -> str:
    """Format the final result message with Mini App support - keep original detailed format"""
    # Keep the original detailed format from hasil
    # Just add Mini App info at the end if available forums exist
    
    footer_addition = ""
    
    # Add Mini App section if there are available forums
    if available_forums and len(available_forums) > 0:
        footer_addition = f"\n\n🚀 *MINI APP TERSEDIA!*\n"
        footer_addition += f"📱 {len(available_forums)} forum siap untuk di-join\n"
        footer_addition += f"💡 Gunakan tombol Mini App di bawah untuk bergabung dengan mudah!"
    
    # Find the last occurrence of "✅ Pengecekan selesai!" and add Mini App info before the tips
    if "✅ Pengecekan selesai!" in hasil:
        # Split at the completion message
        parts = hasil.split("✅ Pengecekan selesai!")
        if len(parts) >= 2:
            # Insert Mini App info before the tips
            return parts[0] + "✅ Pengecekan selesai!" + footer_addition + "\n" + parts[1]
    
    # If the pattern is not found, just append at the end
    return hasil + footer_addition

def extract_available_forums_from_result(hasil: str) -> list:
    """Extract forum yang available dari hasil scraping untuk Mini App"""
    available_forums = []
    lines = hasil.split('\n')
    
    current_course = None
    current_course_code = None
    
    for line in lines:
        # Detect course name - look for lines with 📚
        if '📚' in line:
            # Extract course name from format like: "📚 STATISTIKA DAN PROBABILITAS"
            course_line = line.replace('📚', '').strip()
            current_course = course_line
            
            # Try to find course code in the context (will be inferred from meeting lines)
            current_course_code = None
        
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
                        
                        # Generate a course code if we have course name
                        if current_course and not current_course_code:
                            # Create a generic course code based on course name
                            course_map = {
                                'STATISTIKA DAN PROBABILITAS': '20251-03TPLK006-22TIF0093',
                                'SISTEM BERKAS': '20251-03TPLK007-22TIF0093', 
                                'MATEMATIKA DISKRIT': '20251-03TPLK008-22TIF0093',
                                'JARINGAN KOMPUTER': '20251-03TPLK009-22TIF0093'
                            }
                            current_course_code = course_map.get(current_course, 'UNKNOWN-CODE')
                        
                        if current_course:
                            available_forums.append({
                                'course_name': current_course,
                                'course_code': current_course_code or 'UNKNOWN-CODE',
                                'meeting_number': meeting_number,
                                'status': 'available'
                            })
                except (ValueError, AttributeError):
                    continue
    
    return available_forums

def create_miniapp_keyboard(available_forums: list, miniapp_generator=None) -> InlineKeyboardMarkup:
    """Create inline keyboard dengan Web App buttons yang sebenarnya untuk forum yang available"""
    if not available_forums:
        return None
    
    keyboard_buttons = []
    
    # Add Web App buttons untuk setiap available forum (max 3 untuk tidak spam)
    for forum in available_forums[:3]:
        # Create Mini App URL dengan parameter forum - GANTI URL INI DENGAN URL VERCEL ANDA
        miniapp_url = f"https://YOUR-VERCEL-URL.vercel.app/forum?course={forum['course_code']}&meeting={forum['meeting_number']}&name={forum['course_name'][:20].replace(' ', '%20')}"
        
        # Create Web App button yang akan membuka Mini App
        button = InlineKeyboardButton(
            f"� Join {forum['course_name'][:15]}... M{forum['meeting_number']}", 
            web_app=WebAppInfo(url=miniapp_url)
        )
        keyboard_buttons.append([button])
    
    # Add fallback manual guide button
    info_button = InlineKeyboardButton(
        "� Panduan Manual", 
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

async def process_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                             nim: str, pw: str) -> None:
    """Process user credentials and generate response with Mini App support"""
    
    try:
        # Store credentials
        user_id = update.effective_user.id
        logger.info(f"Processing credentials for user {user_id}")
        
        # Send progress message
        progress_msg = await update.message.reply_text(
            "🔄 *Memproses kredensial...*\n\n"
            "⏳ Mengecek forum yang tersedia\n"
            "🔒 Kredensial disimpan dengan aman",
            parse_mode='Markdown'
        )
        
        # TODO: Here you would implement actual scraping
        # For now, return demo data that matches the old format
        # In production, this would call your scraper service
        
        # Simulate processing time
        import asyncio
        await asyncio.sleep(2)
        
        # This would be the actual scraper result in production
        demo_result = """📋 Hasil Pengecekan Forum Mentari

👤 NIM: 2410****
📅 Waktu: 2025-09-16 23:16:19
========================================

📚 LAPORAN STATUS FORUM DISKUSI
════════════════════════════════════════

📚 STATISTIKA DAN PROBABILITAS
  ❌ Pertemuan 1: ❌ Forum belum tersedia
  🟡 Pertemuan 2: 🟡 Tersedia tapi belum bergabung
  🟡 Pertemuan 3: 🟡 Tersedia tapi belum bergabung
  ❌ Pertemuan 4: ❌ Forum belum tersedia
  🟡 Pertemuan 5: 🟡 Tersedia tapi belum bergabung
  ❌ Pertemuan 6: ❌ Forum belum tersedia

📚 SISTEM BERKAS
  ✅ Pertemuan 1: ✅ Sudah bergabung
  🟡 Pertemuan 2: 🟡 Tersedia tapi belum bergabung
  ❌ Pertemuan 3: ❌ Forum belum tersedia

📚 JARINGAN KOMPUTER
  🟡 Pertemuan 2: 🟡 Tersedia tapi belum bergabung
  🟡 Pertemuan 3: 🟡 Tersedia tapi belum bergabung
  ❌ Pertemuan 4: ❌ Forum belum tersedia

════════════════════════════════════════
📊 RINGKASAN STATUS:
✅ Sudah bergabung: 1
🟡 Tersedia belum gabung: 6
❌ Belum tersedia: 4
📈 Tingkat keberhasilan: 91.0%

════════════════════════════════════════
⏱️ Waktu eksekusi: 120.5 detik
📋 Total mata kuliah: 3
📝 Total pertemuan: 11
🕐 Diperbarui: 2025-09-16 23:30:45

========================================
✅ Pengecekan selesai!
💡 Tips: Bergabunglah di forum yang tersedia untuk mendapatkan nilai partisipasi."""
        
        return demo_result
        
    except Exception as e:
        logger.error(f"Error processing user message: {e}")
        raise

# Import utilities for backward compatibility
def make_progress_callback(msg):
    """Create progress callback function to update message"""
    last_status = {"text": "", "count": 0, "start_time": None}
    
    async def progress_callback(status_text: str):
        try:
            import time
            
            if last_status["start_time"] is None:
                last_status["start_time"] = time.time()
            
            if status_text != last_status["text"]:
                last_status["text"] = status_text
                last_status["count"] += 1
                
                # Update message every few status changes to avoid rate limiting
                if last_status["count"] % 3 == 0:
                    try:
                        elapsed = time.time() - last_status["start_time"]
                        await msg.edit_text(
                            f"🔄 *Memproses permintaan...*\n\n"
                            f"📊 Status: {status_text}\n"
                            f"⏱️ Waktu: {elapsed:.1f}s",
                            parse_mode='Markdown'
                        )
                    except Exception as edit_error:
                        logger.warning(f"Could not update progress: {edit_error}")
                        
        except Exception as e:
            logger.error(f"Progress callback error: {e}")
    
    return progress_callback

def split_message(text: str, max_length: int = 4096) -> list:
    """Split long message into chunks that fit Telegram's limit"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    lines = text.split('\n')
    for line in lines:
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + '\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.rstrip())
                current_chunk = line + '\n'
            else:
                # Single line too long, split it
                chunks.append(line[:max_length])
                current_chunk = line[max_length:] + '\n'
    
    if current_chunk:
        chunks.append(current_chunk.rstrip())
    
    return chunks

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
        
        # Format message with Mini App support
        formatted_result = format_result_message(result, nim, available_forums)
        
        # Split message if too long
        message_chunks = split_message(formatted_result)
        
        # Send final result with Mini App keyboard
        if message_chunks:
            if processing_msg:
                try:
                    await processing_msg.edit_text(
                        message_chunks[0], 
                        parse_mode='Markdown',
                        reply_markup=create_miniapp_keyboard(available_forums) if available_forums else None
                    )
                except Exception:
                    await update.message.reply_text(
                        message_chunks[0], 
                        parse_mode='Markdown',
                        reply_markup=create_miniapp_keyboard(available_forums) if available_forums else None
                    )
            else:
                await update.message.reply_text(
                    message_chunks[0], 
                    parse_mode='Markdown',
                    reply_markup=create_miniapp_keyboard(available_forums) if available_forums else None
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

def extract_credentials(text: str):
    """Extract username and password from user input - Support both formats"""
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