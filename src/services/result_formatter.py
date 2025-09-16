"""
Service untuk formatting hasil scraping
"""

import logging
from typing import Dict, List
from src.models import ScrapingResult, CourseResult, MeetingInfo, ForumStatus


logger = logging.getLogger(__name__)


class ResultFormatterService:
    """Service untuk formatting hasil scraping menjadi pesan yang readable"""
    
    def format_scraping_result(self, result: ScrapingResult) -> str:
        """
        Format hasil scraping lengkap menjadi pesan Telegram
        
        Args:
            result: ScrapingResult object
            
        Returns:
            str: Formatted message
        """
        
        if not result.courses:
            return "📭 Tidak ada data forum yang ditemukan."
        
        # Build message parts
        message_parts = []
        
        # Header
        message_parts.append("📚 *LAPORAN STATUS FORUM DISKUSI*")
        message_parts.append("═" * 40)
        
        # Course details
        for course_result in result.courses:
            message_parts.append(self._format_course_result(course_result))
        
        # Summary statistics
        message_parts.append(self._format_summary_statistics(result))
        
        # Footer with metadata
        message_parts.append(self._format_footer(result))
        
        return "\n".join(message_parts)
    
    def format_course_result(self, course_result: CourseResult) -> str:
        """
        Format hasil untuk satu mata kuliah
        
        Args:
            course_result: CourseResult object
            
        Returns:
            str: Formatted course result
        """
        
        message_parts = []
        
        # Course header
        message_parts.append(f"📚 *{course_result.course.name}*")
        message_parts.append(f"📋 Kode: `{course_result.course.code}`")
        message_parts.append("")
        
        # Meeting details
        for meeting in course_result.meetings_status:
            message_parts.append(self._format_meeting_info(meeting))
        
        # Course summary
        if len(course_result.meetings_status) > 1:
            message_parts.append(self._format_course_summary(course_result))
        
        return "\n".join(message_parts)
    
    def _format_course_result(self, course_result: CourseResult) -> str:
        """Format hasil untuk satu mata kuliah (internal)"""
        
        parts = []
        
        # Course header
        parts.append(f"\n📚 *{course_result.course.name}*")
        
        # Meeting statuses
        for meeting in course_result.meetings_status:
            parts.append(f"  {self._get_status_emoji(meeting.status)} {meeting.message}")
        
        return "\n".join(parts)
    
    def _format_meeting_info(self, meeting: MeetingInfo) -> str:
        """Format informasi satu pertemuan"""
        
        emoji = self._get_status_emoji(meeting.status)
        
        # Basic message
        result = f"{emoji} {meeting.message}"
        
        # Add screenshot info if available
        if meeting.screenshot_path:
            result += f" 📸"
        
        # Add error details for debug mode
        if meeting.error_details and meeting.status in [ForumStatus.ERROR, ForumStatus.TIMEOUT]:
            # Truncate long error messages
            error_preview = meeting.error_details[:100] + "..." if len(meeting.error_details) > 100 else meeting.error_details
            result += f"\n    ℹ️ Detail: `{error_preview}`"
        
        return result
    
    def _format_summary_statistics(self, result: ScrapingResult) -> str:
        """Format statistik ringkasan"""
        
        # Calculate totals
        total_joined = sum(course.joined_count for course in result.courses)
        total_available = sum(course.available_count for course in result.courses)
        total_unavailable = sum(course.unavailable_count for course in result.courses)
        total_errors = sum(course.error_count for course in result.courses)
        
        parts = []
        parts.append("\n" + "═" * 40)
        parts.append("📊 *RINGKASAN STATUS:*")
        parts.append(f"✅ Sudah bergabung: *{total_joined}*")
        parts.append(f"🟡 Tersedia belum gabung: *{total_available}*")
        parts.append(f"❌ Belum tersedia: *{total_unavailable}*")
        
        if total_errors > 0:
            parts.append(f"❗ Error/Tidak terdeteksi: *{total_errors}*")
        
        # Success rate
        if result.total_meetings > 0:
            parts.append(f"📈 Tingkat keberhasilan: *{result.success_rate:.1f}%*")
        
        return "\n".join(parts)
    
    def _format_course_summary(self, course_result: CourseResult) -> str:
        """Format ringkasan untuk satu mata kuliah"""
        
        parts = []
        parts.append("  ────────────────")
        
        summary_items = []
        if course_result.joined_count > 0:
            summary_items.append(f"✅ {course_result.joined_count}")
        if course_result.available_count > 0:
            summary_items.append(f"🟡 {course_result.available_count}")
        if course_result.unavailable_count > 0:
            summary_items.append(f"❌ {course_result.unavailable_count}")
        if course_result.error_count > 0:
            summary_items.append(f"❗ {course_result.error_count}")
        
        if summary_items:
            parts.append(f"  📊 {' | '.join(summary_items)}")
        
        return "\n".join(parts)
    
    def _format_footer(self, result: ScrapingResult) -> str:
        """Format footer dengan metadata"""
        
        parts = []
        parts.append("\n" + "═" * 40)
        
        # Execution info
        parts.append(f"⏱️ Waktu eksekusi: {result.execution_time:.1f} detik")
        parts.append(f"📋 Total mata kuliah: {result.total_courses}")
        parts.append(f"📝 Total pertemuan: {result.total_meetings}")
        
        # Timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        parts.append(f"🕐 Diperbarui: {timestamp}")
        
        return "\n".join(parts)
    
    def _get_status_emoji(self, status: ForumStatus) -> str:
        """Get emoji untuk status forum"""
        
        emoji_map = {
            ForumStatus.JOINED: "✅",
            ForumStatus.AVAILABLE: "🟡", 
            ForumStatus.UNAVAILABLE: "❌",
            ForumStatus.UNKNOWN: "❔",
            ForumStatus.ERROR: "❗",
            ForumStatus.TIMEOUT: "⏰"
        }
        
        return emoji_map.get(status, "❓")
    
    def format_quick_summary(self, result: ScrapingResult) -> str:
        """Format ringkasan singkat untuk notifikasi"""
        
        if not result.courses:
            return "📭 Tidak ada data forum"
        
        # Calculate totals
        total_joined = sum(course.joined_count for course in result.courses)
        total_available = sum(course.available_count for course in result.courses)
        total_unavailable = sum(course.unavailable_count for course in result.courses)
        total_errors = sum(course.error_count for course in result.courses)
        
        parts = []
        parts.append("📊 Status Forum:")
        
        status_parts = []
        if total_joined > 0:
            status_parts.append(f"✅{total_joined}")
        if total_available > 0:
            status_parts.append(f"🟡{total_available}")
        if total_unavailable > 0:
            status_parts.append(f"❌{total_unavailable}")
        if total_errors > 0:
            status_parts.append(f"❗{total_errors}")
        
        parts.append(" | ".join(status_parts))
        parts.append(f"({result.success_rate:.0f}% berhasil)")
        
        return " ".join(parts)
    
    def format_error_message(self, error: Exception) -> str:
        """Format pesan error yang user-friendly"""
        
        error_str = str(error).lower()
        
        # Common error patterns
        if "timeout" in error_str:
            return "⏰ Koneksi timeout. Server mungkin sedang lambat, coba lagi nanti."
        elif "network" in error_str or "connection" in error_str:
            return "🌐 Masalah koneksi internet. Periksa koneksi Anda."
        elif "login" in error_str or "credential" in error_str:
            return "🔐 Login gagal. Periksa NIM dan password Anda."
        elif "captcha" in error_str:
            return "🔒 Gagal menyelesaikan CAPTCHA. Coba lagi nanti."
        elif "browser" in error_str:
            return "🖥️ Masalah browser. Restart aplikasi dan coba lagi."
        else:
            # Generic error with truncated message
            error_preview = str(error)[:100] + "..." if len(str(error)) > 100 else str(error)
            return f"❌ Terjadi kesalahan: {error_preview}"
