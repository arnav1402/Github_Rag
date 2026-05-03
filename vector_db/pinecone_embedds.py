# Backward compatibility wrapper - use embeddings.py and query.py instead
from .embeddings import (
    embed_texts,
    embed_and_store,
    clear_by_namespace,
    get_namespace,
    get_or_create_index,
    EMBED_MODEL,
    DIMENSION,
    BATCH_SIZE,
    pc,
    PINECONE_INDEX
)
from .query import ask

__all__ = [
    "embed_texts",
    "embed_and_store",
    "clear_by_namespace",
    "get_namespace",
    "get_or_create_index",
    "ask",
    "EMBED_MODEL",
    "DIMENSION",
    "BATCH_SIZE",
    "pc",
    "PINECONE_INDEX"
]
