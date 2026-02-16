# RAG (Retrieval-Augmented Generation) Agent

Retrieval-Augmented Generation (RAG) agent using Python, designed to enhance language model responses by retrieving and incorporating relevant contextual information from a dataset.

## Prerequisites
- Python 3.12 or higher
- Virtual environment recommended

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/vinayak-7-0-3/rag-ai
cd rag-ai
```

### 2. Create Virtual Environment
```bash
virtualenv -p python3 VENV
. ./VENV/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Variables
Create a `.env` file in the project root directory with the following variables:

```
# Dataset Configurations
DATASET_DIR=path/to/your/dataset
DATASET_DB_DIR=path/to/your/dataset/database

# Embedding Model Configuration
EMBEDDING_MODEL=your-embedding-model
EMBEDDING_TOKENS=your-embedding-tokens

# LLM and API Configurations
OLLAMA_MODEL_ID=your-ollama-model
TOGETHER_API_KEY=your-together-api-key
GOOGLE_API_KEY=your-google-api-key
TAVILY_API_KEY=your-tavily-api-key

# Additional Configurations
TOKENIZERS_PARALLELISM=true
DATABASE_URL=your-postgres-database-connection-string
```

### 5. Running the Project
```bash
python -m rag
```

## Key Components
- Retrieval mechanism using specified embedding models
- Integration with various LLM providers (Ollama, Together AI, Gemini)
- Support for websearch (Tavily)
- Ranking the generation and check for halucinations.
- Flexible dataset and database configuration

## Environment Variable Details
- `DATASET_DIR`: Path to the source dataset
- `DATASET_DB_DIR`: Path for storing processed dataset database
- `EMBEDDING_MODEL`: Specified embedding model for text vectorization
- `EMBEDDING_TOKENS`: Tokenization parameters for embeddings
- `OLLAMA_MODEL_ID`: Specific Ollama language model
- `TOGETHER_API_KEY`: API key for Together AI services
- `GOOGLE_API_KEY`: Google API authentication
- `TAVILY_API_KEY`: Tavily API key for additional retrieval
- `TOKENIZERS_PARALLELISM`: Enable/disable parallel tokenization
- `DATABASE_URL`: Connection string for database operations

## References
- Langchain Adaptive RAG - [Link](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag_local)
- Docling Hybrid Chunking - [Link](https://docling-project.github.io/docling/examples/hybrid_chunking/)
