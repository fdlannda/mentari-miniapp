"""
Service untuk menyelesaikan CAPTCHA menggunakan 2captcha
"""

import asyncio
import logging
import httpx
from typing import Optional
from playwright.async_api import Page


logger = logging.getLogger(__name__)


class CaptchaSolverService:
    """Service untuk menyelesaikan berbagai jenis CAPTCHA"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://2captcha.com"
        self.timeout = 120  # 2 minutes timeout
    
    async def solve_recaptcha_v2(self, page: Page, site_key: str) -> bool:
        """
        Solve reCAPTCHA v2 using 2captcha service
        
        Args:
            page: Playwright page object
            site_key: reCAPTCHA site key
            
        Returns:
            bool: True if successfully solved, False otherwise
        """
        try:
            logger.info("Starting reCAPTCHA v2 solving process")
            
            # Get current page URL
            page_url = page.url
            
            # Submit CAPTCHA to 2captcha
            captcha_id = await self._submit_recaptcha(site_key, page_url)
            if not captcha_id:
                return False
            
            # Wait for solution
            solution = await self._get_captcha_solution(captcha_id)
            if not solution:
                return False
            
            # Inject solution into page
            success = await self._inject_recaptcha_solution(page, solution)
            return success
            
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA: {e}")
            return False
    
    async def _submit_recaptcha(self, site_key: str, page_url: str) -> Optional[str]:
        """Submit reCAPTCHA to 2captcha service"""
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{self.base_url}/in.php", data={
                    'key': self.api_key,
                    'method': 'userrecaptcha',
                    'googlekey': site_key,
                    'pageurl': page_url,
                    'json': 1
                })
                
                result = response.json()
                
                if result.get('status') == 1:
                    captcha_id = result.get('request')
                    logger.info(f"CAPTCHA submitted successfully, ID: {captcha_id}")
                    return captcha_id
                else:
                    logger.error(f"Failed to submit CAPTCHA: {result}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error submitting CAPTCHA: {e}")
            return None
    
    async def _get_captcha_solution(self, captcha_id: str) -> Optional[str]:
        """Get CAPTCHA solution from 2captcha"""
        
        logger.info(f"Waiting for CAPTCHA solution for ID: {captcha_id}")
        
        # Wait initial time before first check
        await asyncio.sleep(20)
        
        max_attempts = (self.timeout // 5)  # Check every 5 seconds
        
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(f"{self.base_url}/res.php", params={
                        'key': self.api_key,
                        'action': 'get',
                        'id': captcha_id,
                        'json': 1
                    })
                    
                    result = response.json()
                    
                    if result.get('status') == 1:
                        solution = result.get('request')
                        logger.info("CAPTCHA solved successfully")
                        return solution
                    elif result.get('error_text') == 'CAPCHA_NOT_READY':
                        logger.debug(f"CAPTCHA not ready yet, attempt {attempt + 1}/{max_attempts}")
                        await asyncio.sleep(5)
                        continue
                    else:
                        logger.error(f"CAPTCHA solving failed: {result}")
                        return None
                        
            except Exception as e:
                logger.error(f"Error getting CAPTCHA solution: {e}")
                await asyncio.sleep(5)
                continue
        
        logger.error("CAPTCHA solving timeout")
        return None
    
    async def _inject_recaptcha_solution(self, page: Page, solution: str) -> bool:
        """Inject reCAPTCHA solution into page"""
        
        try:
            # Find reCAPTCHA response field and inject solution
            await page.evaluate(f"""
                // Find and fill the reCAPTCHA response field
                const responseField = document.querySelector('#g-recaptcha-response');
                if (responseField) {{
                    responseField.innerHTML = '{solution}';
                    responseField.value = '{solution}';
                    responseField.style.display = 'block';
                }}
                
                // Trigger callback if exists
                if (window.grecaptcha && window.grecaptcha.getResponse) {{
                    window.grecaptcha.getResponse = () => '{solution}';
                }}
                
                // Try to find and trigger callback function
                const recaptchaElement = document.querySelector('.g-recaptcha');
                if (recaptchaElement) {{
                    const callback = recaptchaElement.getAttribute('data-callback');
                    if (callback && window[callback]) {{
                        window[callback]('{solution}');
                    }}
                }}
                
                // Mark as solved
                document.querySelectorAll('.recaptcha-checkbox-border').forEach(el => {{
                    el.style.display = 'none';
                }});
                
                document.querySelectorAll('.recaptcha-checkbox-checkmark').forEach(el => {{
                    el.style.display = 'block';
                }});
            """)
            
            logger.info("reCAPTCHA solution injected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error injecting reCAPTCHA solution: {e}")
            return False


# Convenience function for backward compatibility
async def solve_recaptcha(page: Page, api_key: str) -> bool:
    """
    Solve reCAPTCHA on the current page
    
    Args:
        page: Playwright page object  
        api_key: 2captcha API key
        
    Returns:
        bool: True if successfully solved
    """
    
    try:
        # Try to find reCAPTCHA site key
        site_key = await page.evaluate("""
            () => {
                // Try to find site key from various places
                const recaptchaElement = document.querySelector('.g-recaptcha');
                if (recaptchaElement) {
                    return recaptchaElement.getAttribute('data-sitekey');
                }
                
                // Try to find in script tags
                const scripts = document.querySelectorAll('script');
                for (const script of scripts) {
                    const content = script.textContent || script.innerHTML;
                    const match = content.match(/sitekey['"\\s]*[:=]['"\\s]*([\\w-]+)/i);
                    if (match) {
                        return match[1];
                    }
                }
                
                return null;
            }
        """)
        
        if not site_key:
            logger.warning("reCAPTCHA site key not found")
            return False
        
        logger.info(f"Found reCAPTCHA site key: {site_key}")
        
        # Use the solver service
        solver = CaptchaSolverService(api_key)
        return await solver.solve_recaptcha_v2(page, site_key)
        
    except Exception as e:
        logger.error(f"Error in solve_recaptcha: {e}")
        return False
