"""
Resume splitter module.

Splits documents into chunks using configured parameters.
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter
from config.settings import Config


def split_documents(documents):
    """Split documents into chunks using configured parameters."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP
    )

    chunks = splitter.split_documents(documents)

    return chunks