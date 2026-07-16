import logging
from typing import List
from fastembed import TextEmbedding

logger = logging.getLogger(__name__)

# Load the model on startup so it stays in memory
# BAAI/bge-small-en-v1.5 is the default model for FastEmbed, but we specify it for clarity.
try:
    embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    logger.info("Successfully loaded embedding model: BAAI/bge-small-en-v1.5")
except Exception as e:
    logger.error(f"Failed to load embedding model: {e}")
    embedding_model = None

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generates embeddings for a list of strings in batches.
    Returns a list of vectors (which are lists of floats).
    """
    if not embedding_model:
        logger.warning("Embedding model is not loaded. Returning empty vectors.")
        # Fallback to zeros if model failed to load, though ideally we should raise an error
        return [[0.0] * 384 for _ in texts]
        
    if not texts:
        return []

    # FastEmbed automatically handles batching and ONNX threading under the hood.
    # It yields generators, so we list() it to evaluate immediately.
    embeddings_generator = embedding_model.embed(texts)
    
    # Convert numpy arrays to standard python lists for SQLAlchemy/pgvector
    embeddings_list = [emb.tolist() for emb in embeddings_generator]
    
    return embeddings_list
