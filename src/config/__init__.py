"""
Konfigurasi aplikasi untuk Bot Mentari UNPAM
"""

import os
from typing import List, Optional
from dataclasses import dataclass
from src.models import BrowserConfig, CourseInfo


@dataclass
class AppSettings:
    """Pengaturan aplikasi"""
    
    # Mode operasi
    debug_mode: bool = False
    headless_mode: bool = False
    enable_screenshots: bool = False
    enable_video_recording: bool = False
    pause_on_error: bool = False
    detailed_logging: bool = False
    
    # Performance settings - Optimized for speed
    delay_between_requests: float = 0.8  # Reduced from 1.5
    delay_between_courses: float = 1.0   # Reduced from 2.0
    max_retries: int = 3
    
    # Paths
    screenshot_dir: str = "screenshots"
    video_dir: str = "recordings"
    log_dir: str = "logs"
    data_dir: str = "data"
    
    # Browser configuration
    browser_config: Optional[BrowserConfig] = None
    
    def __post_init__(self):
        """Initialize browser config if not provided"""
        if self.browser_config is None:
            self.browser_config = BrowserConfig(
                headless=self.headless_mode,
                slow_mo=1000 if not self.headless_mode else 0
            )
    
    def update_settings(self, **kwargs):
        """Update settings dinamis dengan validasi"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                # Validasi tipe data
                current_value = getattr(self, key)
                if isinstance(current_value, bool) and not isinstance(value, bool):
                    raise ValueError(f"{key} must be a boolean, got {type(value)}")
                elif isinstance(current_value, (int, float)) and not isinstance(value, (int, float)):
                    raise ValueError(f"{key} must be a number, got {type(value)}")
                elif isinstance(current_value, str) and not isinstance(value, str):
                    raise ValueError(f"{key} must be a string, got {type(value)}")
                
                setattr(self, key, value)
                
                # Update browser config jika diperlukan
                if key in ['headless_mode'] and self.browser_config:
                    self.browser_config.headless = self.headless_mode
                    self.browser_config.slow_mo = 1000 if not self.headless_mode else 0
            else:
                raise ValueError(f"Unknown setting: {key}")
    
    def get_mode_name(self) -> str:
        """Dapatkan nama mode saat ini"""
        if self.headless_mode and not self.enable_screenshots and not self.pause_on_error:
            return "Production"
        elif not self.headless_mode and self.enable_screenshots and not self.pause_on_error:
            return "Development"
        elif self.pause_on_error and self.detailed_logging:
            return "Debug"
        else:
            return "Custom"
    
    @classmethod
    def production_mode(cls) -> 'AppSettings':
        """Konfigurasi untuk mode produksi - dioptimalkan untuk kecepatan"""
        return cls(
            debug_mode=False,
            headless_mode=True,  # Fixed: should be True for production
            enable_screenshots=False,
            enable_video_recording=False,
            pause_on_error=False,
            detailed_logging=False,
            delay_between_requests=0.6,  # Optimized for speed
            delay_between_courses=0.8,   # Optimized for speed
            browser_config=BrowserConfig(
                headless=True,
                slow_mo=0,
                timeout=30000  # Reduced timeout
            )
        )
    
    @classmethod
    def development_mode(cls) -> 'AppSettings':
        """Konfigurasi untuk mode development"""
        return cls(
            debug_mode=True,
            headless_mode=False,
            enable_screenshots=True,
            enable_video_recording=True,
            pause_on_error=False,
            detailed_logging=True,
            delay_between_requests=2.0,
            delay_between_courses=3.0
        )
    
    @classmethod
    def debug_mode(cls) -> 'AppSettings':
        """Konfigurasi untuk mode debug"""
        return cls(
            debug_mode=True,
            headless_mode=False,
            enable_screenshots=True,
            enable_video_recording=True,
            pause_on_error=True,
            detailed_logging=True,
            delay_between_requests=3.0,
            delay_between_courses=5.0,
            browser_config=BrowserConfig(
                headless=False,
                slow_mo=2000
            )
        )


class EnvironmentConfig:
    """Konfigurasi dari environment variables"""
    
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
        
        # Telegram Bot
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        if not self.telegram_token:
            raise ValueError("TELEGRAM_TOKEN environment variable is required")
        
        # 2captcha
        self.captcha_api_key = os.getenv('CAPTCHA_API_KEY')
        if not self.captcha_api_key:
            raise ValueError("CAPTCHA_API_KEY environment variable is required")
        
        # Mentari UNPAM
        self.mentari_base_url = os.getenv('MENTARI_BASE_URL', 'https://mentari.unpam.ac.id')
        
        # Optional settings
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.max_concurrent_sessions = int(os.getenv('MAX_CONCURRENT_SESSIONS', '1'))


class ConfigManager:
    """Manager untuk mengelola konfigurasi secara dinamis"""
    
    def __init__(self, initial_config: AppSettings = None):
        self.config = initial_config or AppSettings.development_mode()
        self._config_history = []
    
    def switch_mode(self, mode: str) -> AppSettings:
        """Switch ke mode yang berbeda"""
        # Save current config to history
        self._config_history.append({
            'mode': self.config.get_mode_name(),
            'config': self.config
        })
        
        mode_lower = mode.lower()
        if mode_lower == 'production':
            self.config = AppSettings.production_mode()
        elif mode_lower == 'development':
            self.config = AppSettings.development_mode()
        elif mode_lower == 'debug':
            self.config = AppSettings.debug_mode()
        else:
            raise ValueError(f"Unknown mode: {mode}. Available modes: production, development, debug")
        
        return self.config
    
    def update_config(self, **kwargs) -> AppSettings:
        """Update konfigurasi current dengan validasi"""
        self.config.update_settings(**kwargs)
        return self.config
    
    def rollback_config(self) -> AppSettings:
        """Kembalikan ke konfigurasi sebelumnya"""
        if self._config_history:
            previous = self._config_history.pop()
            self.config = previous['config']
        return self.config
    
    def get_current_mode(self) -> str:
        """Dapatkan mode saat ini"""
        return self.config.get_mode_name()
    
    def get_config_summary(self) -> dict:
        """Dapatkan ringkasan konfigurasi current"""
        return {
            'mode': self.get_current_mode(),
            'headless': self.config.headless_mode,
            'delay_requests': self.config.delay_between_requests,
            'delay_courses': self.config.delay_between_courses,
            'screenshots': self.config.enable_screenshots,
            'debug': self.config.debug_mode,
            'pause_on_error': self.config.pause_on_error
        }
    
    def create_custom_config(self, **overrides) -> AppSettings:
        """Buat konfigurasi custom dengan override"""
        # Start with current config as base
        base_config = {
            'debug_mode': self.config.debug_mode,
            'headless_mode': self.config.headless_mode,
            'enable_screenshots': self.config.enable_screenshots,
            'enable_video_recording': self.config.enable_video_recording,
            'pause_on_error': self.config.pause_on_error,
            'detailed_logging': self.config.detailed_logging,
            'delay_between_requests': self.config.delay_between_requests,
            'delay_between_courses': self.config.delay_between_courses,
            'max_retries': self.config.max_retries,
        }
        
        # Apply overrides
        base_config.update(overrides)
        
        return AppSettings(**base_config)


class CourseConfiguration:
    """Konfigurasi mata kuliah yang akan di-scrape"""
    
    @staticmethod
    def get_default_courses() -> List[CourseInfo]:
        """Mata kuliah default untuk scraping - loaded from JSON"""
        import json
        import os
        
        try:
            # Load courses from JSON file
            json_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'courses.json')
            with open(json_file, 'r', encoding='utf-8') as file:
                courses_data = json.load(file)
            
            courses = []
            for course_data in courses_data:
                courses.append(CourseInfo(
                    code=course_data['code'],
                    name=course_data['name'],
                    meetings=course_data['meetings']
                ))
            
            return courses
            
        except Exception as e:
            # Fallback to match exactly with courses.json data
            return [
                CourseInfo(
                    code="20251-03TPLK006-22TIF0093",
                    name="STATISTIKA DAN PROBABILITAS",
                    meetings=[1, 2, 3]
                ),
                CourseInfo(
                    code="20251-03TPLK006-22TIF0152",
                    name="SISTEM BERKAS",
                    meetings=[1, 2, 3]
                ),
                CourseInfo(
                    code="20251-03TPLK006-22TIF0142",
                    name="MATEMATIKA DISKRIT",
                    meetings=[1, 2, 3]
                ),
                CourseInfo(
                    code="20251-03TPLK006-22TIF0133",
                    name="JARINGAN KOMPUTER",
                    meetings=[1, 2, 3]
                )
            ]
    
    @staticmethod
    def load_from_file(file_path: str) -> List[CourseInfo]:
        """Load course configuration from JSON file"""
        import json
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            courses = []
            for course_data in data:
                courses.append(CourseInfo(
                    code=course_data['code'],
                    name=course_data['name'],
                    meetings=course_data['meetings']
                ))
            
            return courses
            
        except FileNotFoundError:
            # Return default if file not found
            return CourseConfiguration.get_default_courses()
        except Exception as e:
            raise ValueError(f"Error loading course configuration: {e}")


# Global configuration instance
app_settings = AppSettings.production_mode()
env_config = EnvironmentConfig()
course_config = CourseConfiguration()
