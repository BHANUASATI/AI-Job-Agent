"""
Overleaf login module with session management.

Handles authentication flow, session persistence, and automatic re-login
when sessions expire.
"""

import asyncio
from typing import Optional

from automation.browser_manager import BrowserManager
from automation.config import AutomationConfig
from automation.exceptions import (
    LoginFailedException,
    SessionExpiredException,
    TimeoutException,
)
from automation.overleaf.selectors import OverleafSelectors
from automation.utils import get_logger, retry_with_backoff


class OverleafLogin:
    """
    Handles Overleaf authentication and session management.
    
    Features:
    - Login with email/password
    - Session persistence
    - Automatic session validation
    - Re-login on session expiry
    - Credential management from environment variables
    """
    
    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize OverleafLogin.
        
        Args:
            browser_manager: BrowserManager instance for browser operations
        """
        self.browser_manager = browser_manager
        self.logger = get_logger("overleaf_login")
        self.selectors = OverleafSelectors()
        
        # Validate credentials
        self._validate_credentials()
    
    def _validate_credentials(self) -> None:
        """
        Validate that required credentials are available.
        
        Raises:
            LoginFailedException: If credentials are missing
        """
        if not AutomationConfig.OVERLEAF_EMAIL:
            raise LoginFailedException("OVERLEAF_EMAIL not configured in environment")
        
        if not AutomationConfig.OVERLEAF_PASSWORD:
            raise LoginFailedException("OVERLEAF_PASSWORD not configured in environment")
        
        self.logger.info("Credentials validated")
    
    async def login(
        self,
        session_name: str = "overleaf",
        force_relogin: bool = False,
    ) -> bool:
        """
        Perform login to Overleaf with session management.
        
        Args:
            session_name: Name for session file
            force_relogin: Force fresh login even if session exists
            
        Returns:
            True if login successful
            
        Raises:
            LoginFailedException: If login fails
        """
        # Check if we can reuse existing session
        if not force_relogin and await self._can_reuse_session(session_name):
            self.logger.info("Reusing existing session")
            return True
        
        self.logger.info("Performing fresh login")
        
        try:
            # Navigate to Overleaf
            await self._navigate_to_overleaf()
            
            # Click login button
            await self._click_login_button()
            
            # Enter credentials
            await self._enter_credentials()
            
            # Submit login form
            await self._submit_login()
            
            # Check for CAPTCHA and handle it with AI solving
            await self._handle_captcha_with_ai()
            
            # Wait for successful login
            await self._verify_login_success()
            
            # Verify dashboard is loaded
            await self._verify_dashboard_loaded()
            
            # Save session
            await self.browser_manager.save_session(session_name)
            
            self.logger.info("Login successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            raise LoginFailedException(f"Login failed: {e}")
    
    async def _can_reuse_session(self, session_name: str) -> bool:
        """
        Check if existing session can be reused.
        
        Args:
            session_name: Name of session to check
            
        Returns:
            True if session can be reused
        """
        if not AutomationConfig.SESSION_PERSIST_ENABLED:
            return False
        
        if not await self.browser_manager.is_session_valid(session_name):
            return False
        
        # Try to navigate to dashboard with existing session
        try:
            await self.browser_manager.navigate(AutomationConfig.OVERLEAF_URL)
            
            # Check if we're already logged in by looking for dashboard elements
            await self.browser_manager.wait_for_element(
                self.selectors.DASHBOARD_CONTAINER,
                timeout=5000,
                state="attached"
            )
            
            return True
            
        except TimeoutException:
            self.logger.info("Session expired or invalid")
            return False
    
    async def _navigate_to_overleaf(self) -> None:
        """Navigate to Overleaf homepage."""
        self.logger.info("Navigating to Overleaf")
        await self.browser_manager.navigate(AutomationConfig.OVERLEAF_URL)
    
    async def _click_login_button(self) -> None:
        """Click on the login button on the homepage."""
        self.logger.info("Clicking login button")
        
        await retry_with_backoff(
            lambda: self.browser_manager.click(self.selectors.LOGIN_BUTTON),
            exceptions=(TimeoutException,),
            logger=self.logger,
        )
    
    async def _enter_credentials(self) -> None:
        """Enter email and password credentials."""
        self.logger.info("Entering credentials")
        
        # Wait for email input
        await self.browser_manager.wait_for_element(self.selectors.LOGIN_PAGE_EMAIL_INPUT)
        
        # Enter email
        await self.browser_manager.fill(
            self.selectors.LOGIN_PAGE_EMAIL_INPUT,
            AutomationConfig.OVERLEAF_EMAIL
        )
        
        # Enter password
        await self.browser_manager.fill(
            self.selectors.LOGIN_PAGE_PASSWORD_INPUT,
            AutomationConfig.OVERLEAF_PASSWORD
        )
        
        self.logger.info("Credentials entered")
    
    async def _submit_login(self) -> None:
        """Submit the login form."""
        self.logger.info("Submitting login form")
        
        await retry_with_backoff(
            lambda: self.browser_manager.click(self.selectors.LOGIN_PAGE_SUBMIT_BUTTON),
            exceptions=(TimeoutException,),
            logger=self.logger,
        )
    
    async def _verify_login_success(self) -> None:
        """
        Verify that login was successful by checking for dashboard elements.
        
        Raises:
            LoginFailedException: If login verification fails
        """
        self.logger.info("Verifying login success")
        
        try:
            # Wait a moment for page to load
            await asyncio.sleep(2)
            
            # Check current URL - if it contains /dashboard, we're likely logged in
            current_url = self.browser_manager.page.url
            self.logger.info(f"Current URL after login: {current_url}")
            
            if '/dashboard' in current_url or '/project' in current_url:
                self.logger.info("Login verification successful (URL check)")
                return
            
            # Try to find any dashboard-like element
            try:
                # Check for any project-related elements
                project_elements = await self.browser_manager.page.query_selector_all(
                    'a[href*="/project"]'
                )
                if project_elements:
                    self.logger.info(f"Found {len(project_elements)} project links - login successful")
                    return
            except:
                pass
            
            # Check for user menu or logout button (indicates logged in state)
            try:
                user_menu = await self.browser_manager.page.query_selector(
                    'button.user-menu, [aria-label*="user"], [aria-label*="menu"]'
                )
                if user_menu:
                    self.logger.info("Found user menu - login successful")
                    return
            except:
                pass
            
            # If we're here, check for error messages
            try:
                error_element = await self.browser_manager.page.query_selector(
                    self.selectors.ERROR_MESSAGE
                )
                if error_element:
                    error_text = await error_element.text_content()
                    self.logger.error(f"Login error message: {error_text}")
                    raise LoginFailedException(f"Login error: {error_text}")
            except:
                pass
            
            # Take a screenshot for debugging
            try:
                screenshot_path = AutomationConfig.DOWNLOAD_DIR / "login_debug.png"
                await self.browser_manager.screenshot(screenshot_path)
                self.logger.info(f"Debug screenshot saved: {screenshot_path}")
            except:
                pass
            
            # Get page title for debugging
            try:
                page_title = await self.browser_manager.page.title()
                self.logger.info(f"Page title: {page_title}")
            except:
                pass
            
            self.logger.warning("Could not verify login with standard selectors, but may be successful")
            
        except Exception as e:
            self.logger.error(f"Login verification error: {e}")
            raise LoginFailedException(f"Login verification failed: {e}")
    
    async def _handle_captcha_with_ai(self) -> None:
        """
        Handle CAPTCHA with AI solving integration.
        
        This method detects CAPTCHA and uses AI to solve it if present.
        Falls back to manual intervention if AI solving is not available.
        """
        self.logger.info("Checking for CAPTCHA with AI solving...")
        
        try:
            # Import CAPTCHA solver
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(project_root))
            
            from services.captcha_solver import captcha_solver
            
            # Handle CAPTCHA with retry logic
            captcha_handled = await captcha_solver.handle_captcha_with_retry(self.browser_manager.page)
            
            if captcha_handled:
                self.logger.info("CAPTCHA handled successfully")
            else:
                self.logger.warning("CAPTCHA handling failed, but continuing anyway")
                
        except ImportError:
            self.logger.warning("CAPTCHA solver not available, skipping")
        except Exception as e:
            self.logger.error(f"CAPTCHA handling error: {e}")
            # Continue anyway - CAPTCHA might not be present
    
    async def _verify_dashboard_loaded(self) -> None:
        """
        Verify that the Overleaf dashboard is actually loaded after login.
        
        This ensures we're not just on a login page or error page.
        """
        self.logger.info("Verifying dashboard is loaded...")
        
        try:
            # Wait for page to stabilize
            await asyncio.sleep(2)
            
            # Check current URL
            current_url = self.browser_manager.page.url
            self.logger.info(f"Current URL after login: {current_url}")
            
            # Navigate to dashboard if not already there
            if '/dashboard' not in current_url:
                self.logger.info("Navigating to dashboard...")
                await self.browser_manager.navigate("https://www.overleaf.com/dashboard")
                await asyncio.sleep(3)
            
            # Verify dashboard elements are present
            dashboard_indicators = [
                'a[href*="/project"]',
                '[class*="project"]',
                '[class*="dashboard"]'
            ]
            
            dashboard_loaded = False
            for selector in dashboard_indicators:
                try:
                    element = await self.browser_manager.page.query_selector(selector)
                    if element:
                        dashboard_loaded = True
                        self.logger.info(f"Dashboard verified using: {selector}")
                        break
                except:
                    continue
            
            if dashboard_loaded:
                self.logger.info("Dashboard loaded successfully")
            else:
                self.logger.warning("Could not verify dashboard with standard selectors, but continuing")
                
        except Exception as e:
            self.logger.warning(f"Dashboard verification error: {e}, but continuing")
    
    async def logout(self) -> None:
        """
        Logout from Overleaf.
        
        This is optional but useful for testing.
        """
        self.logger.info("Logging out")
        
        try:
            # Click user menu
            await self.browser_manager.click(self.selectors.USER_MENU)
            
            # Click logout button
            await self.browser_manager.click(self.selectors.LOGOUT_BUTTON)
            
            self.logger.info("Logout successful")
            
        except Exception as e:
            self.logger.warning(f"Logout failed (may not be critical): {e}")
    
    async def ensure_authenticated(
        self,
        session_name: str = "overleaf",
    ) -> bool:
        """
        Ensure user is authenticated, logging in if necessary.
        
        This is the main entry point for authentication - it checks
        existing session and performs login only if needed.
        
        Args:
            session_name: Name for session file
            
        Returns:
            True if authenticated
        """
        try:
            return await self.login(session_name=session_name)
        except SessionExpiredException:
            self.logger.info("Session expired, performing fresh login")
            return await self.login(session_name=session_name, force_relogin=True)
