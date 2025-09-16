"""
Service untuk login ke Mentari UNPAM
"""

import asyncio
import logging
import os
import time
from typing import Optional, Callable, Awaitable
from playwright.async_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

from src.models import LoginCredentials, BrowserConfig
from src.config import app_settings, env_config


logger = logging.getLogger(__name__)


class MentariLoginService:
    """Service untuk login ke sistem Mentari UNPAM"""
    
    def __init__(self, settings=None):
        self.settings = settings or app_settings
        self.login_url = f"{env_config.mentari_base_url}/login"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Pastikan directory untuk screenshot sudah ada"""
        if self.settings.enable_screenshots:
            os.makedirs(self.settings.screenshot_dir, exist_ok=True)
    
    async def login_with_retry(
        self, 
        context: BrowserContext, 
        credentials: LoginCredentials,
        progress_callback: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> bool:
        """
        Login ke Mentari UNPAM dengan retry mechanism
        
        Returns:
            bool: True jika login berhasil, False jika gagal
        """
        max_attempts = self.settings.max_retries + 1  # +1 untuk attempt pertama
        
        for attempt in range(max_attempts):
            try:
                if progress_callback:
                    if attempt == 0:
                        await progress_callback("🔐 Memulai proses login...")
                    else:
                        await progress_callback(f"🔄 Percobaan login ke-{attempt + 1} dari {max_attempts}...")
                
                # Attempt login
                success = await self.login(context, credentials, progress_callback)
                
                if success:
                    logger.info(f"Login successful on attempt {attempt + 1}")
                    return True
                else:
                    logger.warning(f"Login failed on attempt {attempt + 1}")
                    if progress_callback:
                        if attempt < max_attempts - 1:
                            await progress_callback(f"❌ Login gagal, mencoba lagi... ({attempt + 1}/{max_attempts})")
                        else:
                            await progress_callback("❌ Login gagal setelah semua percobaan!")
                    
                    # Wait before retry (except on last attempt)
                    if attempt < max_attempts - 1:
                        retry_delay = self.settings.delay_between_requests * (attempt + 1)  # Exponential backoff
                        logger.info(f"Waiting {retry_delay}s before retry...")
                        await asyncio.sleep(retry_delay)
                        
            except Exception as e:
                logger.error(f"Login error on attempt {attempt + 1}: {e}")
                if progress_callback:
                    await progress_callback(f"❌ Error login: {str(e)[:50]}...")
                
                # Wait before retry (except on last attempt)
                if attempt < max_attempts - 1:
                    retry_delay = self.settings.delay_between_requests * (attempt + 1)
                    await asyncio.sleep(retry_delay)
        
        # All attempts failed
        logger.error(f"Login failed after {max_attempts} attempts")
        return False

    async def login(
        self, 
        context: BrowserContext, 
        credentials: LoginCredentials,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """
        Login ke Mentari UNPAM (single attempt)
        
        Returns:
            bool: True jika login berhasil, False jika gagal
        """
        
        page = await context.new_page()
        
        try:
            logger.info("Starting login process to Mentari UNPAM")
            
            if progress_callback:
                await progress_callback("🔐 Memulai proses login...")
            
            # Configure page
            await self._configure_page(page)
            
            # Navigate to login page
            await self._navigate_to_login(page, progress_callback)
            
            # Fill login form
            await self._fill_login_form(page, credentials, progress_callback)
            
            # Handle CAPTCHA if present
            await self._handle_captcha(page, progress_callback)
            
            # Submit form and wait for result
            success = await self._submit_and_verify(page, progress_callback)
            
            if success:
                logger.info("Login successful")
                if progress_callback:
                    await progress_callback("✅ Login berhasil!")
            else:
                logger.error("Login failed")
                if progress_callback:
                    await progress_callback("❌ Login gagal!")
            
            return success
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            if progress_callback:
                await progress_callback(f"❌ Error login: {str(e)[:50]}...")
            return False
            
        finally:
            await page.close()
    
    async def _configure_page(self, page: Page):
        """Konfigurasi page untuk login"""
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
    
    async def _navigate_to_login(self, page: Page, progress_callback: Optional[callable] = None):
        """Navigate ke halaman login"""
        
        if progress_callback:
            await progress_callback("🌐 Membuka halaman login...")
        
        try:
            await page.goto(self.login_url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # Set initial URL for comparison
            await page.evaluate(f"window.initial_url = '{self.login_url}';")
            
            # Take screenshot if enabled
            if self.settings.enable_screenshots:
                await self._take_screenshot(page, "login_page")
            
            logger.debug("Successfully navigated to login page")
            
        except PlaywrightTimeoutError:
            logger.error("Timeout loading login page")
            raise Exception("Timeout saat membuka halaman login")
        except Exception as e:
            logger.error(f"Error navigating to login: {e}")
            raise Exception(f"Error membuka halaman login: {e}")
    
    async def _fill_login_form(
        self, 
        page: Page, 
        credentials: LoginCredentials, 
        progress_callback: Optional[callable] = None
    ):
        """Fill form login dengan kredensial"""
        
        if progress_callback:
            await progress_callback("📝 Mengisi form login...")
        
        try:
            # Wait for form elements with longer timeout
            await page.wait_for_selector("input[name='username'], input[type='text'], #username", timeout=15000)
            
            # Wait a bit more for all elements to load
            await page.wait_for_timeout(2000)
            
            # Find username field (try multiple selectors)
            username_selectors = [
                "input[name='username']",
                "input[name='Username']",
                "input[type='text']",
                "#username",
                "#Username",
                "input[placeholder*='username' i]",
                "input[placeholder*='nim' i]",
                "input[class*='username']",
                "input[id*='username']"
            ]
            
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = page.locator(selector).first
                    if await username_field.count() > 0:
                        break
                except:
                    continue
            
            if not username_field or await username_field.count() == 0:
                raise Exception("Username field tidak ditemukan")
            
            # Find password field
            password_selectors = [
                "input[name='Password']",
                "input[name='password']", 
                "input[type='password']",
                "#password",
                "#Password", 
                "input[placeholder*='password' i]",
                "input[placeholder*='kata sandi' i]",
                "input[class*='password']",
                "input[id*='password']",
                "input[data-testid*='password']"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = page.locator(selector).first
                    if await password_field.count() > 0:
                        break
                except:
                    continue
            
            if not password_field or await password_field.count() == 0:
                # Enhanced debugging for password field detection
                logger.error("Password field not found with standard selectors")
                
                # Try to log all input fields for debugging
                try:
                    all_inputs = await page.evaluate("""
                        () => {
                            const inputs = document.querySelectorAll('input');
                            return Array.from(inputs).map(input => ({
                                type: input.type,
                                name: input.name,
                                id: input.id,
                                placeholder: input.placeholder,
                                className: input.className
                            }));
                        }
                    """)
                    logger.debug(f"All input fields found: {all_inputs}")
                except Exception as debug_e:
                    logger.debug(f"Could not debug input fields: {debug_e}")
                
                raise Exception("Password field tidak ditemukan - periksa halaman login")
            
            # Clear and fill fields
            await username_field.clear()
            await username_field.fill(credentials.nim)
            await page.wait_for_timeout(500)
            
            await password_field.clear()
            await password_field.fill(credentials.password)
            await page.wait_for_timeout(500)
            
            # Take screenshot after filling
            if self.settings.enable_screenshots:
                await self._take_screenshot(page, "form_filled")
            
            logger.debug("Form filled successfully")
            
        except Exception as e:
            logger.error(f"Error filling login form: {e}")
            raise Exception(f"Error mengisi form login: {e}")
    
    async def _handle_captcha(self, page: Page, progress_callback: Optional[callable] = None):
        """Handle CAPTCHA jika ada"""
        
        try:
            # Check for reCAPTCHA
            recaptcha_frame = page.frame_locator("iframe[src*='recaptcha']").first
            
            if await recaptcha_frame.locator("div").count() > 0:
                if progress_callback:
                    await progress_callback("🔒 Menyelesaikan CAPTCHA...")
                
                logger.info("CAPTCHA detected, solving...")
                
                # Import captcha solver
                from src.services.captcha_solver import solve_recaptcha
                
                success = await solve_recaptcha(page, env_config.captcha_api_key)
                
                if success:
                    logger.info("CAPTCHA solved successfully")
                    if progress_callback:
                        await progress_callback("✅ CAPTCHA berhasil diselesaikan")
                else:
                    logger.warning("CAPTCHA solving failed")
                    if progress_callback:
                        await progress_callback("⚠️ CAPTCHA gagal diselesaikan")
                
                await page.wait_for_timeout(2000)
            else:
                logger.debug("No CAPTCHA detected")
                
        except Exception as e:
            logger.warning(f"Error handling CAPTCHA: {e}")
            # Continue without CAPTCHA if error occurs
    
    async def _submit_and_verify(self, page: Page, progress_callback: Optional[callable] = None) -> bool:
        """Submit form dan verifikasi hasil login"""
        
        if progress_callback:
            await progress_callback("🚀 Mengirim form login...")
        
        try:
            # Find submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Login')",
                "button:has-text('Masuk')",
                "button:has-text('Sign In')",
                ".btn-login",
                "#login-button"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = page.locator(selector).first
                    if await submit_button.count() > 0 and await submit_button.is_visible():
                        break
                except:
                    continue
            
            if not submit_button or await submit_button.count() == 0:
                # Try pressing Enter as fallback
                await page.press("input[type='password']", "Enter")
            else:
                await submit_button.click()
            
            # Wait for navigation or response
            if progress_callback:
                await progress_callback("⏳ Menunggu respons server...")
            
            try:
                # Wait for either success redirect or error message
                await page.wait_for_function(
                    "() => window.location.href !== window.initial_url", 
                    timeout=15000
                )
            except PlaywrightTimeoutError:
                # Check for error messages on same page
                pass
            
            await page.wait_for_timeout(3000)
            
            # Take screenshot after submission
            if self.settings.enable_screenshots:
                await self._take_screenshot(page, "after_login")
            
            # Verify login success
            current_url = page.url
            
            # Check various indicators of successful login
            success_indicators = [
                "/dashboard" in current_url.lower(),
                "/home" in current_url.lower(), 
                "/course" in current_url.lower(),
                "/u-courses" in current_url.lower(),
                current_url != self.login_url
            ]
            
            # Check for error messages
            error_messages = [
                "invalid", "salah", "error", "gagal", "failed", 
                "incorrect", "wrong", "tidak valid"
            ]
            
            page_text = await page.inner_text("body")
            has_error = any(error in page_text.lower() for error in error_messages)
            
            # Determine success
            login_success = any(success_indicators) and not has_error
            
            if login_success:
                logger.info(f"Login successful - redirected to: {current_url}")
                return True
            else:
                logger.error(f"Login failed - still on: {current_url}")
                if has_error:
                    logger.error("Error message detected on page")
                return False
                
        except Exception as e:
            logger.error(f"Error during login submission: {e}")
            return False
    
    async def _take_screenshot(self, page: Page, name: str) -> str:
        """Take screenshot dengan timestamp"""
        timestamp = int(time.time())
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join(self.settings.screenshot_dir, filename)
        
        await page.screenshot(path=filepath)
        logger.debug(f"Screenshot saved: {filepath}")
        
        return filepath
