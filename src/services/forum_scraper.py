"""
Service untuk scraping forum Mentari UNPAM
"""

import asyncio
import logging
import os
import time
from typing import List, Optional, Callable
from playwright.async_api import Page, BrowserContext

from src.models import (
    CourseInfo, CourseResult, MeetingInfo, ForumStatus, 
    BrowserConfig, ScrapingResult
)
from src.config import app_settings


logger = logging.getLogger(__name__)


class ForumScraperService:
    """Service untuk scraping status forum diskusi"""
    
    def __init__(self, settings=None):
        self.settings = settings or app_settings
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Pastikan directory untuk output sudah ada"""
        if self.settings.enable_screenshots:
            os.makedirs(self.settings.screenshot_dir, exist_ok=True)
        if self.settings.enable_video_recording:
            os.makedirs(self.settings.video_dir, exist_ok=True)
    
    async def scrape_all_courses(
        self, 
        context: BrowserContext, 
        courses: List[CourseInfo],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> ScrapingResult:
        """Scrape semua mata kuliah"""
        
        start_time = time.time()
        course_results = []
        
        logger.info(f"Starting scraping for {len(courses)} courses")
        
        for idx, course in enumerate(courses):
            if progress_callback:
                progress_text = f"📚 Mengecek: {course.name} ({idx + 1}/{len(courses)})"
                await progress_callback(progress_text)
            
            logger.info(f"Processing course: {course.name}")
            
            try:
                course_result = await self._scrape_single_course(context, course, progress_callback, idx + 1, len(courses))
                course_results.append(course_result)
                
                # Reduced delay between courses for speed
                if idx < len(courses) - 1:
                    await asyncio.sleep(max(0.5, self.settings.delay_between_courses * 0.5))
                    
            except Exception as e:
                logger.error(f"Error processing course {course.name}: {e}")
                # Create error result
                error_result = CourseResult.from_course_info(course)
                for meeting_num in course.meetings:
                    error_meeting = MeetingInfo(
                        number=meeting_num,
                        status=ForumStatus.ERROR,
                        message=f"Pertemuan {meeting_num}: ❗ Error: {str(e)[:50]}...",
                        error_details=str(e)
                    )
                    error_result.add_meeting_result(error_meeting)
                course_results.append(error_result)
        
        execution_time = time.time() - start_time
        
        if progress_callback:
            total_meetings = sum(len(course.meetings) for course in courses)
            completed_meetings = sum(len(result.meetings_status) for result in course_results)
            await progress_callback(f"✅ Selesai! Mengecek {completed_meetings} pertemuan dalam {execution_time:.1f} detik\n📝 Menyusun laporan...")
        
        return ScrapingResult.from_course_results(course_results, execution_time)
    
    async def _scrape_single_course(
        self, 
        context: BrowserContext, 
        course: CourseInfo,
        progress_callback: Optional[Callable[[str], None]] = None,
        course_idx: int = 1,
        total_courses: int = 1
    ) -> CourseResult:
        """Scrape satu mata kuliah"""
        
        page = await context.new_page()
        await self._configure_page(page)
        
        course_result = CourseResult.from_course_info(course)
        total_meetings = len(course.meetings)
        
        try:
            for idx, meeting_num in enumerate(course.meetings):
                # Update progress untuk setiap pertemuan
                if progress_callback:
                    progress_text = f"📚 {course.name} ({course_idx}/{total_courses})\n🔍 Mengecek Pertemuan {meeting_num} ({idx + 1}/{total_meetings})"
                    await progress_callback(progress_text)
                
                try:
                    meeting_result = await self._check_meeting_forum(
                        page, course.code, meeting_num
                    )
                    course_result.add_meeting_result(meeting_result)
                    
                    # Optimized delay - reduced for speed
                    if meeting_result.status in [ForumStatus.UNKNOWN, ForumStatus.ERROR]:
                        await asyncio.sleep(min(1.0, self.settings.delay_between_requests))
                    else:
                        await asyncio.sleep(max(0.3, self.settings.delay_between_requests * 0.5))
                        
                except Exception as e:
                    logger.error(f"Error checking meeting {meeting_num} for {course.name}: {e}")
                    error_meeting = MeetingInfo(
                        number=meeting_num,
                        status=ForumStatus.ERROR,
                        message=f"Pertemuan {meeting_num}: ❗ Error: {str(e)[:30]}...",
                        error_details=str(e)
                    )
                    course_result.add_meeting_result(error_meeting)
            
            # Progress update setelah course selesai
            if progress_callback:
                completed_meetings = len(course_result.meetings_status)
                joined = course_result.joined_count
                available = course_result.available_count
                unavailable = course_result.unavailable_count
                
                status_summary = f"✅{joined} 🟡{available} ❌{unavailable}"
                progress_text = f"✅ {course.name} selesai ({course_idx}/{total_courses})\n📊 {status_summary} dari {completed_meetings} pertemuan"
                await progress_callback(progress_text)
                    
        finally:
            await page.close()
        
        return course_result
    
    async def _configure_page(self, page: Page):
        """Konfigurasi page untuk optimal scraping"""
        # Set timeout
        page.set_default_timeout(self.settings.browser_config.timeout)
        
        # Set viewport
        await page.set_viewport_size({
            "width": self.settings.browser_config.viewport_width,
            "height": self.settings.browser_config.viewport_height
        })
        
        # Set user agent
        await page.set_extra_http_headers({
            'User-Agent': self.settings.browser_config.user_agent
        })
    
    async def _check_meeting_forum(
        self, 
        page: Page, 
        course_code: str, 
        meeting_num: int
    ) -> MeetingInfo:
        """Check status forum untuk pertemuan tertentu"""
        
        url = f"https://mentari.unpam.ac.id/u-courses/{course_code}?accord_pertemuan=PERTEMUAN_{meeting_num}"
        
        logger.debug(f"Checking forum for {course_code} meeting {meeting_num}")
        
        try:
            # Load page with retry
            await self._load_page_with_retry(page, url)
            
            # Take screenshot if enabled
            screenshot_path = None
            if self.settings.enable_screenshots:
                screenshot_path = await self._take_screenshot(
                    page, course_code, meeting_num
                )
            
            # Find forum section
            section = await self._find_forum_section(page, meeting_num)
            if not section:
                return MeetingInfo(
                    number=meeting_num,
                    status=ForumStatus.UNKNOWN,
                    message=f"Pertemuan {meeting_num}: ❔ Section tidak ditemukan",
                    screenshot_path=screenshot_path
                )
            
            # Analyze forum status
            status, message = await self._analyze_forum_status(section, meeting_num)
            
            return MeetingInfo(
                number=meeting_num,
                status=status,
                message=message,
                screenshot_path=screenshot_path
            )
            
        except Exception as e:
            logger.warning(f"Error checking forum {course_code} meeting {meeting_num}: {e}")
            
            if "timeout" in str(e).lower():
                return MeetingInfo(
                    number=meeting_num,
                    status=ForumStatus.TIMEOUT,
                    message=f"Pertemuan {meeting_num}: ⏰ Timeout - server lambat",
                    error_details=str(e)
                )
            else:
                return MeetingInfo(
                    number=meeting_num,
                    status=ForumStatus.ERROR,
                    message=f"Pertemuan {meeting_num}: ❗ Error: {str(e)[:50]}...",
                    error_details=str(e)
                )
    
    async def _load_page_with_retry(self, page: Page, url: str, max_retries: int = 2):
        """Load page dengan retry mechanism - optimized for speed"""
        
        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    # First attempt - fast load
                    await page.goto(url, timeout=20000, wait_until="domcontentloaded")
                else:
                    # Retry with more patience
                    await page.goto(url, timeout=15000, wait_until="networkidle")
                
                # Reduced wait time for better speed
                await page.wait_for_timeout(1500)
                
                # Try to wait for pertemuan content with shorter timeout
                try:
                    await page.wait_for_selector("div[id*='PERTEMUAN']", timeout=6000)
                except:
                    logger.debug("Pertemuan div not found immediately, continuing...")
                
                # Much shorter final wait
                await page.wait_for_timeout(1000)
                break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Page load attempt {attempt + 1} failed, retrying...")
                    await page.wait_for_timeout(1000)  # Shorter retry delay
                    continue
                else:
                    raise e
    
    async def _take_screenshot(self, page: Page, course_code: str, meeting_num: int) -> str:
        """Take screenshot untuk analisis"""
        timestamp = int(time.time())
        filename = f"forum_{course_code}_{meeting_num}_{timestamp}.png"
        filepath = os.path.join(self.settings.screenshot_dir, filename)
        
        await page.screenshot(path=filepath, full_page=True)
        logger.debug(f"Screenshot saved: {filepath}")
        
        return filepath
    
    async def _find_forum_section(self, page: Page, meeting_num: int):
        """Find section untuk pertemuan tertentu"""
        
        # Enhanced selectors dengan prioritas
        selectors = [
            # Most specific - direct pertemuan section IDs
            f"div[id='PERTEMUAN_{meeting_num}6']",
            f"div[id='PERTEMUAN_{meeting_num}']", 
            f"div[id^='PERTEMUAN_{meeting_num}'][id$='6']",
            
            # Filtered selectors to avoid user elements
            f"div[id^='PERTEMUAN_{meeting_num}']:not([id*='username']):not([id*='user'])",
            f"div[id*='PERTEMUAN_{meeting_num}']:not([id*='username']):not([id*='user'])",
            
            # Content-based selectors
            f"div:has-text('PERTEMUAN {meeting_num}'):not(:has-text('username'))",
            f"div:has-text('Pertemuan {meeting_num}'):not(:has-text('username'))",
            
            # Course content containers
            f"div[class*='course-content'][id*='{meeting_num}']",
            f"section[id*='pertemuan_{meeting_num}']",
        ]
        
        for selector in selectors:
            try:
                candidates = page.locator(selector)
                count = await candidates.count()
                
                if count > 0:
                    logger.debug(f"Found {count} elements with selector: {selector}")
                    
                    # Validate each candidate
                    for i in range(count):
                        candidate = candidates.nth(i)
                        
                        if await candidate.is_visible():
                            # Check if it's relevant content
                            text = await candidate.inner_text()
                            
                            # Skip user-related elements
                            skip_keywords = ['username', 'user profile', 'sidebar', 'navigation']
                            if any(keyword in text.lower() for keyword in skip_keywords):
                                continue
                            
                            # Check for course content
                            course_keywords = ['forum', 'diskusi', 'pertemuan', 'content']
                            if any(keyword in text.lower() for keyword in course_keywords) or len(text) > 50:
                                logger.debug(f"Selected valid section using: {selector}")
                                return candidate
                        
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        
        # Try scroll and expand if nothing found
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
            # Try to expand accordions
            accordion_buttons = page.locator("button:has-text('PERTEMUAN'), button:has-text('Pertemuan')")
            count = await accordion_buttons.count()
            
            if count > 0:
                logger.debug("Expanding accordion sections...")
                for i in range(min(count, 5)):  # Limit to avoid infinite loops
                    try:
                        button = accordion_buttons.nth(i)
                        if await button.is_visible():
                            await button.click()
                            await page.wait_for_timeout(1000)
                    except:
                        continue
                
                # Try selectors again after expansion
                for selector in selectors[:3]:  # Try top 3 selectors
                    try:
                        section = page.locator(selector).first
                        if await section.count() > 0 and await section.is_visible():
                            logger.debug(f"Found section after expansion: {selector}")
                            return section
                    except:
                        continue
                        
        except Exception as e:
            logger.debug(f"Error during scroll/expand: {e}")
        
        return None
    
    async def _analyze_forum_status(self, section, meeting_num: int) -> tuple[ForumStatus, str]:
        """Analyze status forum dari section yang ditemukan"""
        
        try:
            # Get section content
            section_text = await section.inner_text()
            text_lower = section_text.lower()
            
            # Check various indicators
            status_indicators = {
                'has_check': await section.locator("[data-testid='CheckCircleIcon'], .check-icon, [class*='check'], [class*='complete']").count() > 0,
                'has_forum_button': await section.locator("button:has-text('Forum'), a:has-text('Forum'), [class*='forum']").count() > 0,
                'has_diskusi_button': await section.locator("button:has-text('Diskusi'), a:has-text('Diskusi'), [class*='diskusi']").count() > 0,
                'has_no_content': await section.locator("i:text('No content'), span:text('No content'), div:text('No content')").count() > 0,
                'has_unavailable': await section.locator("text=belum tersedia, text=tidak tersedia, text=coming soon").count() > 0,
                'has_join_button': await section.locator("button:has-text('Gabung'), button:has-text('Join'), [class*='join']").count() > 0,
                'has_access_granted': await section.locator("[class*='granted'], [class*='accessible'], .available").count() > 0
            }
            
            # Text-based indicators
            text_indicators = {
                'text_joined': any(phrase in text_lower for phrase in ['sudah bergabung', 'joined', 'telah bergabung']),
                'text_unavailable': any(phrase in text_lower for phrase in ['belum tersedia', 'not available', 'coming soon']),
                'text_available': any(phrase in text_lower for phrase in ['tersedia', 'available', 'forum', 'diskusi']),
                'text_no_content': any(phrase in text_lower for phrase in ['no content', 'tidak ada konten', 'kosong']),
                'text_join': any(phrase in text_lower for phrase in ['gabung', 'join', 'bergabung'])
            }
            
            # Debug logging
            if self.settings.detailed_logging:
                logger.debug(f"Status indicators: {status_indicators}")
                logger.debug(f"Text indicators: {text_indicators}")
                logger.debug(f"Section text preview: {text_lower[:200]}...")
            
            # Manual pause for debugging
            if self.settings.pause_on_error and not any(status_indicators.values()):
                logger.info(f"Pausing for manual analysis - Meeting {meeting_num}")
                if not self.settings.headless_mode:
                    input("Press Enter to continue after manual analysis...")
            
            # Determine status with priority logic
            if status_indicators['has_no_content'] or status_indicators['has_unavailable'] or text_indicators['text_unavailable']:
                return ForumStatus.UNAVAILABLE, f"Pertemuan {meeting_num}: ❌ Forum belum tersedia"
            
            elif (status_indicators['has_forum_button'] or status_indicators['has_diskusi_button']) and \
                 (status_indicators['has_check'] or status_indicators['has_access_granted'] or text_indicators['text_joined']):
                return ForumStatus.JOINED, f"Pertemuan {meeting_num}: ✅ Sudah bergabung"
            
            elif (status_indicators['has_forum_button'] or status_indicators['has_diskusi_button'] or 
                  status_indicators['has_join_button'] or text_indicators['text_join']) and \
                 not (status_indicators['has_check'] or text_indicators['text_joined']):
                return ForumStatus.AVAILABLE, f"Pertemuan {meeting_num}: 🟡 Tersedia tapi belum bergabung"
            
            elif text_indicators['text_available'] or 'forum' in text_lower or 'diskusi' in text_lower:
                return ForumStatus.AVAILABLE, f"Pertemuan {meeting_num}: 🟡 Forum tersedia (status belum jelas)"
            
            else:
                return ForumStatus.UNKNOWN, f"Pertemuan {meeting_num}: ❔ Status forum tidak terdeteksi"
                
        except Exception as e:
            logger.error(f"Error analyzing forum status: {e}")
            return ForumStatus.ERROR, f"Pertemuan {meeting_num}: ❗ Error analisis: {str(e)[:30]}..."
