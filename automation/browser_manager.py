"""
Browser Manager for automation module.

Provides reusable browser operations including launching, closing, context management,
session persistence, and download handling. Designed to be platform-agnostic
and reusable for different websites (LinkedIn, Naukri, Indeed, etc.).
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Error as PlaywrightError,
)

from automation.config import AutomationConfig
from automation.exceptions import (
    BrowserLaunchException,
    TimeoutException,
    NetworkException,
)
from automation.utils import get_logger, retry_with_backoff, generate_timestamp
from automation.visual_logger import VisualLogger


class BrowserManager:
    """
    Manages browser lifecycle and operations for automation tasks.
    
    This class provides a reusable interface for browser automation that can be
    used across different platforms (Overleaf, LinkedIn, Naukri, etc.).
    
    Features:
    - Browser launch and cleanup
    - Context management with session persistence
    - Page creation and management
    - Download directory handling
    - Configurable timeouts and headless mode
    - Error handling and retry logic
    """
    
    def __init__(
        self,
        headless: Optional[bool] = None,
        browser_type: Optional[str] = None,
        download_dir: Optional[Path] = None,
        timeout: Optional[int] = None,
        visual_mode: Optional[bool] = None,
        visual_logger: Optional[VisualLogger] = None,
    ):
        """
        Initialize BrowserManager.
        
        Args:
            headless: Whether to run browser in headless mode (default from config)
            browser_type: Browser type - chromium, firefox, or webkit (default from config)
            download_dir: Directory for downloads (default from config)
            timeout: Default timeout in milliseconds (default from config)
            visual_mode: Whether to enable visual execution mode (default from config)
            visual_logger: Visual logger instance for progress tracking
        """
        self.logger = get_logger("browser_manager")
        
        # Determine if visual mode is enabled
        self.visual_mode = visual_mode if visual_mode is not None else (
            AutomationConfig.DEBUG_MODE or AutomationConfig.VISUAL_MODE
        )
        
        # Override headless for visual mode
        if self.visual_mode:
            self.headless = AutomationConfig.VISUAL_HEADLESS
        else:
            self.headless = headless if headless is not None else AutomationConfig.BROWSER_HEADLESS
        
        self.browser_type = browser_type if browser_type is not None else AutomationConfig.BROWSER_TYPE
        self.download_dir = download_dir if download_dir is not None else AutomationConfig.DOWNLOAD_DIR
        self.timeout = timeout if timeout is not None else AutomationConfig.BROWSER_TIMEOUT
        
        # Visual logger
        self.visual_logger = visual_logger or VisualLogger()
        
        # Video recording
        self.video_path: Optional[Path] = None
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Ensure download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(
            f"BrowserManager initialized: headless={self.headless}, "
            f"browser_type={self.browser_type}, download_dir={self.download_dir}, "
            f"visual_mode={self.visual_mode}"
        )
    
    async def launch(self) -> None:
        """
        Launch the browser with configured settings.
        
        Raises:
            BrowserLaunchException: If browser fails to launch
        """
        self.logger.info("Launching browser...")
        self.visual_logger.step("1/10", "Launching Browser...")
        
        try:
            self.playwright = await async_playwright().start()
            
            # Determine slow motion based on visual mode
            if self.visual_mode:
                slow_mo = AutomationConfig.VISUAL_SLOW_MO
            else:
                slow_mo = AutomationConfig.BROWSER_SLOW_MO
            
            # Launch browser with appropriate arguments
            launch_args = {
                "headless": self.headless,
                "slow_mo": slow_mo,
            }
            
            # Add browser-specific arguments if needed
            if self.browser_type == "chromium":
                launch_args["args"] = [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            
            browser_launcher = getattr(self.playwright, self.browser_type)
            self.browser = await retry_with_backoff(
                lambda: browser_launcher.launch(**launch_args),
                exceptions=(PlaywrightError,),
                logger=self.logger,
            )
            
            self.logger.info(f"Browser launched successfully: {self.browser_type}")
            self.visual_logger.success("Browser launched successfully")
            
            # Take screenshot if visual mode
            if self.visual_mode and AutomationConfig.SCREENSHOT_ENABLED:
                await self._take_screenshot("browser_launched")
            
        except PlaywrightError as e:
            self.logger.error(f"Failed to launch browser: {e}")
            self.visual_logger.error(f"Browser launch failed: {e}")
            raise BrowserLaunchException(f"Browser launch failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error launching browser: {e}")
            self.visual_logger.error(f"Unexpected error: {e}")
            raise BrowserLaunchException(f"Unexpected error: {e}")
    
    async def create_context(
        self,
        session_name: str = "default",
        persist_session: Optional[bool] = None,
    ) -> BrowserContext:
        """
        Create a browser context with optional session persistence.
        
        Args:
            session_name: Name for session file
            persist_session: Whether to persist session (default from config)
            
        Returns:
            BrowserContext instance
            
        Raises:
            BrowserLaunchException: If context creation fails
        """
        if not self.browser:
            await self.launch()
        
        persist_session = persist_session if persist_session is not None else AutomationConfig.SESSION_PERSIST_ENABLED
        
        # Determine viewport based on visual mode - FIXED SIZE FOR STABILITY
        if self.visual_mode:
            viewport = {
                "width": AutomationConfig.VISUAL_VIEWPORT_WIDTH,
                "height": AutomationConfig.VISUAL_VIEWPORT_HEIGHT
            }
        else:
            viewport = {"width": 1920, "height": 1080}
        
        context_args = {
            "viewport": viewport,
            "user_agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "accept_downloads": True,
        }
        
        # Add video recording for visual mode
        if self.visual_mode and AutomationConfig.VIDEO_ENABLED:
            timestamp = generate_timestamp()
            video_filename = f"session_{session_name}_{timestamp}.webm"
            self.video_path = AutomationConfig.VIDEO_DIR / video_filename
            context_args["record_video_dir"] = AutomationConfig.VIDEO_DIR
            context_args["record_video_size"] = AutomationConfig.get_video_size()
        
        # Load existing session if available
        session_path = AutomationConfig.get_session_path(session_name)
        if persist_session and session_path.exists():
            self.logger.info(f"Loading existing session: {session_path}")
            try:
                with open(session_path, 'r') as f:
                    storage_state = json.load(f)
                context_args["storage_state"] = storage_state
            except Exception as e:
                self.logger.warning(f"Failed to load session file: {e}")
        
        try:
            self.context = await self.browser.new_context(**context_args)
            self.context.set_default_timeout(self.timeout)
            
            self.logger.info(f"Browser context created: session_name={session_name}")
            return self.context
            
        except PlaywrightError as e:
            self.logger.error(f"Failed to create context: {e}")
            raise BrowserLaunchException(f"Context creation failed: {e}")
    
    async def save_session(self, session_name: str = "default") -> None:
        """
        Save current browser context session to file.
        
        Args:
            session_name: Name for session file
        """
        if not self.context:
            self.logger.warning("No context to save")
            return
        
        session_path = AutomationConfig.get_session_path(session_name)
        
        try:
            storage_state = await self.context.storage_state()
            
            with open(session_path, 'w') as f:
                json.dump(storage_state, f, indent=2)
            
            self.logger.info(f"Session saved: {session_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")
    
    async def is_session_valid(self, session_name: str = "default") -> bool:
        """
        Check if a session file exists and is not expired.
        
        Args:
            session_name: Name of session to check
            
        Returns:
            True if session is valid, False otherwise
        """
        session_path = AutomationConfig.get_session_path(session_name)
        
        if not session_path.exists():
            return False
        
        # Check if session is expired
        session_age = datetime.now() - datetime.fromtimestamp(session_path.stat().st_mtime)
        expiry_hours = AutomationConfig.SESSION_EXPIRY_HOURS
        
        if session_age > timedelta(hours=expiry_hours):
            self.logger.info(f"Session expired: {session_name}")
            return False
        
        return True
    
    async def new_page(self) -> Page:
        """
        Create a new page in the current context.
        
        Returns:
            Page instance
            
        Raises:
            BrowserLaunchException: If page creation fails
        """
        if not self.context:
            await self.create_context()
        
        try:
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout)
            
            self.logger.info("New page created")
            return self.page
            
        except PlaywrightError as e:
            self.logger.error(f"Failed to create page: {e}")
            raise BrowserLaunchException(f"Page creation failed: {e}")
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> None:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            wait_until: When to consider navigation successful (default: networkidle)
            
        Raises:
            TimeoutException: If navigation times out
            NetworkException: If navigation fails due to network error
        """
        if not self.page:
            await self.new_page()
        
        self.logger.info(f"Navigating to: {url}")
        self.visual_logger.step("2/10", f"Navigating to {url}")
        
        try:
            await self.page.goto(url, wait_until=wait_until, timeout=self.timeout)
            self.logger.info(f"Navigation successful: {url}")
            self.visual_logger.success(f"Navigation successful")
            
            # Human-like delay after navigation in visual mode
            await self._human_like_delay()
            
        except PlaywrightError as e:
            if "timeout" in str(e).lower():
                self.logger.error(f"Navigation timeout: {url}")
                self.visual_logger.error(f"Navigation timeout: {url}")
                raise TimeoutException(f"Navigation timeout: {url}")
            else:
                self.logger.error(f"Navigation failed: {e}")
                self.visual_logger.error(f"Navigation failed: {e}")
                raise NetworkException(f"Navigation failed: {e}")
    
    async def wait_for_element(
        self,
        selector: str,
        timeout: Optional[int] = None,
        state: str = "visible",
    ) -> None:
        """
        Wait for an element to be in the specified state.
        
        Args:
            selector: CSS selector for the element
            timeout: Timeout in milliseconds (default from config)
            state: Element state - visible, hidden, attached, detached
            
        Raises:
            TimeoutException: If element does not reach desired state
        """
        if not self.page:
            raise BrowserLaunchException("No page available")
        
        timeout = timeout if timeout is not None else self.timeout
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout, state=state)
            self.logger.debug(f"Element found: {selector}")
            
        except PlaywrightError as e:
            self.logger.error(f"Element not found: {selector}")
            raise TimeoutException(f"Element not found: {selector}")
    
    async def click(self, selector: str, timeout: Optional[int] = None) -> None:
        """
        Click on an element.
        
        Args:
            selector: CSS selector for the element
            timeout: Timeout in milliseconds (default from config)
            
        Raises:
            TimeoutException: If element not found or click fails
        """
        if not self.page:
            raise BrowserLaunchException("No page available")
        
        timeout = timeout if timeout is not None else self.timeout
        
        await self.wait_for_element(selector, timeout=timeout)
        
        # Human-like delay before clicking in visual mode
        await self._human_like_delay()
        
        try:
            await self.page.click(selector, timeout=timeout)
            self.logger.debug(f"Clicked: {selector}")
            
            # Human-like delay after clicking in visual mode
            await self._human_like_delay()
            
        except PlaywrightError as e:
            self.logger.error(f"Click failed: {selector}")
            raise TimeoutException(f"Click failed: {selector}")
    
    async def fill(self, selector: str, value: str, timeout: Optional[int] = None) -> None:
        """
        Fill a form field with a value.
        
        Args:
            selector: CSS selector for the element
            value: Value to fill
            timeout: Timeout in milliseconds (default from config)
            
        Raises:
            TimeoutException: If element not found or fill fails
        """
        if not self.page:
            raise BrowserLaunchException("No page available")
        
        timeout = timeout if timeout is not None else self.timeout
        
        await self.wait_for_element(selector, timeout=timeout)
        
        # Human-like delay before filling in visual mode
        await self._human_like_delay()
        
        try:
            # Use human-like typing in visual mode
            if self.visual_mode:
                # Clear field first
                await self.page.fill(selector, "", timeout=timeout)
                # Type character by character
                await self._human_like_typing(value)
            else:
                await self.page.fill(selector, value, timeout=timeout)
            
            self.logger.debug(f"Filled: {selector}")
            
            # Human-like delay after filling in visual mode
            await self._human_like_delay()
            
        except PlaywrightError as e:
            self.logger.error(f"Fill failed: {selector}")
            raise TimeoutException(f"Fill failed: {selector}")
    
    async def get_text(self, selector: str, timeout: Optional[int] = None) -> str:
        """
        Get text content of an element.
        
        Args:
            selector: CSS selector for the element
            timeout: Timeout in milliseconds (default from config)
            
        Returns:
            Text content of the element
            
        Raises:
            TimeoutException: If element not found
        """
        if not self.page:
            raise BrowserLaunchException("No page available")
        
        timeout = timeout if timeout is not None else self.timeout
        
        await self.wait_for_element(selector, timeout=timeout)
        
        try:
            text = await self.page.text_content(selector, timeout=timeout)
            self.logger.debug(f"Retrieved text: {selector}")
            return text or ""
            
        except PlaywrightError as e:
            self.logger.error(f"Failed to get text: {selector}")
            raise TimeoutException(f"Failed to get text: {selector}")
    
    async def screenshot(self, path: Path) -> None:
        """
        Take a screenshot of the current page.
        
        Args:
            path: Path to save the screenshot
        """
        if not self.page:
            raise BrowserLaunchException("No page available")
        
        await self.page.screenshot(path=str(path))
        self.logger.info(f"Screenshot saved: {path}")
        self.visual_logger.screenshot(path)
    
    async def _take_screenshot(self, milestone: str) -> None:
        """
        Take a screenshot with milestone name (internal method).
        
        Args:
            milestone: Name of the milestone
        """
        if not AutomationConfig.SCREENSHOT_ENABLED:
            return
        
        try:
            timestamp = generate_timestamp()
            filename = f"{milestone}_{timestamp}.png"
            path = AutomationConfig.SCREENSHOT_DIR / filename
            
            if self.page:
                await self.page.screenshot(path=str(path), full_page=True)
                self.visual_logger.screenshot(path)
        except Exception as e:
            self.logger.warning(f"Failed to take screenshot: {e}")
    
    async def _human_like_delay(self) -> None:
        """Add human-like delay between actions in visual mode."""
        if self.visual_mode:
            delay = AutomationConfig.VISUAL_PAUSE_AFTER_ACTION / 1000
            await asyncio.sleep(delay)
    
    async def _human_like_typing(self, text: str) -> None:
        """
        Type text character by character with human-like delay.
        
        Args:
            text: Text to type
        """
        if self.visual_mode:
            # Type character by character
            for char in text:
                await self.page.keyboard.type(char)
                delay = AutomationConfig.VISUAL_TYPING_DELAY / 1000
                await asyncio.sleep(delay)
        else:
            # Type all at once
            await self.page.keyboard.type(text)
    
    async def capture_error_state(self, error: Exception, selector: Optional[str] = None) -> None:
        """
        Capture error state for debugging.
        
        Args:
            error: The exception that occurred
            selector: The selector that failed (if applicable)
        """
        if not self.visual_mode:
            return
        
        self.visual_logger.error_details(error, selector)
        
        # Take screenshot of current state
        if AutomationConfig.SCREENSHOT_ON_ERROR:
            try:
                timestamp = generate_timestamp()
                filename = f"error_{timestamp}.png"
                path = AutomationConfig.SCREENSHOT_DIR / filename
                
                if self.page:
                    await self.page.screenshot(path=str(path), full_page=True)
                    self.visual_logger.screenshot(path)
            except Exception as e:
                self.logger.warning(f"Failed to take error screenshot: {e}")
        
        # Save page HTML
        try:
            timestamp = generate_timestamp()
            filename = f"error_page_{timestamp}.html"
            path = AutomationConfig.SCREENSHOT_DIR / filename
            
            if self.page:
                html_content = await self.page.content()
                with open(path, 'w') as f:
                    f.write(html_content)
                self.visual_logger.info(f"Page HTML saved: {path}")
        except Exception as e:
            self.logger.warning(f"Failed to save page HTML: {e}")
        
        # Get current URL
        try:
            if self.page:
                current_url = self.page.url
                self.visual_logger.info(f"Current URL: {current_url}")
        except Exception as e:
            self.logger.warning(f"Failed to get current URL: {e}")
    
    async def close(self) -> None:
        """Close browser and cleanup resources."""
        self.logger.info("Closing browser...")
        
        try:
            # In visual mode, wait before closing
            if self.visual_mode and AutomationConfig.VISUAL_KEEP_BROWSER_OPEN:
                self.visual_logger.waiting(f"Keeping browser open for {AutomationConfig.VISUAL_BROWSER_CLOSE_DELAY} seconds...")
                await asyncio.sleep(AutomationConfig.VISUAL_BROWSER_CLOSE_DELAY)
            
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            self.logger.info("Browser closed successfully")
            
            # Print video info if available
            if self.visual_mode and self.video_path and self.video_path.exists():
                self.visual_logger.print_video_info(self.video_path)
            
        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.launch()
        await self.create_context()
        await self.new_page()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    @property
    def is_launched(self) -> bool:
        """Check if browser is launched."""
        return self.browser is not None
    
    @property
    def has_context(self) -> bool:
        """Check if context exists."""
        return self.context is not None
    
    @property
    def has_page(self) -> bool:
        """Check if page exists."""
        return self.page is not None
