"""
Resume loader module.

Loads PDF resumes from configured directory.
"""

from langchain_community.document_loaders import PyPDFLoader
from config.settings import Config
from utils.logger import get_logger
from utils.exceptions import ResumeLoadError

logger = get_logger(__name__)


def load_resumes():
    """
    Load all PDF resumes from configured directory.
    
    Returns:
        List of loaded document objects
        
    Raises:
        ResumeLoadError: If resume loading fails
    """
    documents = []
    
    try:
        # Ensure directory exists
        Config.RESUME_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Loading resumes from {Config.RESUME_DIR}")

        resume_files = list(Config.RESUME_DIR.glob("*.pdf"))
        
        if not resume_files:
            logger.warning(f"No PDF files found in {Config.RESUME_DIR}")
            return documents
        
        for file in resume_files:
            try:
                logger.debug(f"Loading resume: {file.name}")
                loader = PyPDFLoader(str(file))
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"Successfully loaded {file.name}")
            except Exception as e:
                logger.error(f"Failed to load resume {file.name}: {e}")
                # Continue with other files instead of failing completely
        
        logger.info(f"Loaded {len(documents)} document chunks from {len(resume_files)} resumes")
        return documents
        
    except Exception as e:
        logger.error(f"Error loading resumes: {e}", exc_info=True)
        raise ResumeLoadError(f"Failed to load resumes: {e}")