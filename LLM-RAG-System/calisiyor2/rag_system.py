# rag_system.py
from langchain.chains import RetrievalQA
from vector_store import VectorStore
from document_processor import DocumentProcessor
from language_model import LanguageModel
from langchain.prompts import PromptTemplate
import torch

class RAGSystem:
    def __init__(self, vector_store_dir="faiss_index"):
        self.vector_store = VectorStore(persist_directory=vector_store_dir)
        self.document_processor = DocumentProcessor(chunk_size=384, chunk_overlap=50)
        
        # GPU belleğinize göre en uygun modeli seçin
        if torch.cuda.is_available() and torch.cuda.get_device_properties(0).total_memory > 8 * 1024 * 1024 * 1024:
            # 8GB+ GPU için daha güçlü model
            self.language_model = LanguageModel("tiiuae/falcon-7b-instruct")
        else:
            # Daha az bellek için daha küçük model
            self.language_model = LanguageModel("tiiuae/falcon-7b-instruct")

        self.llm = None
        self.qa_chain = None
    
    def initialize(self):
        """Sistem bileşenlerini başlatır"""
        self.llm = self.language_model.load_quantized_model()
        try:
            vector_store = self.vector_store.load_vector_store()
        except FileNotFoundError:
            print("Vektör veritabanı bulunamadı. Önce dokümanları işleyin.")
            vector_store = None
        
        if vector_store:
            # Daha fazla benzer doküman getir (5 yerine 7)
            retriever = vector_store.as_retriever(search_kwargs={"k": 7})
            
            # Edebi ton için özel prompt tanımlama
            template = """Görevin, verilen metinleri edebi bir dile dönüştürmek, kitapları özetlemek veya video transkriptlerini kitaplaştırmaktır.
            
            Edebi stil kullan, tutarlı bir anlatım tonu sağla ve bütünlüklü bir metin oluştur.
            
            Bağlam:
            {context}
            
            Soru:
            {question}
            
            Lütfen detaylı, tutarlı, bütünlüklü ve edebi bir yanıt ver:"""
            
            PROMPT = PromptTemplate(
                template=template,
                input_variables=["context", "question"]
            )
            
            # QA zinciri oluştur
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT}
            )
        
        return self
    
    def process_documents(self, directory_path):
        """Dizinden dokümanları işler ve vektör veritabanı oluşturur"""
        documents = self.document_processor.load_and_split_directory(directory_path)
        vector_store = self.vector_store.create_vector_store(documents)
        return len(documents)
    
    def process_single_document(self, file_path):
        """Tek bir dokümanı işler ve vektör veritabanına ekler"""
        documents = self.document_processor.load_and_split_documents(file_path)
        vector_store = self.vector_store.create_vector_store(documents)
        return len(documents)
    
    def query(self, question):
        """Sisteme sorgu yapar"""
        if not self.qa_chain:
            raise ValueError("Sistem henüz başlatılmadı. Önce initialize() metodunu çağırın.")
        
        # Sorguyu parçalara böl ve işle (çok uzunsa)
        if len(question) > 4000:
            print("[INFO] Sorgu çok uzun, parçalara bölünüyor...")
            chunks = [question[i:i+4000] for i in range(0, len(question), 4000)]
            results = []
            
            for i, chunk in enumerate(chunks):
                print(f"[INFO] Sorgu parçası {i+1}/{len(chunks)} işleniyor...")
                part_result = self.qa_chain({"query": chunk})
                results.append(part_result["result"])
            
            # Sonuçları birleştir
            combined_result = "\n\n".join(results)
            
            # Kaynak belgelerini ilk parçadan al (basitlik için)
            source_documents = self.qa_chain({"query": chunks[0]})["source_documents"]
            
            return {
                "answer": combined_result,
                "source_documents": source_documents
            }
        else:
            # Normal sorgu işleme
            result = self.qa_chain({"query": question})
            return {
                "answer": result["result"],
                "source_documents": result["source_documents"]
            }