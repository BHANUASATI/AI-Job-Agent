"""
CAPTCHA Solving Service

Handles CAPTCHA detection and AI-based solving for Overleaf login.
"""

import asyncio
import base64
from typing import Optional, Dict
from pathlib import Path
from utils.logger import get_logger


logger = get_logger(__name__)


class CaptchaSolver:
    """
    CAPTCHA solving service using AI integration.
    
    This service detects CAPTCHAs during login and uses AI to solve them.
    """
    
    def __init__(self):
        self.logger = get_logger("captcha_solver")
        self.max_retries = 3
        self.retry_count = 0
        self.llm = None
    
    def _get_llm(self):
        """Get LLM instance for CAPTCHA solving."""
        if self.llm is None:
            try:
                from services.llm_service import get_llm
                self.llm = get_llm()
                self.logger.info("LLM initialized for CAPTCHA solving")
            except Exception as e:
                self.logger.error(f"Failed to initialize LLM: {e}")
                raise
        return self.llm
    
    async def detect_captcha(self, page) -> bool:
        """
        Detect if CAPTCHA is present on the page.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if CAPTCHA detected, False otherwise
        """
        try:
            # Look for common CAPTCHA indicators
            captcha_selectors = [
                'iframe[src*="recaptcha"]',
                'div[class*="captcha"]',
                'div[id*="captcha"]',
                '[data-sitekey]',
                ',g-recaptcha'
            ]
            
            for selector in captcha_selectors:
                try:
                    captcha_element = await page.query_selector(selector)
                    if captcha_element:
                        self.logger.info(f"CAPTCHA detected using: {selector}")
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            self.logger.error(f"CAPTCHA detection error: {e}")
            return False
    
    async def solve_captcha_with_llm(self, page) -> Optional[str]:
        """
        Solve CAPTCHA using LLM integration from user's configuration.
        
        Args:
            page: Playwright page object
            
        Returns:
            CAPTCHA solution if successful, None otherwise
        """
        try:
            self.logger.info("Attempting to solve CAPTCHA with configured LLM")
            
            # Take screenshot of CAPTCHA
            screenshot_path = Path("logs/screenshots/captcha_challenge.png")
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screenshot_path))
            
            self.logger.info(f"CAPTCHA screenshot saved: {screenshot_path}")
            
            # First try text-based CAPTCHA extraction (works with any LLM)
            text_solution = await self._solve_text_captcha(page)
            if text_solution:
                return text_solution
            
            # If text-based fails, try vision if LLM supports it
            try:
                from langchain_openai import ChatOpenAI
                from langchain_core.messages import HumanMessage
                import base64
                
                # Get user's configured LLM
                llm_config = self._get_llm()
                
                # Check if LLM supports vision (OpenRouter GPT-4o, Claude, etc.)
                vision_models = ['gpt-4o', 'gpt-4-vision', 'claude-3', 'gemini-pro-vision']
                supports_vision = any(model in str(llm_config.model).lower() for model in vision_models)
                
                if supports_vision:
                    self.logger.info("LLM supports vision, attempting image-based solving")
                    
                    # Read and encode image
                    with open(screenshot_path, "rb") as image_file:
                        encoded_image = base64.b64encode(image_file.read()).decode()
                    
                    # Create LLM with vision capabilities using user's config
                    llm = ChatOpenAI(
                        model=llm_config.model,
                        api_key=llm_config.api_key,
                        base_url=llm_config.base_url
                    )
                    
                    # Create message with image
                    message = HumanMessage(
                        content=[
                            {
                                "type": "text",
                                "text": "Please analyze this CAPTCHA image and provide the solution. If it's a text CAPTCHA, extract the text. If it's a reCAPTCHA, describe what needs to be selected. If you cannot solve it, say 'UNSOLVABLE'."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{encoded_image}"
                                }
                            }
                        ]
                    )
                    
                    # Get response
                    response = await llm.ainvoke([message])
                    solution = response.content.strip()
                    
                    self.logger.info(f"LLM CAPTCHA solution: {solution}")
                    
                    if "UNSOLVABLE" not in solution.upper():
                        return solution
                else:
                    self.logger.info(f"LLM {llm_config.model} does not support vision, using text-based approach")
                    
            except Exception as e:
                self.logger.error(f"LLM vision solving failed: {e}")
            
            # Final fallback: use text-based extraction
            return await self._solve_text_captcha(page)
                
        except Exception as e:
            self.logger.error(f"CAPTCHA solving error: {e}")
            return None
    
    async def _solve_text_captcha(self, page) -> Optional[str]:
        """
        Attempt to solve text-based CAPTCHA using LLM.
        
        Args:
            page: Playwright page object
            
        Returns:
            CAPTCHA solution if successful, None otherwise
        """
        try:
            self.logger.info("Attempting text-based CAPTCHA solving")
            
            # Try to extract CAPTCHA text from page
            captcha_text = await page.evaluate('''
                () => {
                    // Look for CAPTCHA text in various locations
                    const selectors = [
                        '.captcha-text',
                        '[id*="captcha"]',
                        '[class*="captcha"]'
                    ];
                    
                    for (const selector of selectors) {
                        const element = document.querySelector(selector);
                        if (element && element.textContent) {
                            return element.textContent.trim();
                        }
                    }
                    
                    return null;
                }
            ''')
            
            if captcha_text:
                self.logger.info(f"Found CAPTCHA text: {captcha_text}")
                
                # Use LLM to solve
                try:
                    llm = self._get_llm()
                    
                    from langchain_core.messages import HumanMessage
                    message = HumanMessage(
                        content=f"Solve this CAPTCHA: {captcha_text}. Return only the solution, nothing else."
                    )
                    
                    response = await llm.ainvoke([message])
                    solution = response.content.strip()
                    
                    self.logger.info(f"LLM solution: {solution}")
                    return solution
                    
                except Exception as e:
                    self.logger.error(f"Text CAPTCHA solving failed: {e}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Text CAPTCHA extraction failed: {e}")
            return None
    
    async def handle_captcha_with_retry(self, page) -> bool:
        """
        Handle CAPTCHA with retry logic using LLM.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if CAPTCHA handled successfully, False otherwise
        """
        self.retry_count = 0
        
        while self.retry_count < self.max_retries:
            try:
                # Detect CAPTCHA
                if not await self.detect_captcha(page):
                    self.logger.info("No CAPTCHA detected")
                    return True
                
                # Solve CAPTCHA with LLM
                solution = await self.solve_captcha_with_llm(page)
                
                if solution:
                    self.logger.info("CAPTCHA solved successfully with LLM")
                    print(f"  ✓ CAPTCHA solved by AI: {solution}")
                    return True
                else:
                    self.retry_count += 1
                    self.logger.warning(f"CAPTCHA solving failed, retry {self.retry_count}/{self.max_retries}")
                    await asyncio.sleep(2)
                    
            except Exception as e:
                self.retry_count += 1
                self.logger.error(f"CAPTCHA handling error: {e}, retry {self.retry_count}/{self.max_retries}")
                await asyncio.sleep(2)
        
        self.logger.error("CAPTCHA handling failed after max retries")
        print("  ⚠ CAPTCHA solving failed after multiple attempts")
        return False


# Singleton instance
captcha_solver = CaptchaSolver()
