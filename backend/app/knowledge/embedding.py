"""Embedding function provider for ChromaDB knowledge retrieval.

Configures ChromaDB's embedding function with single-thread CPU constraints
to prevent memory explosion on 512MB RAM cloud instances.
"""

from __future__ import annotations

import os

# Limit internal math/thread pool allocation to prevent memory spikes
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import chromadb
import chromadb.utils.embedding_functions as ef

_EMBEDDING_FUNCTION = None


def get_embedding_function() -> chromadb.EmbeddingFunction:
    """Return the singleton embedding function."""
    global _EMBEDDING_FUNCTION
    if _EMBEDDING_FUNCTION is None:
        _EMBEDDING_FUNCTION = ef.DefaultEmbeddingFunction()
    return _EMBEDDING_FUNCTION
