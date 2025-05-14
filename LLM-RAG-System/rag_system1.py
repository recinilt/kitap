# rag_system.py
from langchain.chains import RetrievalQA
from vector_store import VectorStore
from document_processor import DocumentProcessor
from language_model import LanguageModel
from langchain.prompts import PromptTemplate

class RAGSystem:
    def __init__(self, vector_store_dir="faiss_index"):
        self.vector_store = VectorStore(persist_directory=vector_store_dir)
        self.document_processor = DocumentProcessor()
        #self.language_model = LanguageModel()
        #self.language_model = LanguageModel("mistralai/Mistral-7B-Instruct-v0.1")
        #self.language_model = LanguageModel("mistralai/Mistral-7B-v0.1")
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
            retriever = vector_store.as_retriever(search_kwargs={"k": 5})
            
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
        
        result = self.qa_chain({"query": question})
        return {
            "answer": result["result"],
            "source_documents": result["source_documents"]
        }