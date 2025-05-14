# simplified_rag_system.py
# Basitleştirilmiş RAG sistemi, embeddings olmadan çalışır
from langchain.chains import LLMChain
from language_model import LanguageModel
from langchain.prompts import PromptTemplate
import os
import json

class SimplifiedRAGSystem:
    def __init__(self):
        self.language_model = LanguageModel()
        self.llm = None
        self.chain = None
        self.documents = {}  # Dokümanları basit bir sözlükte saklayacağız
        self.doc_index = {}  # Basit kelime-dokuman indeksi
    
    def initialize(self):
        """Sistem bileşenlerini başlatır"""
        self.llm = self.language_model.load_quantized_model()
        
        # Edebi ton için özel prompt tanımlama
        template = """Görevin, verilen metinleri edebi bir dile dönüştürmek, kitapları özetlemek veya video transkriptlerini kitaplaştırmaktır.
        
        Edebi stil kullan, tutarlı bir anlatım tonu sağla ve bütünlüklü bir metin oluştur.
        
        Aşağıdaki bilgiler konuyla ilgili referans olarak verilmiştir:
        {context}
        
        Sorgu:
        {query}
        
        Lütfen detaylı, tutarlı, bütünlüklü ve edebi bir yanıt ver:"""
        
        PROMPT = PromptTemplate(
            template=template,
            input_variables=["context", "query"]
        )
        
        # LLM zinciri oluştur
        self.chain = LLMChain(
            llm=self.llm,
            prompt=PROMPT
        )
        
        # Kaydedilmiş dokümanları varsa yükle
        self._load_documents()
        
        return self
    
    def _load_documents(self):
        """Kaydedilmiş dokümanları yükler"""
        if os.path.exists("documents.json"):
            try:
                with open("documents.json", "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
                
                # İndeks oluştur
                self._build_index()
                print(f"{len(self.documents)} doküman yüklendi.")
            except:
                print("Dokümanlar yüklenemedi.")
                self.documents = {}
    
    def _save_documents(self):
        """Dokümanları kaydeder"""
        with open("documents.json", "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
    
    def _build_index(self):
        """Basit bir kelime indeksi oluşturur"""
        self.doc_index = {}
        for doc_id, doc in self.documents.items():
            words = doc["content"].lower().split()
            for word in set(words):  # Her kelimeyi bir kez işle
                if word not in self.doc_index:
                    self.doc_index[word] = []
                if doc_id not in self.doc_index[word]:
                    self.doc_index[word].append(doc_id)
    
    def process_single_document(self, file_path):
        """Tek bir dokümanı işler ve sözlüğe ekler"""
        if not os.path.exists(file_path):
            return 0
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Dosyayı dokümanlar sözlüğüne ekle
            doc_id = os.path.basename(file_path)
            self.documents[doc_id] = {
                "source": file_path,
                "content": content
            }
            
            # İndeksi güncelle
            words = content.lower().split()
            for word in set(words):
                if word not in self.doc_index:
                    self.doc_index[word] = []
                if doc_id not in self.doc_index[word]:
                    self.doc_index[word].append(doc_id)
            
            # Dokümanları kaydet
            self._save_documents()
            
            return 1  # 1 doküman işlendi
        except Exception as e:
            print(f"Doküman işleme hatası: {e}")
            return 0
    
    def process_documents(self, directory_path):
        """Bir dizindeki tüm .txt dosyalarını işler"""
        if not os.path.isdir(directory_path):
            return 0
        
        count = 0
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.txt'):
                    file_path = os.path.join(root, file)
                    count += self.process_single_document(file_path)
        
        return count
    
    def _simple_search(self, query, k=5):
        """Sorgu terimlerine göre basit bir arama yapar"""
        query_words = query.lower().split()
        doc_scores = {}
        
        for word in query_words:
            if word in self.doc_index:
                for doc_id in self.doc_index[word]:
                    if doc_id not in doc_scores:
                        doc_scores[doc_id] = 0
                    doc_scores[doc_id] += 1
        
        # Sonuçları skora göre sırala
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        # En yüksek skorlu k dokümanı döndür
        result_docs = []
        for doc_id, score in sorted_docs[:k]:
            if doc_id in self.documents:
                doc = self.documents[doc_id]
                result_docs.append({
                    "source": doc["source"],
                    "content": doc["content"],
                    "score": score
                })
        
        return result_docs
    
    def query(self, question):
        """Sisteme sorgu yapar"""
        if not self.chain:
            raise ValueError("Sistem henüz başlatılmadı. Önce initialize() metodunu çağırın.")
        
        # Basit arama yap
        results = self._simple_search(question)
        
        # Eğer sonuç bulunamazsa genel bir yanıt ver
        if not results:
            context = "Üzgünüm, bu konuyla ilgili elimde yeterli bilgi yok. Genel bilgilerime dayanarak bir yanıt vermeye çalışacağım."
        else:
            # En iyi sonuçları birleştir (en fazla 1000 karakter)
            context = "\n\n".join([f"Kaynak ({doc['source']}): {doc['content'][:1000]}" for doc in results])
        
        # LLM'e gönder
        result = self.chain.run(context=context, query=question)
        
        # Sonuçları formatlayarak döndür
        source_documents = []
        for doc in results:
            source_documents.append({
                "page_content": doc["content"][:200] + "...",
                "metadata": {"source": doc["source"]}
            })
        
        return {
            "answer": result,
            "source_documents": source_documents
        }