"""
Vector store module.

Creates and manages FAISS vector database using configured settings.
"""

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import Config
from utils.logger import get_logger
from utils.exceptions import VectorStoreError

logger = get_logger(__name__)


def create_vector_store(chunks):
    """
    Create or load FAISS vector store with configured settings.
    
    Args:
        chunks: List of document chunks to index
        
    Returns:
        FAISS vector store instance
        
    Raises:
        VectorStoreError: If vector store operations fail
    """
    try:
        logger.info("Creating/loading vector store")
        
        embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            model_kwargs={'device': Config.EMBEDDING_DEVICE}
        )

        # Ensure directory exists
        persist_directory = Config.VECTOR_DB_DIR
        persist_directory.mkdir(parents=True, exist_ok=True)

        # Check if existing vector store exists
        index_path = persist_directory / "index"
        
        if index_path.exists():
            logger.info(f"Loading existing vector store from {persist_directory}")
            # Load existing vector store
            vector_store = FAISS.load_local(
                str(persist_directory), 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            # Add new chunks if provided
            if chunks:
                logger.info(f"Adding {len(chunks)} new chunks to vector store")
                vector_store.add_documents(chunks)
        else:
            logger.info(f"Creating new vector store with {len(chunks)} chunks")
            # Create new vector store
            vector_store = FAISS.from_documents(chunks, embeddings)
        
        # Save to disk
        vector_store.save_local(str(persist_directory))
        logger.info("Vector store saved successfully")
        
        return vector_store
        
    except Exception as e:
        logger.error(f"Error creating vector store: {e}", exc_info=True)
        raise VectorStoreError(f"Failed to create vector store: {e}")