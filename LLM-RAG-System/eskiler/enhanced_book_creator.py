# enhanced_book_creator.py
import os
import re
import time
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from tqdm import tqdm

class EnhancedBookCreator:
    def __init__(self, rag_system):
        """
        Gelişmiş kitap oluşturma sistemi
        
        Args:
            rag_system: Mevcut RAG sistemi
        """
        self.rag_system = rag_system
        self.chapter_outlines = {}
        self.chapter_contents = {}
        self.book_metadata = {}
    
    def analyze_content(self, content_summary, series_name, num_episodes):
        """
        Kitap içeriğini analiz eder ve bir yapı oluşturur
        
        Args:
            content_summary: İçerik özeti
            series_name: Seri adı
            num_episodes: Bölüm sayısı
            
        Returns:
            Kitap yapısı metadatası
        """
        print("İçerik analiz ediliyor...")
        
        # İçerik analizi için özel prompt
        analysis_prompt = f"""
        '{series_name}' başlıklı {num_episodes} bölümlük içeriği analiz et ve kapsamlı bir kitap yapısı oluştur.
        
        İÇERİK ÖZETI: {content_summary[:2000]}
        
        Aşağıdaki bilgileri JSON formatında döndür:
        1. book_title: İçeriğe uygun çarpıcı bir kitap başlığı
        2. book_subtitle: Alt başlık
        3. estimated_page_count: Tahmini sayfa sayısı (içerik uzunluğuna göre)
        4. chapters: Ana bölümlerin listesi, her biri için:
           - title: Bölüm başlığı
           - importance_level: 1-5 arası (5 en önemli)
           - estimated_pages: Tahmini sayfa sayısı (konunun kapsamına göre)
           - subchapters: Alt bölümlerin listesi, her biri için:
             - title: Alt bölüm başlığı
             - key_concepts: Bu alt bölümde yer alması gereken anahtar kavramlar
             
        Yanıtı düz JSON formatında ver, başka açıklama ekleme.
        """
        
        result = self.rag_system.query(analysis_prompt)
        
        # JSON'u metinden çıkarma
        try:
            json_text = re.search(r'(\{.*\})', result["answer"], re.DOTALL).group(1)
            book_structure = json.loads(json_text)
        except:
            # Alternatif çözüm - saf JSON olmayabilir
            try:
                # RAW formatı şu şekilde temizle
                clean_text = result["answer"].replace("```json", "").replace("```", "").strip()
                book_structure = json.loads(clean_text)
            except:
                # Son çare - manuel format
                book_structure = {
                    "book_title": f"{series_name}",
                    "book_subtitle": "Kapsamlı Bir İnceleme",
                    "estimated_page_count": max(num_episodes * 30, 100),
                    "chapters": self._generate_default_chapters(num_episodes)
                }
        
        self.book_metadata = book_structure
        return book_structure
    
    def _generate_default_chapters(self, num_episodes, min_chapters=3, max_chapters=7):
        """Varsayılan bölüm yapısı oluşturur"""
        chapter_count = min(max(min_chapters, num_episodes), max_chapters)
        chapters = []
        
        for i in range(chapter_count):
            chapters.append({
                "title": f"Bölüm {i+1}",
                "importance_level": 3,
                "estimated_pages": 15,
                "subchapters": [
                    {
                        "title": f"Alt Bölüm {i+1}.1",
                        "key_concepts": ["Kavram 1", "Kavram 2"]
                    },
                    {
                        "title": f"Alt Bölüm {i+1}.2",
                        "key_concepts": ["Kavram 3", "Kavram 4"]
                    }
                ]
            })
        
        return chapters
    
    def generate_chapter_outlines(self):
        """Her bölüm için detaylı taslak oluşturur"""
        print("Bölüm taslakları oluşturuluyor...")
        
        if not self.book_metadata or not self.book_metadata.get("chapters"):
            raise ValueError("Önce içerik analizi yapılmalıdır")
        
        for idx, chapter in enumerate(tqdm(self.book_metadata["chapters"])):
            # Bölüm taslağı için özel prompt
            outline_prompt = f"""
            '{self.book_metadata["book_title"]}' kitabının '{chapter["title"]}' bölümü için detaylı bir taslak oluştur.
            
            BÖLÜM ÖNEMİ: {chapter["importance_level"]}/5
            TAHMİNİ SAYFA SAYISI: {chapter["estimated_pages"]}
            
            Bu bölüm şu alt bölümleri içermeli:
            {", ".join([subchapter["title"] for subchapter in chapter["subchapters"]])}
            
            Her alt bölümde şu anahtar kavramlar yer almalı:
            {json.dumps([{subchapter["title"]: subchapter["key_concepts"]} for subchapter in chapter["subchapters"]], ensure_ascii=False, indent=2)}
            
            Bölüm taslağını markdown formatında döndür. Sadece taslak oluştur, içerik yazma.
            Taslak, her alt bölüm için 3-5 madde içermeli.
            """
            
            result = self.rag_system.query(outline_prompt)
            self.chapter_outlines[chapter["title"]] = result["answer"]
        
        return self.chapter_outlines
    
    def generate_chapter_contents(self):
        """Her bölüm için içerik oluşturur"""
        print("Bölüm içerikleri oluşturuluyor...")
        
        if not self.chapter_outlines:
            raise ValueError("Önce bölüm taslakları oluşturulmalıdır")
        
        for idx, chapter in enumerate(tqdm(self.book_metadata["chapters"])):
            # Bölüm içeriği için özel prompt
            content_prompt = f"""
            '{self.book_metadata["book_title"]}' kitabının '{chapter["title"]}' bölümü için kapsamlı içerik oluştur.
            
            BÖLÜM TASLAĞI:
            {self.chapter_outlines[chapter["title"]]}
            
            Aşağıdaki kurallara uygun şekilde içerik oluştur:
            1. İçerik tamamen TÜRKÇE olmalı
            2. Akademik, edebi ve tutarlı bir dil kullan
            3. Taslaktaki tüm maddeleri kapsamlı şekilde açıkla
            4. Her alt bölüm için yeterli açıklama ve detay sağla
            5. İçeriğin kapsamı yaklaşık {chapter["estimated_pages"]} sayfa olmalı
            6. Tekrarlardan kaçın, net ve anlaşılır ifadeler kullan
            7. Örnekler ve açıklamalarla metni zenginleştir
            
            İçeriği markdown formatında döndür, alt bölüm başlıklarını ## ile, alt-alt bölümleri ### ile işaretle.
            """
            
            result = self.rag_system.query(content_prompt)
            self.chapter_contents[chapter["title"]] = result["answer"]
        
        return self.chapter_contents
    
    def generate_front_matter(self):
        """Kitap ön kısmını (kapak, içindekiler, önsöz) oluşturur"""
        print("Kitap ön kısmı oluşturuluyor...")
        
        front_matter_prompt = f"""
        '{self.book_metadata["book_title"]}' kitabının ön kısmını oluştur.
        
        Kitap bilgileri:
        - Başlık: {self.book_metadata["book_title"]}
        - Alt başlık: {self.book_metadata.get("book_subtitle", "")}
        - Tahmini sayfa sayısı: {self.book_metadata.get("estimated_page_count", 100)}
        
        Bölümler:
        {json.dumps([{
            "bölüm": chapter["title"], 
            "alt_bölümler": [subchapter["title"] for subchapter in chapter["subchapters"]]
        } for chapter in self.book_metadata["chapters"]], ensure_ascii=False, indent=2)}
        
        Şunları sırasıyla oluştur:
        1. Kapak sayfası (başlık ve alt başlık)
        2. İçindekiler (tüm bölüm ve alt bölümlerin sayfa numaraları ile)
        3. Önsöz (kitabın amacı, kapsamı ve yaklaşımını açıklayan)
        
        Hepsini markdown formatında, TÜRKÇE olarak oluştur. İçindekiler kısmında tüm bölüm ve alt bölümler görünmeli.
        """
        
        result = self.rag_system.query(front_matter_prompt)
        return result["answer"]
    
    def generate_back_matter(self):
        """Kitap arka kısmını (sonuç, kavram dizini) oluşturur"""
        print("Kitap arka kısmı oluşturuluyor...")
        
        # Tüm içeriği birleştir
        all_content = " ".join([content for content in self.chapter_contents.values()])
        
        # İçerikten anahtar kavramları çıkar
        key_concepts_prompt = f"""
        Aşağıdaki içerikten en önemli 20-30 anahtar kavramı çıkar:
        
        {all_content[:5000]}
        
        Yanıtı "Kavram: Tanım" formatında, alfabetik sırayla döndür.
        """
        
        concepts_result = self.rag_system.query(key_concepts_prompt)
        
        # Sonuç bölümü oluştur
        conclusion_prompt = f"""
        '{self.book_metadata["book_title"]}' kitabı için kapsamlı bir sonuç bölümü oluştur.
        
        Kitaptaki bölümler:
        {", ".join([chapter["title"] for chapter in self.book_metadata["chapters"]])}
        
        Sonuç bölümü şunları içermeli:
        1. Kitabın ana argümanlarının özeti
        2. Temel çıkarımlar ve değerlendirmeler
        3. Konu üzerine genel bir perspektif
        
        Markdown formatında, TÜRKÇE olarak oluştur.
        """
        
        conclusion_result = self.rag_system.query(conclusion_prompt)
        
        # Birleştir
        back_matter = f"""
        # Sonuç ve Değerlendirme
        
        {conclusion_result["answer"]}
        
        # Kavram Dizini
        
        {concepts_result["answer"]}
        """
        
        return back_matter
    
    def compile_book(self):
        """Tüm kitap bölümlerini birleştirir"""
        print("Kitap derleniyor...")
        
        if not self.chapter_contents:
            raise ValueError("Önce bölüm içerikleri oluşturulmalıdır")
        
        front_matter = self.generate_front_matter()
        back_matter = self.generate_back_matter()
        
        full_book = front_matter + "\n\n"
        
        # Ana bölümleri ekle
        for chapter in self.book_metadata["chapters"]:
            if chapter["title"] in self.chapter_contents:
                full_book += f"\n\n# {chapter['title']}\n\n"
                full_book += self.chapter_contents[chapter["title"]]
        
        full_book += "\n\n" + back_matter
        
        # Tutarlılık kontrolü
        full_book = self._ensure_consistency(full_book)
        
        return full_book
    
    def _ensure_consistency(self, text):
        """Metin tutarlılığını sağlar"""
        # İngilizce başlıkları Türkçe'ye çevir
        replacements = {
            "Introduction:": "Giriş:",
            "Introduction": "Giriş",
            "Title:": "Başlık:",
            "Subtitle:": "Alt Başlık:",
            "Author:": "Yazar:",
            "Publisher:": "Yayıncı:",
            "ISBN:": "ISBN:",
            "Cover Image:": "Kapak Resmi:",
            "Section": "Bölüm",
            "Example": "Örnek",
            "Conclusion:": "Sonuç:",
            "Conclusion": "Sonuç",
            "Chapter": "Bölüm",
            "Table of Contents": "İçindekiler",
            "Preface": "Önsöz",
            "Index": "Dizin"
        }
        
        for eng, tr in replacements.items():
            text = text.replace(eng, tr)
        
        # Tekrarlanan başlıkları temizle
        lines = text.split("\n")
        cleaned_lines = []
        prev_line = ""
        
        for line in lines:
            if line.strip() and line.strip() != prev_line.strip():
                cleaned_lines.append(line)
            prev_line = line
        
        return "\n".join(cleaned_lines)
    
    def create_book(self, content_summary, series_name, num_episodes, output_file=None):
        """Tam kitap oluşturma süreci"""
        start_time = time.time()
        
        # Adım 1: İçerik analizi
        self.analyze_content(content_summary, series_name, num_episodes)
        
        # Adım 2: Bölüm taslakları
        self.generate_chapter_outlines()
        
        # Adım 3: Bölüm içerikleri
        self.generate_chapter_contents()
        
        # Adım 4: Kitabı derle
        full_book = self.compile_book()
        
        # Adım 5: Dosyaya kaydet
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(full_book)
            print(f"Kitap '{output_file}' dosyasına kaydedildi.")
        
        elapsed_time = time.time() - start_time
        print(f"Kitap oluşturma tamamlandı. ({elapsed_time:.2f} saniye)")
        
        return full_book


# Eklenmesi gereken fonksiyonlar - app.py'ye entegre edilmelidir
def create_enhanced_book(rag_system, content_summary, series_name, num_episodes, output_file=None):
    """Gelişmiş kitap oluşturma fonksiyonu"""
    creator = EnhancedBookCreator(rag_system)
    return creator.create_book(content_summary, series_name, num_episodes, output_file)