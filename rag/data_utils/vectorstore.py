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
        result = self.vectordb.similarity_search(query, 3)
        return result

db = ChromaDB()