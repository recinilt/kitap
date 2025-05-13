# vector_store.py
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os

class VectorStore:
    def __init__(self, persist_directory="faiss_index"):
        self.persist_directory = persist_directory
        # Daha kompakt, GPU uyumlu embedding modeli
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.vector_store = None

    def create_vector_store(self, documents):
        """Belgelerden FAISS vektör veritabanı oluşturur"""
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        self.vector_store.save_local(self.persist_directory)
        return self.vector_store
        
    def load_vector_store(self):
        """Mevcut FAISS veritabanını yükler"""
        if os.path.exists(self.persist_directory):
            self.vector_store = FAISS.load_local(self.persist_directory, self.embeddings)
            return self.vector_store
        else:
            raise FileNotFoundError(f"{self.persist_directory} bulunamadı")
    
    def similarity_search(self, query, k=5):
        """Sorguya benzer dokümanları bulur"""
        if not self.vector_store:
            self.load_vector_store()
        return self.vector_store.similarity_search(query, k=k)