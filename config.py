"""App configuration and constants."""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Default OpenAI API key (override with OPENAI_API_KEY in .env for production)
DEFAULT_OPENAI_API_KEY = os.environ.get(
    "OPENAI_API_KEY",
    "",
)

# Embedding model for clustering
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
