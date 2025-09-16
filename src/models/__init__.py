"""
Data models untuk Bot Mentari UNPAM
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class ForumStatus(Enum):
    """Status forum diskusi"""
    JOINED = "joined"                    # ✅ Sudah bergabung
    AVAILABLE = "available"              # 🟡 Tersedia tapi belum bergabung  
    UNAVAILABLE = "unavailable"          # ❌ Forum belum tersedia
    UNKNOWN = "unknown"                  # ❔ Status tidak terdeteksi
    ERROR = "error"                      # ❗ Error saat mengecek
    TIMEOUT = "timeout"                  # ⏰ Timeout


@dataclass
class MeetingInfo:
    """Informasi pertemuan"""
    number: int
    status: ForumStatus
    message: str
    screenshot_path: Optional[str] = None
    error_details: Optional[str] = None


@dataclass
class CourseInfo:
    """Informasi mata kuliah"""
    code: str
    name: str
    meetings: List[int]
    
    def __post_init__(self):
        """Validasi data setelah inisialisasi"""
        if not self.code or not self.name:
            raise ValueError("Course code and name are required")
        if not self.meetings:
            raise ValueError("At least one meeting is required")


@dataclass
class CourseResult:
    """Hasil scraping untuk satu mata kuliah"""
    course: CourseInfo
    meetings_status: List[MeetingInfo]
    total_meetings: int
    joined_count: int
    available_count: int
    unavailable_count: int
    error_count: int
    
    @classmethod
    def from_course_info(cls, course: CourseInfo) -> 'CourseResult':
        """Create empty result from course info"""
        return cls(
            course=course,
            meetings_status=[],
            total_meetings=len(course.meetings),
            joined_count=0,
            available_count=0,
            unavailable_count=0,
            error_count=0
        )
    
    def add_meeting_result(self, meeting: MeetingInfo):
        """Add meeting result and update counters"""
        self.meetings_status.append(meeting)
        
        if meeting.status == ForumStatus.JOINED:
            self.joined_count += 1
        elif meeting.status == ForumStatus.AVAILABLE:
            self.available_count += 1
        elif meeting.status == ForumStatus.UNAVAILABLE:
            self.unavailable_count += 1
        else:
            self.error_count += 1


@dataclass
class ScrapingResult:
    """Hasil lengkap scraping semua mata kuliah"""
    courses: List[CourseResult]
    total_courses: int
    total_meetings: int
    success_rate: float
    execution_time: float
    
    @classmethod
    def from_course_results(cls, course_results: List[CourseResult], execution_time: float) -> 'ScrapingResult':
        """Create from list of course results"""
        total_meetings = sum(result.total_meetings for result in course_results)
        successful_checks = sum(
            result.joined_count + result.available_count + result.unavailable_count 
            for result in course_results
        )
        success_rate = (successful_checks / total_meetings * 100) if total_meetings > 0 else 0
        
        return cls(
            courses=course_results,
            total_courses=len(course_results),
            total_meetings=total_meetings,
            success_rate=success_rate,
            execution_time=execution_time
        )


@dataclass
class LoginCredentials:
    """Kredensial login"""
    nim: str
    password: str
    
    def __post_init__(self):
        """Validasi kredensial"""
        if not self.nim or not self.password:
            raise ValueError("NIM and password are required")


@dataclass
class BrowserConfig:
    """Konfigurasi browser"""
    headless: bool = True
    slow_mo: int = 0
    viewport_width: int = 2560  # Increased for 75% zoom equivalent
    viewport_height: int = 1440  # Increased for 75% zoom equivalent
    timeout: int = 45000
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    args: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Set default args if not provided"""
        if self.args is None:
            self.args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-blink-features=AutomationControlled'
            ]
