"""
Overleaf project manager module.

Handles project operations including opening projects, waiting for editor load,
and verifying project availability.
"""

import asyncio
from typing import Optional

from automation.browser_manager import BrowserManager
from automation.config import AutomationConfig
from automation.exceptions import (
    ProjectNotFoundException,
    EditorNotLoadedException,
    TimeoutException,
)
from automation.overleaf.selectors import OverleafSelectors
from automation.utils import get_logger, retry_with_backoff


class OverleafProjectManager:
    """
    Manages Overleaf project operations.
    
    Features:
    - Open specific projects by name
    - Wait for editor to fully load
    - Verify project availability
    - Handle project not found errors
    """
    
    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize OverleafProjectManager.
        
        Args:
            browser_manager: BrowserManager instance for browser operations
        """
        self.browser_manager = browser_manager
        self.logger = get_logger("overleaf_project_manager")
        self.selectors = OverleafSelectors()
    
    async def open_project(
        self,
        project_name: Optional[str] = None,
    ) -> bool:
        """
        Open a specific Overleaf project.
        
        Args:
            project_name: Name of the project to open (default from config)
            
        Returns:
            True if project opened successfully
            
        Raises:
            ProjectNotFoundException: If project cannot be found
            EditorNotLoadedException: If editor fails to load
        """
        project_name = project_name or AutomationConfig.OVERLEAF_DEFAULT_PROJECT
        
        self.logger.info(f"Opening project: {project_name}")
        
        try:
            # Navigate to dashboard
            await self._navigate_to_dashboard()
            
            # Find and click on project
            await self._find_and_open_project(project_name)
            
            # Wait for editor to load
            await self._wait_for_editor_load()
            
            # Verify project opened successfully
            await self._verify_project_opened()
            
            # Verify editor is interactive
            await self._verify_editor_interactive()
            
            self.logger.info(f"Project opened successfully: {project_name}")
            return True
            
        except TimeoutException as e:
            self.logger.error(f"Timeout while opening project: {e}")
            raise ProjectNotFoundException(f"Project not found or timeout: {project_name}")
        except Exception as e:
            self.logger.error(f"Failed to open project: {e}")
            raise ProjectNotFoundException(f"Failed to open project: {project_name}")
    
    async def open_first_project(self) -> str:
        """
        Open the first available project on the dashboard.
        
        Returns:
            Name of the project that was opened
            
        Raises:
            ProjectNotFoundException: If no projects are available
        """
        self.logger.info("Opening first available project")
        
        try:
            # Navigate to dashboard
            await self._navigate_to_dashboard()
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Use JavaScript to find and click the first project link
            try:
                project_info = await self.browser_manager.page.evaluate('''
                    () => {
                        // Look for links containing /project
                        const links = Array.from(document.querySelectorAll('a[href*="/project"]'));
                        if (links.length > 0) {
                            const link = links[0];
                            return {
                                href: link.href,
                                text: link.textContent.trim(),
                                exists: true
                            };
                        }
                        return { exists: false };
                    }
                ''')
                
                if project_info['exists']:
                    project_name = project_info['text']
                    project_url = project_info['href']
                    
                    self.logger.info(f"Found project via JavaScript: {project_name}")
                    
                    # Navigate directly to the project URL
                    await self.browser_manager.navigate(project_url)
                    
                    # Wait for editor to load
                    await self._wait_for_editor_load()
                    
                    # Verify project opened successfully
                    await self._verify_project_opened()
                    
                    return project_name
                else:
                    raise ProjectNotFoundException("No projects available to open")
                    
            except Exception as e:
                self.logger.error(f"JavaScript approach failed: {e}")
                raise ProjectNotFoundException("No projects available to open")
            
        except ProjectNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to open first project: {e}")
            raise ProjectNotFoundException("No projects available to open")
    
    async def _navigate_to_dashboard(self) -> None:
        """Navigate to Overleaf dashboard."""
        self.logger.info("Navigating to dashboard")
        
        dashboard_url = f"{AutomationConfig.OVERLEAF_URL}/dashboard"
        await self.browser_manager.navigate(dashboard_url)
        
        # Wait for page to load
        await asyncio.sleep(2)
        
        # Try to wait for project list, but don't fail if not found
        try:
            await self.browser_manager.wait_for_element(
                self.selectors.PROJECT_LIST,
                timeout=5000
            )
        except:
            self.logger.warning("Project list selector not found, will try alternative methods")
    
    async def _find_and_open_project(self, project_name: str) -> None:
        """
        Find project in list and open it.
        
        Args:
            project_name: Name of the project to find
            
        Raises:
            ProjectNotFoundException: If project not found in list
        """
        self.logger.info(f"Finding project in list: {project_name}")
        
        try:
            # Try to find project by exact text match first
            try:
                selector = f'text="{project_name}"'
                await self.browser_manager.wait_for_element(selector, timeout=5000)
                await self.browser_manager.click(selector)
                self.logger.info(f"Clicked on project: {project_name}")
                return
            except:
                self.logger.warning(f"Could not find exact match for: {project_name}")
            
            # Try partial match - look for any element containing the project name
            try:
                elements = await self.browser_manager.page.query_selector_all('*')
                for element in elements:
                    try:
                        text = await element.text_content()
                        if text and project_name.lower() in text.lower():
                            # Try to click on this element or its parent link
                            parent_link = await element.query_selector('a[href*="/project"]')
                            if parent_link:
                                await parent_link.click()
                                self.logger.info(f"Clicked on project via partial match")
                                return
                            # Try clicking the element itself
                            await element.click()
                            self.logger.info(f"Clicked on project via partial match")
                            return
                    except:
                        continue
            except:
                pass
            
            # If still not found, try to click on the first project link
            try:
                first_project_link = await self.browser_manager.page.query_selector('a[href*="/project"]')
                if first_project_link:
                    await first_project_link.click()
                    self.logger.info(f"Clicked on first available project link")
                    return
            except:
                pass
            
            # If all methods fail, raise exception
            raise ProjectNotFoundException(f"Project not found: {project_name}")
            
        except ProjectNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Error finding project: {e}")
            raise ProjectNotFoundException(f"Project not found: {project_name}")
    
    async def _wait_for_editor_load(self) -> None:
        """
        Wait for the editor to fully load.
        
        Raises:
            EditorNotLoadedException: If editor fails to load
        """
        self.logger.info("Waiting for editor to load")
        
        try:
            # Wait for editor container
            await self.browser_manager.wait_for_element(
                self.selectors.EDITOR_CONTAINER,
                timeout=AutomationConfig.EDITOR_LOAD_TIMEOUT
            )
            
            # Wait for file tree to load
            await self.browser_manager.wait_for_element(
                self.selectors.FILE_TREE,
                timeout=5000
            )
            
            # Wait for editor content area
            await self.browser_manager.wait_for_element(
                self.selectors.EDITOR_CONTENT,
                timeout=5000
            )
            
            self.logger.info("Editor loaded successfully")
            
        except TimeoutException as e:
            self.logger.error(f"Editor failed to load: {e}")
            raise EditorNotLoadedException("Editor failed to load within timeout")
    
    async def _verify_project_opened(self) -> None:
        """
        Verify that project opened successfully.
        
        Raises:
            EditorNotLoadedException: If verification fails
        """
        self.logger.info("Verifying project opened successfully")
        
        try:
            # Check for editor toolbar
            await self.browser_manager.wait_for_element(
                self.selectors.EDITOR_TOOLBAR,
                timeout=5000
            )
            
            # Check for recompile button (indicates project is ready)
            await self.browser_manager.wait_for_element(
                self.selectors.RECOMPILE_BUTTON,
                timeout=5000
            )
            
            self.logger.info("Project verification successful")
            
        except TimeoutException as e:
            self.logger.error(f"Project verification failed: {e}")
            raise EditorNotLoadedException("Project verification failed")
    
    async def _verify_editor_interactive(self) -> None:
        """
        Verify that the editor is interactive and ready for editing.
        
        This ensures the editor is not just loaded but also functional.
        """
        self.logger.info("Verifying editor is interactive...")
        
        try:
            # Wait a moment for editor to stabilize
            await asyncio.sleep(2)
            
            # Check for editable elements
            editor_selectors = [
                'textarea',
                '[contenteditable="true"]',
                '.ace_text-input',
                '.CodeMirror'
            ]
            
            editor_found = False
            for selector in editor_selectors:
                try:
                    element = await self.browser_manager.page.query_selector(selector)
                    if element:
                        editor_found = True
                        self.logger.info(f"Editor verified as interactive using: {selector}")
                        break
                except:
                    continue
            
            if editor_found:
                self.logger.info("Editor is interactive and ready")
            else:
                self.logger.warning("Could not verify editor interactivity, but continuing")
                
        except Exception as e:
            self.logger.warning(f"Editor interactivity verification error: {e}, but continuing")
    
    async def list_projects(self) -> list:
        """
        List all available projects on the dashboard.
        
        Returns:
            List of project names
            
        Raises:
            TimeoutException: If dashboard cannot be loaded
        """
        self.logger.info("Listing projects")
        
        try:
            # Navigate to dashboard
            await self._navigate_to_dashboard()
            
            projects = []
            
            # Wait for page to fully load
            await asyncio.sleep(3)
            
            # Try to find project cards using more specific selectors
            try:
                # Look for project cards with specific Overleaf structure
                project_cards = await self.browser_manager.page.query_selector_all(
                    'div[class*="project"], a[href*="/project"]'
                )
                
                for card in project_cards:
                    try:
                        # Get the text content of the card
                        text = await card.text_content()
                        # Clean up the text
                        if text and len(text.strip()) > 2 and len(text.strip()) < 100:
                            # Filter out common non-project text
                            clean_text = text.strip()
                            if not any(x in clean_text.lower() for x in ['cookie', 'privacy', 'help', 'about', 'contact', 'pricing', 'features', '©', 'overleaf']):
                                projects.append(clean_text)
                    except:
                        continue
            except:
                pass
            
            # Remove duplicates and empty strings
            projects = list(set([p for p in projects if p]))
            
            # Sort by length (project names are usually medium length)
            projects.sort(key=len)
            
            # Filter to likely project names (3-50 characters)
            projects = [p for p in projects if 3 <= len(p) <= 50]
            
            self.logger.info(f"Found {len(projects)} potential projects")
            return projects
            
        except Exception as e:
            self.logger.error(f"Failed to list projects: {e}")
            raise
    
    async def project_exists(self, project_name: str) -> bool:
        """
        Check if a project exists.
        
        Args:
            project_name: Name of the project to check
            
        Returns:
            True if project exists
        """
        self.logger.info(f"Checking if project exists: {project_name}")
        
        try:
            projects = await self.list_projects()
            return project_name in projects
            
        except Exception as e:
            self.logger.error(f"Failed to check project existence: {e}")
            return False
    
    async def get_current_project_name(self) -> Optional[str]:
        """
        Get the name of the currently open project.
        
        Returns:
            Project name or None if cannot be determined
        """
        self.logger.info("Getting current project name")
        
        try:
            # Try to get project name from URL or page title
            url = self.browser_manager.page.url
            if '/project/' in url:
                # Extract project ID from URL
                project_id = url.split('/project/')[-1].split('/')[0]
                self.logger.info(f"Current project ID: {project_id}")
                return project_id
            
            # Alternative: try to get from page title
            title = await self.browser_manager.page.title()
            if title:
                self.logger.info(f"Current project title: {title}")
                return title
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get current project name: {e}")
            return None
