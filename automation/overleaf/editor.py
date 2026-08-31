"""
Overleaf editor module for resume editing.

Handles opening files, editing specific sections, triggering recompilation,
and verifying compilation status.
"""

import re
from typing import Dict, Optional, List

from automation.browser_manager import BrowserManager
from automation.config import AutomationConfig
from automation.exceptions import (
    EditorNotLoadedException,
    CompileFailedException,
    TimeoutException,
)
from automation.overleaf.selectors import OverleafSelectors
from automation.utils import get_logger, retry_with_backoff, parse_latex_error


class OverleafEditor:
    """
    Manages Overleaf editor operations for resume editing.
    
    Features:
    - Open specific files in editor
    - Edit specific LaTeX sections (Skills, Experience, etc.)
    - Trigger recompilation
    - Wait for compilation to complete
    - Detect compilation errors
    - Verify autosave completion
    - Maintain LaTeX formatting
    """
    
    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize OverleafEditor.
        
        Args:
            browser_manager: BrowserManager instance for browser operations
        """
        self.browser_manager = browser_manager
        self.logger = get_logger("overleaf_editor")
        self.selectors = OverleafSelectors()
    
    async def open_file(self, filename: str = "master_resume.tex") -> bool:
        """
        Open a specific file in the editor.
        
        Args:
            filename: Name of the file to open
            
        Returns:
            True if file opened successfully
            
        Raises:
            EditorNotLoadedException: If file cannot be opened
        """
        self.logger.info(f"Opening file: {filename}")
        
        try:
            # Get file selector
            file_selector = self.selectors.get_file_selector(filename)
            
            # Wait for file to appear in file tree
            await self.browser_manager.wait_for_element(
                file_selector,
                timeout=AutomationConfig.BROWSER_TIMEOUT
            )
            
            # Click on file to open
            await retry_with_backoff(
                lambda: self.browser_manager.click(file_selector),
                exceptions=(TimeoutException,),
                logger=self.logger,
            )
            
            # Wait for editor to load the file content
            await self._wait_for_editor_ready()
            
            self.logger.info(f"File opened successfully: {filename}")
            return True
            
        except TimeoutException as e:
            self.logger.error(f"Failed to open file: {filename}")
            raise EditorNotLoadedException(f"Failed to open file: {filename}")
    
    async def _wait_for_editor_ready(self) -> None:
        """
        Wait for editor to be ready for editing.
        
        Raises:
            EditorNotLoadedException: If editor is not ready
        """
        self.logger.info("Waiting for editor to be ready")
        
        try:
            # Wait for editor content area
            await self.browser_manager.wait_for_element(
                self.selectors.EDITOR_CONTENT,
                timeout=AutomationConfig.EDITOR_LOAD_TIMEOUT
            )
            
            # Wait for autosave indicator to show "saved"
            await self.browser_manager.wait_for_element(
                self.selectors.AUTOSAVE_SAVED,
                timeout=AutomationConfig.AUTOSAVE_WAIT_TIMEOUT
            )
            
            self.logger.info("Editor is ready")
            
        except TimeoutException as e:
            self.logger.error(f"Editor not ready: {e}")
            raise EditorNotLoadedException("Editor not ready within timeout")
    
    async def get_file_content(self) -> str:
        """
        Get the current content of the open file.
        
        Returns:
            File content as string
            
        Raises:
            EditorNotLoadedException: If content cannot be retrieved
        """
        self.logger.info("Getting file content")
        
        try:
            # Select all content in editor
            await self.browser_manager.page.keyboard.press("Control+A")
            
            # Copy content
            await self.browser_manager.page.keyboard.press("Control+C")
            
            # Get clipboard content
            # Note: Playwright doesn't have direct clipboard access
            # Alternative: get content from editor element
            content = await self.browser_manager.page.evaluate(
                """() => {
                    const editor = document.querySelector('.ace_editor');
                    if (editor) {
                        const ace = editor.ace;
                        if (ace) {
                            return ace.getValue();
                        }
                    }
                    return '';
                }"""
            )
            
            self.logger.info(f"Retrieved {len(content)} characters")
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to get file content: {e}")
            raise EditorNotLoadedException("Failed to get file content")
    
    async def edit_section(
        self,
        section_name: str,
        new_content: str,
    ) -> bool:
        """
        Edit a specific section in the LaTeX file.
        
        This method replaces only the specified section while preserving
        the rest of the file structure and LaTeX formatting.
        
        Args:
            section_name: Name of section to edit (e.g., 'skills', 'experience')
            new_content: New LaTeX content for the section
            
        Returns:
            True if edit successful
            
        Raises:
            EditorNotLoadedException: If edit fails
        """
        self.logger.info(f"Editing section: {section_name}")
        
        try:
            # Get current file content
            current_content = await self.get_file_content()
            
            # Use AI resume editor for intelligent updates
            try:
                import sys
                from pathlib import Path
                project_root = Path(__file__).parent.parent.parent
                sys.path.insert(0, str(project_root))
                
                from services.ai_resume_editor import ai_resume_editor
                
                updated_content = await ai_resume_editor.update_resume_section(
                    current_content,
                    section_name,
                    new_content
                )
                
                self.logger.info(f"Used AI editor for section: {section_name}")
                
            except ImportError:
                self.logger.warning("AI resume editor not available, using simple replacement")
                # Fallback to simple replacement
                section_pattern = self.selectors.get_section_selector(section_name)
                updated_content = self._replace_latex_section(
                    current_content,
                    section_pattern,
                    new_content
                )
            
            if updated_content == current_content:
                self.logger.warning(f"Section not found or no changes made: {section_name}")
                return False
            
            # Replace entire content (Overleaf editor handles this well)
            await self._replace_entire_content(updated_content)
            
            # Wait for autosave
            await self._wait_for_autosave()
            
            self.logger.info(f"Section edited successfully: {section_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to edit section: {section_name}")
            raise EditorNotLoadedException(f"Failed to edit section: {section_name}")
    
    def _replace_latex_section(
        self,
        content: str,
        section_pattern: str,
        new_content: str,
    ) -> str:
        """
        Replace a LaTeX section with new content.
        
        Args:
            content: Original LaTeX content
            section_pattern: Pattern to identify the section
            new_content: New content for the section
            
        Returns:
            Updated LaTeX content
        """
        # Convert pattern to regex
        # This is a simplified approach - production would need more robust LaTeX parsing
        pattern = re.escape(section_pattern)
        
        # Find section start
        section_start = re.search(pattern, content, re.IGNORECASE)
        if not section_start:
            return content
        
        # Find next section (to determine where current section ends)
        next_section = re.search(
            r'\\section\{',
            content[section_start.end():],
            re.IGNORECASE
        )
        
        if next_section:
            # Replace content between current section and next section
            end_pos = section_start.end() + next_section.start()
            updated = (
                content[:section_start.end()] +
                '\n' + new_content + '\n' +
                content[end_pos:]
            )
        else:
            # No next section, replace till end of file
            updated = (
                content[:section_start.end()] +
                '\n' + new_content + '\n' +
                content[section_start.end():]
            )
        
        return updated
    
    async def _replace_entire_content(self, new_content: str) -> None:
        """
        Replace entire file content in editor.
        
        Args:
            new_content: New content to set
       ."""
        self.logger.info("Replacing entire file content")
        
        try:
            # Select all content
            await self.browser_manager.page.keyboard.press("Control+A")
            
            # Type new content
            await self.browser_manager.page.keyboard.type(new_content)
            
            self.logger.info("Content replaced")
            
        except Exception as e:
            self.logger.error(f"Failed to replace content: {e}")
            raise EditorNotLoadedException("Failed to replace content")
    
    async def _wait_for_autosave(self) -> None:
        """
        Wait for autosave to complete.
        
        Raises:
            TimeoutException: If autosave doesn't complete
        """
        self.logger.info("Waiting for autosave")
        
        try:
            # Wait for autosave indicator to show "saved"
            await self.browser_manager.wait_for_element(
                self.selectors.AUTOSAVE_SAVED,
                timeout=AutomationConfig.AUTOSAVE_WAIT_TIMEOUT
            )
            
            self.logger.info("Autosave completed")
            
        except TimeoutException as e:
            self.logger.warning(f"Autosave timeout (may not be critical): {e}")
    
    async def recompile(self) -> Dict:
        """
        Trigger LaTeX recompilation and wait for completion.
        
        Returns:
            Dictionary with compilation status and any errors
            
        Raises:
            CompileFailedException: If compilation fails
        """
        self.logger.info("Triggering recompilation")
        
        try:
            # Click recompile button
            await retry_with_backoff(
                lambda: self.browser_manager.click(self.selectors.RECOMPILE_BUTTON),
                exceptions=(TimeoutException,),
                logger=self.logger,
            )
            
            # Wait for compilation to complete
            result = await self._wait_for_compilation()
            
            self.logger.info(f"Compilation completed: {result['status']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Compilation failed: {e}")
            raise CompileFailedException(f"Compilation failed: {e}")
    
    async def _wait_for_compilation(self) -> Dict:
        """
        Wait for compilation to complete and check status with enhanced error detection.
        
        Returns:
            Dictionary with status and error information
            
        Raises:
            CompileFailedException: If compilation fails
        """
        self.logger.info("Waiting for compilation with enhanced error detection")
        
        try:
            # Wait for compile status (either success or error)
            await self.browser_manager.page.wait_for_selector(
                f"{self.selectors.COMPILE_STATUS}, {self.selectors.COMPILE_ERROR}",
                timeout=AutomationConfig.COMPILE_TIMEOUT
            )
            
            # Check for errors first
            error_element = await self.browser_manager.page.query_selector(
                self.selectors.COMPILE_ERROR
            )
            
            if error_element:
                # Get error log
                error_log = await self._get_compile_log()
                
                # Parse LaTeX errors
                error_info = parse_latex_error(error_log)
                
                self.logger.error(f"Compilation failed with {error_info['error_count']} errors")
                
                # Save errors to logs
                self._save_compile_errors(error_log, error_info)
                
                # Take screenshot for debugging
                try:
                    screenshot_path = AutomationConfig.SCREENSHOT_DIR / "compile_error.png"
                    await self.browser_manager.page.screenshot(path=str(screenshot_path))
                    self.logger.info(f"Compile error screenshot saved: {screenshot_path}")
                except:
                    pass
                
                return {
                    'status': 'failed',
                    'errors': error_info['errors'],
                    'raw_log': error_log,
                    'error_info': error_info
                }
            
            # Check for success with multiple indicators
            success_indicators = [
                self.selectors.COMPILE_SUCCESS,
                '[data-test-id="compile-success"]',
                '.compile-success',
                '[class*="success"]'
            ]
            
            compilation_successful = False
            for indicator in success_indicators:
                try:
                    success_element = await self.browser_manager.page.query_selector(indicator)
                    if success_element:
                        compilation_successful = True
                        self.logger.info(f"Compilation successful (detected via: {indicator})")
                        break
                except:
                    continue
            
            if compilation_successful:
                self.logger.info("Compilation verified successful")
                return {
                    'status': 'success',
                    'errors': [],
                    'raw_log': '',
                    'error_info': None
                }
            
            # If no clear success or error, check for warnings
            self.logger.warning("Compilation status unclear, checking for warnings...")
            return {
                'status': 'unknown',
                'errors': [],
                'raw_log': '',
                'error_info': None
            }
            
        except Exception as e:
            self.logger.error(f"Compilation monitoring error: {e}")
            raise CompileFailedException(f"Compilation monitoring failed: {e}")
    
    def _save_compile_errors(self, error_log: str, error_info: Dict) -> None:
        """
        Save compilation errors to log file for debugging.
        
        Args:
            error_log: Raw error log
            error_info: Parsed error information
        """
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_log_path = AutomationConfig.LOG_DIR / f"compile_errors_{timestamp}.log"
            
            with open(error_log_path, 'w') as f:
                f.write(f"Compilation Errors - {timestamp}\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Total Errors: {error_info['error_count']}\n\n")
                f.write("Parsed Errors:\n")
                for error in error_info['errors']:
                    f.write(f"  - Line {error['line']}: {error['message']}\n")
                f.write("\nRaw Log:\n")
                f.write(error_log)
            
            self.logger.info(f"Compile errors saved to: {error_log_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save compile errors: {e}")
    
    async def _get_compile_log(self) -> str:
        """
        Get the compilation error log.
        
        Returns:
            Error log as string
        """
        self.logger.info("Getting compile log")
        
        try:
            # Try to get compile log element
            log_element = await self.browser_manager.page.query_selector(
                self.selectors.COMPILE_LOG_OUTPUT
            )
            
            if log_element:
                log_text = await log_element.text_content()
                return log_text or ""
            
            return ""
            
        except Exception as e:
            self.logger.warning(f"Failed to get compile log: {e}")
            return ""
    
    async def verify_no_editor_errors(self) -> bool:
        """
        Verify that there are no editor errors displayed.
        
        Returns:
            True if no errors
        """
        self.logger.info("Verifying no editor errors")
        
        try:
            # Check for error messages
            error_element = await self.browser_manager.page.query_selector(
                self.selectors.ERROR_MESSAGE
            )
            
            if error_element:
                error_text = await error_element.text_content()
                self.logger.warning(f"Editor error detected: {error_text}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Error checking for editor errors: {e}")
            return True  # Assume no errors if check fails
    
    async def edit_sections(
        self,
        sections: Dict[str, str],
    ) -> bool:
        """
        Edit multiple sections in sequence.
        
        Args:
            sections: Dictionary mapping section names to new content
            
        Returns:
            True if all edits successful
        """
        self.logger.info(f"Editing {len(sections)} sections")
        
        success = True
        for section_name, new_content in sections.items():
            try:
                await self.edit_section(section_name, new_content)
            except Exception as e:
                self.logger.error(f"Failed to edit section {section_name}: {e}")
                success = False
        
        return success
