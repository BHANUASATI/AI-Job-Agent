"""
Overleaf PDF downloader module.

Handles downloading compiled PDFs with versioning, overwrite protection,
and download verification.
"""

from pathlib import Path
from typing import Optional

from automation.browser_manager import BrowserManager
from automation.config import AutomationConfig
from automation.exceptions import (
    DownloadFailedException,
    TimeoutException,
)
from automation.overleaf.selectors import OverleafSelectors
from automation.utils import (
    get_logger,
    generate_timestamp,
    sanitize_filename,
    ensure_unique_filepath,
)


class OverleafDownloader:
    """
    Manages PDF download operations from Overleaf.
    
    Features:
    - Download latest compiled PDF
    - Configurable download directory
    - Unique filename generation with timestamp
    - Overwrite protection
    - Wait for download completion
    - Verify PDF exists after download
    - Resume versioning with timestamps
    """
    
    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize OverleafDownloader.
        
        Args:
            browser_manager: BrowserManager instance for browser operations
        """
        self.browser_manager = browser_manager
        self.logger = get_logger("overleaf_downloader")
        self.selectors = OverleafSelectors()
    
    async def download_pdf(
        self,
        filename: Optional[str] = None,
        save_to_versions: bool = True,
        base_name: Optional[str] = None,
    ) -> Path:
        """
        Download the latest compiled PDF from Overleaf.
        
        Args:
            filename: Custom filename for the downloaded PDF (optional)
            save_to_versions: Whether to save to resume_versions directory
            base_name: Base name for versioned filename
            
        Returns:
            Absolute path to the downloaded PDF
            
        Raises:
            DownloadFailedException: If download fails
        """
        self.logger.info("Starting PDF download")
        
        try:
            # Determine download path
            if filename:
                download_path = AutomationConfig.get_download_path(filename)
            else:
                timestamp = generate_timestamp()
                base_name = base_name or "resume"
                filename = f"{base_name}_{timestamp}.pdf"
                
                if save_to_versions:
                    download_path = AutomationConfig.get_resume_version_path(
                        base_name,
                        timestamp
                    )
                else:
                    download_path = AutomationConfig.get_download_path(filename)
            
            # Ensure unique filename (overwrite protection)
            download_path = ensure_unique_filepath(download_path)
            
            # Setup download handler
            download_promise = self._setup_download_handler(download_path)
            
            # Click download button
            await self._trigger_download()
            
            # Wait for download to complete
            await self._wait_for_download(download_promise, download_path)
            
            # Verify download
            await self._verify_download(download_path)
            
            self.logger.info(f"PDF downloaded successfully: {download_path}")
            return download_path
            
        except Exception as e:
            self.logger.error(f"PDF download failed: {e}")
            raise DownloadFailedException(f"PDF download failed: {e}")
    
    def _setup_download_handler(self, download_path: Path):
        """
        Setup download handler to capture download events.
        
        Args:
            download_path: Path where download should be saved
            
        Returns:
            Download promise from Playwright
        """
        self.logger.info(f"Setting up download handler for: {download_path}")
        
        # Ensure download directory exists
        download_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup download handler
        async def handle_download(download):
            await download.save_as(download_path)
            self.logger.info(f"Download saved to: {download_path}")
        
        return self.browser_manager.page.wait_for_event(
            "download",
            predicate=lambda download: True
        )
    
    async def _trigger_download(self) -> None:
        """
        Trigger the PDF download by clicking the download button.
        
        Raises:
            DownloadFailedException: If download button not found or click fails
        """
        self.logger.info("Triggering PDF download")
        
        try:
            # Wait for download button to be available
            await self.browser_manager.wait_for_element(
                self.selectors.PDF_DOWNLOAD_BUTTON,
                timeout=AutomationConfig.BROWSER_TIMEOUT
            )
            
            # Click download button
            await self.browser_manager.click(self.selectors.PDF_DOWNLOAD_BUTTON)
            
            self.logger.info("Download button clicked")
            
        except TimeoutException as e:
            self.logger.error("Download button not found")
            raise DownloadFailedException("Download button not found")
    
    async def _wait_for_download(
        self,
        download_promise,
        download_path: Path,
    ) -> None:
        """
        Wait for download to complete.
        
        Args:
            download_promise: Download promise from Playwright
            download_path: Expected download path
            
        Raises:
            DownloadFailedException: If download times out
        """
        self.logger.info("Waiting for download to complete")
        
        try:
            # Wait for download event
            download = await download_promise
            
            # Wait for download to finish saving
            await download.save_as(download_path)
            
            self.logger.info("Download completed")
            
        except Exception as e:
            self.logger.error(f"Download wait failed: {e}")
            raise DownloadFailedException(f"Download wait failed: {e}")
    
    async def _verify_download(self, download_path: Path) -> None:
        """
        Verify that the downloaded PDF exists and is valid with enhanced verification.
        
        Args:
            download_path: Path to the downloaded file
            
        Raises:
            DownloadFailedException: If verification fails
        """
        self.logger.info(f"Verifying download with enhanced checks: {download_path}")
        
        try:
            # Check if file exists
            if not download_path.exists():
                raise DownloadFailedException(f"Downloaded file not found: {download_path}")
            
            # Check if file has content
            file_size = download_path.stat().st_size
            if file_size == 0:
                raise DownloadFailedException(f"Downloaded file is empty: {download_path}")
            
            # Check if it's a PDF (basic check by extension and size)
            if download_path.suffix.lower() != '.pdf':
                raise DownloadFailedException(f"Downloaded file is not a PDF: {download_path}")
            
            # PDF files should be at least a few KB
            if file_size < 1024:
                raise DownloadFailedException(f"Downloaded PDF is too small: {file_size} bytes")
            
            # Verify PDF file signature (magic number)
            try:
                with open(download_path, 'rb') as f:
                    header = f.read(4)
                    if header != b'%PDF':
                        raise DownloadFailedException(f"File does not have valid PDF signature: {download_path}")
            except Exception as e:
                self.logger.warning(f"Could not verify PDF signature: {e}")
            
            # Log verification success with details
            self.logger.info(f"Download verified successfully: {file_size} bytes")
            
            # Save download info to log
            self._save_download_info(download_path, file_size)
            
        except Exception as e:
            self.logger.error(f"Download verification failed: {e}")
            raise DownloadFailedException(f"Download verification failed: {e}")
    
    def _save_download_info(self, download_path: Path, file_size: int) -> None:
        """
        Save download information to log file.
        
        Args:
            download_path: Path to downloaded file
            file_size: Size of the file in bytes
        """
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            download_log_path = AutomationConfig.LOG_DIR / "downloads.log"
            
            with open(download_log_path, 'a') as f:
                f.write(f"{timestamp} | {download_path.name} | {file_size} bytes | Success\n")
            
            self.logger.info(f"Download info logged to: {download_log_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save download info: {e}")
    
    async def download_latest_pdf(self, base_name: str = "resume") -> Path:
        """
        Download the latest PDF with automatic versioning.
        
        This is a convenience method that handles filename generation
        and versioning automatically.
        
        Args:
            base_name: Base name for the resume (e.g., "python_backend")
            
        Returns:
            Absolute path to the downloaded PDF
        """
        self.logger.info(f"Downloading latest PDF with base name: {base_name}")
        
        sanitized_base = sanitize_filename(base_name)
        return await self.download_pdf(
            filename=None,
            save_to_versions=True,
            base_name=sanitized_base,
        )
    
    async def get_pdf_preview_url(self) -> Optional[str]:
        """
        Get the URL of the current PDF preview.
        
        Returns:
            PDF preview URL or None if not available
        """
        self.logger.info("Getting PDF preview URL")
        
        try:
            # Try to get PDF download link
            download_link = await self.browser_manager.page.query_selector(
                self.selectors.PDF_DOWNLOAD_LINK
            )
            
            if download_link:
                url = await download_link.get_attribute('href')
                self.logger.info(f"PDF preview URL: {url}")
                return url
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to get PDF preview URL: {e}")
            return None
    
    async def is_pdf_available(self) -> bool:
        """
        Check if a compiled PDF is available for download.
        
        Returns:
            True if PDF is available
        """
        self.logger.info("Checking if PDF is available")
        
        try:
            # Check for download button
            download_button = await self.browser_manager.page.query_selector(
                self.selectors.PDF_DOWNLOAD_BUTTON
            )
            
            if download_button:
                self.logger.info("PDF is available for download")
                return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Failed to check PDF availability: {e}")
            return False
