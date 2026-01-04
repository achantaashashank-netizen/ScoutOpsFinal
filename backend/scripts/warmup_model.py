"""
Warmup script to pre-load the embedding model on startup.
This prevents the first RAG request from being slow.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.rag.embeddings import generate_embedding

print("Warming up embedding model...")
# Generate a dummy embedding to trigger model download/loading
generate_embedding("warmup")
print("Embedding model ready!")
