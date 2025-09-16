"""
Core application service untuk Bot Mentari UNPAM
"""

import asyncio
import logging
import time
from typing import Optional, Callable, List
from playwright.async_api import async_playwright

from src.models import LoginCredentials, CourseInfo, ScrapingResult
from src.config import app_settings, course_config
from src.services.auth_service import MentariLoginService
from src.services.forum_scraper import ForumScraperService
from src.services.result_formatter import ResultFormatterService


logger = logging.getLogger(__name__)


class MentariBotCore:
    """Core service untuk Bot Mentari UNPAM"""
    
    def __init__(self, settings=None):
        self.settings = settings or app_settings
        self.auth_service = MentariLoginService(settings)
        self.scraper_service = ForumScraperService(settings)
        self.formatter_service = ResultFormatterService()
    
    async def execute_full_scraping(
        self,
        credentials: LoginCredentials,
        courses: Optional[List[CourseInfo]] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Execute full scraping process: login + scrape all courses
        
        Args:
            credentials: Login credentials
            courses: List of courses to scrape (default: all configured courses)
            progress_callback: Callback for progress updates
            
        Returns:
            str: Formatted result message
        """
        
        start_time = time.time()
        
        if not courses:
            courses = course_config.get_default_courses()
        
        logger.info(f"Starting full scraping for {len(courses)} courses")
        
        if progress_callback:
            await progress_callback("🚀 Memulai proses scraping...")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await self._launch_browser(p)
            
            try:
                # Create browser context with proper video recording setup
                context_options = {
                    'viewport': {
                        'width': self.settings.browser_config.viewport_width,
                        'height': self.settings.browser_config.viewport_height
                    },
                    'user_agent': self.settings.browser_config.user_agent
                }
                
                # Add video recording if enabled and not headless
                if self.settings.enable_video_recording and not self.settings.browser_config.headless:
                    import os
                    os.makedirs(self.settings.video_dir, exist_ok=True)
                    context_options['record_video_dir'] = self.settings.video_dir
                    context_options['record_video_size'] = {
                        'width': self.settings.browser_config.viewport_width,
                        'height': self.settings.browser_config.viewport_height
                    }
                
                context = await browser.new_context(**context_options)
                
                # Step 1: Login with retry
                if progress_callback:
                    await progress_callback("🔐 Melakukan login...")
                
                login_success = await self.auth_service.login_with_retry(
                    context, credentials, progress_callback
                )
                
                if not login_success:
                    error_msg = "❌ Login gagal. Periksa NIM dan password Anda."
                    logger.error("Login failed")
                    return error_msg
                
                # Step 2: Scrape forums
                if progress_callback:
                    await progress_callback("📊 Mengecek status forum...")
                
                scraping_result = await self.scraper_service.scrape_all_courses(
                    context, courses, progress_callback
                )
                
                # Step 3: Format results
                if progress_callback:
                    await progress_callback("📝 Menyusun laporan...")
                
                formatted_result = self.formatter_service.format_scraping_result(
                    scraping_result
                )
                
                execution_time = time.time() - start_time
                logger.info(f"Full scraping completed in {execution_time:.2f} seconds")
                
                return formatted_result
                
            except Exception as e:
                logger.error(f"Error during full scraping: {e}")
                return f"❌ Terjadi kesalahan saat scraping: {str(e)}"
                
            finally:
                await browser.close()
    
    async def execute_quick_check(
        self,
        credentials: LoginCredentials,
        course_code: str,
        meeting_numbers: List[int],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Execute quick check for specific course and meetings
        
        Args:
            credentials: Login credentials
            course_code: Course code to check
            meeting_numbers: List of meeting numbers to check
            progress_callback: Callback for progress updates
            
        Returns:
            str: Formatted result message
        """
        
        # Create single course info
        course = CourseInfo(
            code=course_code,
            name="Quick Check",
            meetings=meeting_numbers
        )
        
        return await self.execute_full_scraping(
            credentials, [course], progress_callback
        )
    
    async def test_login_only(
        self,
        credentials: LoginCredentials,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Test login without scraping
        
        Args:
            credentials: Login credentials
            progress_callback: Callback for progress updates
            
        Returns:
            bool: True if login successful
        """
        
        logger.info("Testing login only")
        
        async with async_playwright() as p:
            browser = await self._launch_browser(p)
            
            try:
                # Create browser context for login test
                context_options = {
                    'viewport': {
                        'width': self.settings.browser_config.viewport_width, 
                        'height': self.settings.browser_config.viewport_height
                    },
                    'user_agent': self.settings.browser_config.user_agent
                }
                
                context = await browser.new_context(**context_options)
                
                login_success = await self.auth_service.login_with_retry(
                    context, credentials, progress_callback
                )
                
                if login_success:
                    logger.info("Login test successful")
                else:
                    logger.error("Login test failed")
                
                return login_success
                
            except Exception as e:
                logger.error(f"Error during login test: {e}")
                return False
                
            finally:
                await browser.close()
    
    async def _launch_browser(self, playwright):
        """Launch browser dengan konfigurasi yang tepat"""
        
        browser_config = self.settings.browser_config
        
        launch_options = {
            'headless': browser_config.headless,
            'slow_mo': browser_config.slow_mo,
            'args': browser_config.args
        }
        
        # Video recording is configured per context, not browser launch
        # We'll handle this when creating the browser context
        
        logger.debug(f"Launching browser with options: {launch_options}")
        
        try:
            browser = await playwright.chromium.launch(**launch_options)
            return browser
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise Exception(f"Gagal meluncurkan browser: {e}")
    
    def update_settings(self, new_settings):
        """Update application settings"""
        self.settings = new_settings
        self.auth_service.settings = new_settings
        self.scraper_service.settings = new_settings
        
        logger.info("Application settings updated")


# Convenience functions for backward compatibility
async def login_and_scrape(nim: str, password: str, progress_callback=None) -> str:
    """
    Backward compatibility function
    
    Args:
        nim: Student ID
        password: Password
        progress_callback: Progress callback function
        
    Returns:
        str: Formatted scraping result
    """
    
    credentials = LoginCredentials(nim=nim, password=password)
    bot_core = MentariBotCore()
    
    return await bot_core.execute_full_scraping(credentials, None, progress_callback)
