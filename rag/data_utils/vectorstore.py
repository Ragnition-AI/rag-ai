from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from config import Config


class ChromaDB:
    def __init__(self):

        self.persist_dir = Config.DATASET_DB_DIR

        self.embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}
        )

        #self.client = chromadb.PersistentClient()
        #self.collection = self.client.get_or_create_collection("data01")

        self.vectordb = Chroma(
            collection_name="data01",
            persist_directory=self.persist_dir,
 			embedding_function=self.embeddings
        )

    def add_datas(self, documents: list):
        self.vectordb.add_documents(documents=documents)

    def search(self, query:str):
        result = self.vectordb.similarity_search(query, 4)
        return result

    def list_documents(self):
        results = self.vectordb.get(include=['metadatas'])
    
        unique_filenames = set()
        for metadata in results['metadatas']:
            filename = metadata.get('source') or metadata.get('filename')
            if filename:
                unique_filenames.add(filename)
        
        return list(unique_filenames)

db = ChromaDB()