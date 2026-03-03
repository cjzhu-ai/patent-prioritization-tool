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
    "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",
)

# Embedding model for clustering
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
