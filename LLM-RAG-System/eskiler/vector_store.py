# vector_store.py (Güncellenen versiyon)
from langchain_community.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import os

class VectorStore:
    def __init__(self, persist_directory="chroma_db"):
        self.persist_directory = persist_directory
        
        # Alternatif gömme modeli seçenekleri
        try:
            # İlk seçenek: HuggingFace gömme modeli
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            print("HuggingFace embeddings başarıyla yüklendi.")
        except ImportError:
            try:
                # İkinci seçenek: Özel basit gömme (fallback) - İhtiyaca göre özelleştirin
                # from langchain_community.embeddings import FakeEmbeddings 
                # self.embeddings = FakeEmbeddings(size=384)  # Test amaçlı sahte gömme
                
                # Alternatif olarak, basit bir HF modeli kullanalım
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="distilbert-base-uncased",
                    model_kwargs={'device': 'cpu'}
                )
                print("Alternatif embeddings yüklendi.")
            except:
                raise ImportError("Embedding modeli yüklenemedi. Lütfen 'pip install sentence-transformers huggingface_hub==0.19.4' komutunu çalıştırın.")
        
        self.vector_store = None

    def create_vector_store(self, documents):
        """Belgelerden Chroma vektör veritabanı oluşturur"""
        self.vector_store = Chroma.from_documents(
            documents, 
            self.embeddings,
            persist_directory=self.persist_directory
        )
        self.vector_store.persist()  # Değişiklikleri diske kaydet
        return self.vector_store
        
    def load_vector_store(self):
        """Mevcut Chroma veritabanını yükler"""
        if os.path.exists(self.persist_directory):
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            return self.vector_store
        else:
            raise FileNotFoundError(f"{self.persist_directory} bulunamadı")
    
    def similarity_search(self, query, k=5):
        """Sorguya benzer dokümanları bulur"""
        if not self.vector_store:
            self.load_vector_store()
        return self.vector_store.similarity_search(query, k=k)