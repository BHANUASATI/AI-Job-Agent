"""
Browser automation package for AI Job Agent.

This package provides production-grade browser automation capabilities
with a focus on Overleaf resume management. The module is designed to be
reusable for future automation tasks (LinkedIn, Naukri, Indeed, etc.).

Public API:
    OverleafAutomation: Main class for Overleaf resume automation
"""

import asyncio
from pathlib import Path
from typing import Dict, Optional

from automation.browser_manager import BrowserManager
from automation.config import AutomationConfig
from automation.exceptions import (
    AutomationException,
    LoginFailedException,
    ProjectNotFoundException,
    CompileFailedException,
    DownloadFailedException,
)
from automation.overleaf.login import OverleafLogin
from automation.overleaf.project_manager import OverleafProjectManager
from automation.overleaf.editor import OverleafEditor
from automation.overleaf.downloader import OverleafDownloader
from automation.utils import get_logger
from automation.visual_logger import VisualLogger, ProgressTracker


class OverleafAutomation:
    """
    Main interface for Overleaf resume automation.
    
    This class provides a clean, high-level API for automating resume
    management on Overleaf without exposing Playwright internals to the
    rest of the application.
    
    Example usage:
        ```python
        automation = OverleafAutomation()
        
        pdf_path = await automation.generate_resume(
            project_name="Master Resume",
            updated_sections={
                "skills": "\\item Python, JavaScript, React",
                "experience": "\\item Senior Engineer at Tech Corp"
            }
        )
        ```
    
    Features:
    - Automatic authentication with session persistence
    - Project opening and verification
    - Section-based resume editing
    - LaTeX compilation with error detection
    - PDF download with versioning
    - Comprehensive error handling
    - Structured logging
    - Retry mechanism with exponential backoff
    """
    
    def __init__(
        self,
        headless: Optional[bool] = None,
        project_name: Optional[str] = None,
        visual_mode: Optional[bool] = None,
        visual_logger: Optional[VisualLogger] = None,
    ):
        """
        Initialize OverleafAutomation.
        
        Args:
            headless: Whether to run browser in headless mode (default from config)
            project_name: Default project name (default from config)
            visual_mode: Whether to enable visual execution mode (default from config)
            visual_logger: Visual logger instance for progress tracking
        """
        self.logger = get_logger("overleaf_automation")
        
        # Determine visual mode
        self.visual_mode = visual_mode if visual_mode is not None else (
            AutomationConfig.DEBUG_MODE or AutomationConfig.VISUAL_MODE
        )
        
        # Visual logger
        self.visual_logger = visual_logger or VisualLogger()
        
        # Validate configuration
        try:
            AutomationConfig.validate()
        except ValueError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise
        
        # Initialize components with visual mode support
        self.browser_manager = BrowserManager(
            headless=headless,
            visual_mode=self.visual_mode,
            visual_logger=self.visual_logger
        )
        self.login = OverleafLogin(self.browser_manager)
        self.project_manager = OverleafProjectManager(self.browser_manager)
        self.editor = OverleafEditor(self.browser_manager)
        self.downloader = OverleafDownloader(self.browser_manager)
        
        # Default project name
        self.default_project_name = project_name or AutomationConfig.OVERLEAF_DEFAULT_PROJECT
        
        # Track state
        self._is_authenticated = False
        self._is_project_open = False
        self._output_pdf: Optional[Path] = None
        
        # Progress tracker
        self.steps = [
            "Launching Browser",
            "Opening Overleaf",
            "Logging In",
            "Opening Project",
            "Loading Resume File",
            "Updating Resume",
            "Waiting for Auto Save",
            "Recompiling",
            "Downloading PDF",
            "Completing Execution"
        ]
        self.progress_tracker = ProgressTracker(self.steps, self.visual_logger)
        
        self.logger.info("OverleafAutomation initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def initialize(self) -> None:
        """
        Initialize the automation session.
        
        This launches the browser and authenticates with Overleaf.
        """
        self.logger.info("Initializing automation session")
        
        if self.visual_mode:
            self.visual_logger.start_execution()
        
        try:
            # Launch browser
            await self.browser_manager.launch()
            self.progress_tracker.complete_step(True)
            
            # Authenticate
            self.progress_tracker.next_step()  # Opening Overleaf
            await self.login.ensure_authenticated()
            self._is_authenticated = True
            self.progress_tracker.complete_step(True)
            
            self.progress_tracker.next_step()  # Logging In
            self.progress_tracker.complete_step(True)
            
            # Take screenshot after login in visual mode
            if self.visual_mode:
                await self.browser_manager._take_screenshot("login_successful")
                self.visual_logger.milestone("Login Successful")
            
            self.logger.info("Automation session initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            self.progress_tracker.complete_step(False)
            await self.browser_manager.capture_error_state(e)
            raise AutomationException(f"Initialization failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup and close the automation session."""
        self.logger.info("Cleaning up automation session")
        
        try:
            await self.browser_manager.close()
            self._is_authenticated = False
            self._is_project_open = False
            
            self.logger.info("Automation session cleaned up")
            
            # Print execution summary in visual mode
            if self.visual_mode:
                self.visual_logger.end_execution()
                
                # Print output info
                if self._output_pdf:
                    self.visual_logger.separator()
                    self.visual_logger.info(f"Output PDF: {self._output_pdf}")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    async def generate_resume(
        self,
        project_name: Optional[str] = None,
        updated_sections: Optional[Dict[str, str]] = None,
        filename: Optional[str] = None,
        base_name: Optional[str] = None,
        recompile: bool = True,
    ) -> Path:
        """
        Generate a resume by editing sections and downloading the PDF.
        
        This is the main entry point for resume generation. It handles
        the complete workflow: authentication, project opening, editing,
        compilation, and download.
        
        Args:
            project_name: Name of the Overleaf project (default from config)
            updated_sections: Dictionary mapping section names to LaTeX content
                Example: {"skills": "\\item Python, JavaScript", "experience": "..."}
            filename: Custom filename for the downloaded PDF (optional)
            base_name: Base name for versioned filename (e.g., "python_backend")
            recompile: Whether to recompile after editing (default: True)
            
        Returns:
            Absolute path to the downloaded PDF
            
        Raises:
            LoginFailedException: If authentication fails
            ProjectNotFoundException: If project cannot be found
            CompileFailedException: If LaTeX compilation fails
            DownloadFailedException: If PDF download fails
            AutomationException: For other automation errors
        """
        project_name = project_name or self.default_project_name
        
        self.logger.info(f"Generating resume for project: {project_name}")
        
        try:
            # Ensure authenticated
            if not self._is_authenticated:
                await self.initialize()
            
            # Open project
            self.progress_tracker.next_step()  # Opening Project
            await self.project_manager.open_project(project_name)
            self._is_project_open = True
            self.progress_tracker.complete_step(True)
            
            if self.visual_mode:
                await self.browser_manager._take_screenshot("project_opened")
                self.visual_logger.milestone("Project Opened")
            
            # Open main file
            self.progress_tracker.next_step()  # Loading Resume File
            await self.editor.open_file("master_resume.tex")
            self.progress_tracker.complete_step(True)
            
            if self.visual_mode:
                await self.browser_manager._take_screenshot("resume_loaded")
                self.visual_logger.milestone("Resume File Loaded")
            
            # Edit sections if provided
            if updated_sections:
                self.progress_tracker.next_step()  # Updating Resume
                self.logger.info(f"Editing {len(updated_sections)} sections")
                await self.editor.edit_sections(updated_sections)
                self.progress_tracker.complete_step(True)
                
                if self.visual_mode:
                    await self.browser_manager._take_screenshot("resume_updated")
                    self.visual_logger.milestone("Resume Updated")
            else:
                self.progress_tracker.next_step()
                self.progress_tracker.complete_step(True)  # Skip editing
            
            # Wait for autosave
            self.progress_tracker.next_step()  # Waiting for Auto Save
            if self.visual_mode:
                self.visual_logger.waiting("Waiting for autosave...")
            await asyncio.sleep(2)  # Wait for autosave
            self.progress_tracker.complete_step(True)
            
            # Recompile if requested
            if recompile:
                self.progress_tracker.next_step()  # Recompiling
                self.logger.info("Recompiling LaTeX")
                compile_result = await self.editor.recompile()
                
                if compile_result['status'] == 'failed':
                    error_msg = f"Compilation failed with {len(compile_result['errors'])} errors"
                    self.logger.error(error_msg)
                    self.progress_tracker.complete_step(False)
                    raise CompileFailedException(error_msg)
                
                self.progress_tracker.complete_step(True)
                
                if self.visual_mode:
                    await self.browser_manager._take_screenshot("compilation_completed")
                    self.visual_logger.milestone("Compilation Completed")
            else:
                self.progress_tracker.next_step()
                self.progress_tracker.complete_step(True)  # Skip recompile
            
            # Verify no editor errors
            await self.editor.verify_no_editor_errors()
            
            # Download PDF
            self.progress_tracker.next_step()  # Downloading PDF
            self.logger.info("Downloading PDF")
            pdf_path = await self.downloader.download_pdf(
                filename=filename,
                save_to_versions=True,
                base_name=base_name,
            )
            self._output_pdf = pdf_path
            self.progress_tracker.complete_step(True)
            
            if self.visual_mode:
                await self.browser_manager._take_screenshot("pdf_downloaded")
                self.visual_logger.milestone("PDF Downloaded")
            
            # Complete execution
            self.progress_tracker.next_step()  # Completing Execution
            self.progress_tracker.complete_step(True)
            
            self.logger.info(f"Resume generated successfully: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            self.logger.error(f"Resume generation failed: {e}")
            self.progress_tracker.complete_step(False)
            await self.browser_manager.capture_error_state(e)
            raise
    
    async def edit_resume(
        self,
        project_name: Optional[str] = None,
        updated_sections: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Edit resume sections without downloading.
        
        This is useful when you want to make edits but handle
        compilation and download separately.
        
        Args:
            project_name: Name of the Overleaf project (default from config)
            updated_sections: Dictionary mapping section names to LaTeX content
            
        Returns:
            True if editing successful
            
        Raises:
            ProjectNotFoundException: If project cannot be found
            EditorNotLoadedException: If editing fails
        """
        project_name = project_name or self.default_project_name
        
        self.logger.info(f"Editing resume for project: {project_name}")
        
        try:
            # Ensure authenticated
            if not self._is_authenticated:
                await self.initialize()
            
            # Open project
            await self.project_manager.open_project(project_name)
            self._is_project_open = True
            
            # Open main file
            await self.editor.open_file("master_resume.tex")
            
            # Edit sections
            if updated_sections:
                success = await self.editor.edit_sections(updated_sections)
                return success
            
            return True
            
        except Exception as e:
            self.logger.error(f"Resume editing failed: {e}")
            raise
    
    async def download_pdf(
        self,
        project_name: Optional[str] = None,
        filename: Optional[str] = None,
        base_name: Optional[str] = None,
    ) -> Path:
        """
        Download the current PDF without editing.
        
        This is useful when you want to download the latest compiled
        PDF without making any edits.
        
        Args:
            project_name: Name of the Overleaf project (default from config)
            filename: Custom filename for the downloaded PDF (optional)
            base_name: Base name for versioned filename
            
        Returns:
            Absolute path to the downloaded PDF
            
        Raises:
            ProjectNotFoundException: If project cannot be found
            DownloadFailedException: If download fails
        """
        project_name = project_name or self.default_project_name
        
        self.logger.info(f"Downloading PDF for project: {project_name}")
        
        try:
            # Ensure authenticated
            if not self._is_authenticated:
                await self.initialize()
            
            # Open project
            await self.project_manager.open_project(project_name)
            self._is_project_open = True
            
            # Download PDF
            pdf_path = await self.downloader.download_pdf(
                filename=filename,
                save_to_versions=True,
                base_name=base_name,
            )
            
            self.logger.info(f"PDF downloaded successfully: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            self.logger.error(f"PDF download failed: {e}")
            raise
    
    async def recompile_resume(
        self,
        project_name: Optional[str] = None,
    ) -> Dict:
        """
        Recompile the current resume without editing.
        
        Args:
            project_name: Name of the Overleaf project (default from config)
            
        Returns:
            Dictionary with compilation status and errors
            
        Raises:
            ProjectNotFoundException: If project cannot be found
            CompileFailedException: If compilation fails
        """
        project_name = project_name or self.default_project_name
        
        self.logger.info(f"Recompiling resume for project: {project_name}")
        
        try:
            # Ensure authenticated
            if not self._is_authenticated:
                await self.initialize()
            
            # Open project
            await self.project_manager.open_project(project_name)
            self._is_project_open = True
            
            # Open main file
            await self.editor.open_file("master_resume.tex")
            
            # Recompile
            result = await self.editor.recompile()
            
            self.logger.info(f"Recompile completed: {result['status']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Recompile failed: {e}")
            raise
    
    async def list_projects(self) -> list:
        """
        List all available Overleaf projects.
        
        Returns:
            List of project names
        """
        self.logger.info("Listing projects")
        
        try:
            # Ensure authenticated
            if not self._is_authenticated:
                await self.initialize()
            
            projects = await self.project_manager.list_projects()
            return projects
            
        except Exception as e:
            self.logger.error(f"Failed to list projects: {e}")
            raise


__all__ = [
    'OverleafAutomation',
    'AutomationException',
    'LoginFailedException',
    'ProjectNotFoundException',
    'CompileFailedException',
    'DownloadFailedException',
]
