# app/embedder.py

# This module exists so the ~90MB SentenceTransformer model is loaded into
# memory exactly once and shared across the app, instead of each of
# ingest.py and retrieve.py loading their own separate copy.
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
