import os
import logging
from os import getenv
from dotenv import load_dotenv

if not os.environ.get("ENV"):
    load_dotenv('.env', override=True)

class Config(object):
    DATASET_DIR = getenv("DATASET_DIR")
    DATASET_DB_DIR = getenv('DATASET_DB_DIR')
    
    EMBEDDING_MODEL = getenv('EMBEDDING_MODEL', 'BAAI/bge-m3')
    EMBEDDING_TOKENS = int(getenv('EMBEDDING_TOKENS', 8192))

    OLLAMA_MODEL_ID = getenv('OLLAMA_MODEL_ID', 'qwen2.5:14b-instruct-q4_K_M')
    TOGETHER_API_KEY = getenv('TOGETHER_API_KEY')
    GOOGLE_API_KEY = getenv('GOOGLE_API_KEY')
    TAVILY_API_KEY = getenv('TAVILY_API_KEY')

    TOKENIZERS_PARALLELISM = getenv('TOKENIZERS_PARALLELISM', 'true')