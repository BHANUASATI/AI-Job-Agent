"""
Job Description Parser Service

Handles parsing of job descriptions from multiple file formats (PDF, DOCX, TXT)
following industry-level protocols for security, validation, and error handling.
"""

import os
import re
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from pypdf import PdfReader
from docx import Document
from utils.logger import get_logger
from utils.exceptions import JDParserError

logger = get_logger(__name__)

# Security: Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt'}

# MIME type mapping for validation
MIME_TYPES = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.txt': 'text/plain'
}


class JDParser:
    """Industry-standard job description parser with security and validation."""
    
    def __init__(self):
        self.temp_dir = None
    
    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and os.path.exists(self.temp_dir):
            self._cleanup_temp_files()
    
    def _cleanup_temp_files(self):
        """Clean up temporary files securely."""
        try:
            import shutil
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
    
    def _validate_file(self, file_path: Path, original_filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file security and format.
        
        Args:
            file_path: Path to the uploaded file
            original_filename: Original filename from upload
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file extension
        file_ext = Path(original_filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return False, f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return False, f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
        
        if file_size == 0:
            return False, "File is empty"
        
        # Verify file actually exists and is readable
        if not file_path.exists():
            return False, "File not found"
        
        if not os.access(file_path, os.R_OK):
            return False, "File is not readable"
        
        return True, None
    
    def _extract_text_from_pdf(self, file_path: Path) -> str:
        """
        Extract text from PDF file with error handling.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
            
        Raises:
            JDParserError: If PDF parsing fails
        """
        try:
            reader = PdfReader(str(file_path))
            text_content = []
            
            # Security: Limit number of pages to prevent DoS
            max_pages = min(len(reader.pages), 50)
            
            for page_num in range(max_pages):
                try:
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(text)
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {e}")
                    continue
            
            full_text = "\n".join(text_content)
            
            if not full_text.strip():
                raise JDParserError("No text could be extracted from PDF")
            
            logger.info(f"Successfully extracted {len(full_text)} characters from PDF")
            return full_text
            
        except Exception as e:
            logger.error(f"PDF parsing error: {e}", exc_info=True)
            raise JDParserError(f"Failed to parse PDF file: {str(e)}")
    
    def _extract_text_from_docx(self, file_path: Path) -> str:
        """
        Extract text from DOCX file with error handling.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text content
            
        Raises:
            JDParserError: If DOCX parsing fails
        """
        try:
            doc = Document(str(file_path))
            text_content = []
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_content.append(cell.text)
            
            full_text = "\n".join(text_content)
            
            if not full_text.strip():
                raise JDParserError("No text could be extracted from DOCX")
            
            logger.info(f"Successfully extracted {len(full_text)} characters from DOCX")
            return full_text
            
        except Exception as e:
            logger.error(f"DOCX parsing error: {e}", exc_info=True)
            raise JDParserError(f"Failed to parse DOCX file: {str(e)}")
    
    def _extract_text_from_txt(self, file_path: Path) -> str:
        """
        Extract text from TXT file with encoding handling.
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            Extracted text content
            
        Raises:
            JDParserError: If TXT parsing fails
        """
        try:
            # Try multiple encodings for robustness
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        text = f.read()
                    
                    if text.strip():
                        logger.info(f"Successfully extracted {len(text)} characters from TXT (encoding: {encoding})")
                        return text
                except UnicodeDecodeError:
                    continue
            
            raise JDParserError("Could not decode text file with any supported encoding")
            
        except Exception as e:
            logger.error(f"TXT parsing error: {e}", exc_info=True)
            raise JDParserError(f"Failed to parse TXT file: {str(e)}")
    
    def parse_jd_file(self, file_content: bytes, filename: str) -> str:
        """
        Parse job description from uploaded file.
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename with extension
            
        Returns:
            Extracted job description text
            
        Raises:
            JDParserError: If parsing fails or validation errors occur
        """
        # Create temporary file for processing
        temp_file_path = None
        try:
            # Use temp directory if available, otherwise system temp
            base_dir = self.temp_dir if self.temp_dir else tempfile.gettempdir()
            temp_file_path = Path(base_dir) / f"temp_jd_{os.urandom(8).hex()}{Path(filename).suffix}"
            
            # Write content to temp file
            with open(temp_file_path, 'wb') as f:
                f.write(file_content)
            
            # Validate file
            is_valid, error_msg = self._validate_file(temp_file_path, filename)
            if not is_valid:
                raise JDParserError(error_msg)
            
            # Extract text based on file type
            file_ext = Path(filename).suffix.lower()
            
            if file_ext == '.pdf':
                text = self._extract_text_from_pdf(temp_file_path)
            elif file_ext == '.docx':
                text = self._extract_text_from_docx(temp_file_path)
            elif file_ext == '.txt':
                text = self._extract_text_from_txt(temp_file_path)
            else:
                raise JDParserError(f"Unsupported file type: {file_ext}")
            
            # Clean up the extracted text
            text = self._clean_extracted_text(text)
            
            # Validate extracted content
            if len(text) < 50:
                raise JDParserError("Extracted text is too short to be a valid job description")
            
            if len(text) > 100000:  # 100k characters limit
                raise JDParserError("Extracted text is too long. Maximum length: 100,000 characters")
            
            return text
            
        except JDParserError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing JD file: {e}", exc_info=True)
            raise JDParserError(f"Failed to parse job description file: {str(e)}")
        finally:
            # Clean up temp file
            if temp_file_path and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_file_path}: {e}")
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text with security considerations.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove control characters except common whitespace
        import re
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove common PDF artifacts
        artifacts = [
            '\x0c',  # Form feed
        ]
        for artifact in artifacts:
            text = text.replace(artifact, '')
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove multiple consecutive newlines
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')
        
        # Sanitize potential script/content injection attempts
        dangerous_patterns = [
            '<script', 'javascript:', 'onerror=', 'onload=', 
            'onclick=', 'onmouseover=', 'data:', 'vbscript:'
        ]
        
        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if pattern in text_lower:
                logger.warning(f"Removed potentially dangerous pattern: {pattern}")
                text = text.replace(pattern, '')
        
        return text.strip()


# Global instance
_jd_parser = None

def get_jd_parser() -> JDParser:
    """Get or create JD parser instance."""
    global _jd_parser
    if _jd_parser is None:
        _jd_parser = JDParser()
    return _jd_parser