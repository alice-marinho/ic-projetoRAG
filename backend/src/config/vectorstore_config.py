import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
load_dotenv()

EMBEDDING_SENTENCE_MODEL= "sentence-transformers/multi-qa-mpnet-base-dot-v1"
EMBEDDING_GEMINI_MODEL= "sentence-transformers/multi-qa-mpnet-base-dot-v1"

# EMBEDDING_SENTENCE_MODEL = SentenceTransformer("sentence-transformers/multi-qa-mpnet-base-dot-v1")

EMBEDDING_PROVIDER = ""