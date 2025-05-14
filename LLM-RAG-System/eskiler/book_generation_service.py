# book_generation_service.py
import os
import time
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from enhanced_book_creator import EnhancedBookCreator
from content_processor import ContentProcessor

class BookGenerationService:
    """Kitap oluşturma sürecini yöneten ve koordine eden servis sınıfı"""
    
    def __init__(self, rag_system):
        """
        Kitap oluşturma servisini başlatır
        
        Args:
            rag_system: RAG sistemi referansı
        """
        self.rag_system = rag_system
        self.content_processor = ContentProcessor()
        self.book_creator = EnhancedBookCreator(rag_system)
        self.temp_files = []
    
    def _cleanup(self):
        """Geçici dosyaları temizler"""
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
        self.temp_files = []
    
    def preprocess_content(self, content):
        """İçeriği ön işlemden geçirir"""
        return self.content_processor.preprocess_transcript(content)
    
    def detect_content_size(self, content):
        """İçerik boyutunu ve karmaşıklığını değerlendirir"""
        stats = self.content_processor.calculate_readability(content)
        quality = self.content_processor.assess_content_quality(content)
        
        word_count = stats["word_count"]
        
        if word_count < 1000:
            size = "small"  # Küçük
        elif word_count < 5000:
            size = "medium"  # Orta
        elif word_count < 20000:
            size = "large"  # Büyük
        else:
            size = "very_large"  # Çok Büyük
        
        complexity = "medium"  # Varsayılan karmaşıklık
        
        # Karmaşıklığı kelime çeşitliliği ve okunabilirliğe göre belirle
        if quality["unique_word_ratio"] > 0.7 and stats["avg_words_per_sentence"] > 15:
            complexity = "high"  # Yüksek karmaşıklık
        elif quality["unique_word_ratio"] < 0.5 and stats["avg_words_per_sentence"] < 10:
            complexity = "low"  # Düşük karmaşıklık
        
        return {
            "size": size,
            "complexity": complexity,
            "stats": stats,
            "quality": quality
        }
    
    def split_large_content(self, content):
        """Büyük içeriği bölümlere ayırır"""
        # İçerik değerlendirmesi
        assessment = self.detect_content_size(content)
        
        # Küçük ve orta boy içerikler için bölme gerekmez
        if assessment["size"] in ["small", "medium"]:
            return [content]
        
        # Paragrafları böl
        paragraphs = re.split(r'\n\s*\n', content)
        
        # Her bölüm için hedef kelime sayısı
        if assessment["size"] == "large":
            target_words = 4000  # Büyük içerik için hedef (yaklaşık 16 sayfa)
        else:  # very_large
            target_words = 8000  # Çok büyük içerik için hedef (yaklaşık 32 sayfa)
        
        # Bölümleri oluştur
        parts = []
        current_part = []
        current_word_count = 0
        
        for paragraph in paragraphs:
            paragraph_word_count = len(paragraph.split())
            
            # Eğer eklersek hedefi aşacak mı?
            if current_word_count + paragraph_word_count > target_words and current_part:
                # Mevcut bölümü kaydet ve yeni bölüm başlat
                parts.append("\n\n".join(current_part))
                current_part = [paragraph]
                current_word_count = paragraph_word_count
            else:
                # Mevcut bölüme ekle
                current_part.append(paragraph)
                current_word_count += paragraph_word_count
        
        # Son bölümü ekle
        if current_part:
            parts.append("\n\n".join(current_part))
        
        return parts
    
    def generate_book_structure(self, content_summary, series_name, num_episodes):
        """İçerik analizine dayalı kitap yapısı oluşturur"""
        # İçeriği işle ve yapı çıkar
        processed_content = self.preprocess_content(content_summary)
        return self.content_processor.generate_structure_from_content(
            processed_content, 
            min_chapters=max(3, min(7, num_episodes))
        )
    
    def _process_chunk(self, chunk_idx, chunk, series_name, num_episodes, total_chunks):
        """Her bir içerik parçasını asenkron işler"""
        chunk_title = f"{series_name} - Bölüm {chunk_idx+1}/{total_chunks}"
        
        # Her parça için özel prompt
        chunk_prompt = f"""
        '{series_name}' başlıklı çalışmanın {chunk_idx+1}. bölümünü edebi bir dille kitaplaştır.
        
        İÇERİK BÖLÜMÜ: {chunk_idx+1}/{total_chunks}
        
        ÖNEMLİ KURALLAR:
        1. İçerik tamamen TÜRKÇE olmalı
        2. Akademik, edebi ve tutarlı bir dil kullan
        3. Tekrarlardan kaçın, net ve anlaşılır ifadeler kullan
        4. Bu bölüm için mantıklı bir yapı oluştur, bu kitabın {chunk_idx+1}. bölümü olduğunu unutma
        5. Tekrarlanan ifadeleri tekrar etme, konuyu akıcı bir şekilde anlat
        6. Konuşma dilinden yazı diline uygun şekilde dönüştür
        7. Bölüm başında "Bölüm {chunk_idx+1}" ifadesini ekle
        
        İÇERİK:
        {chunk}
        """
        
        # RAG sorgusu yap
        result = self.rag_system.query(chunk_prompt)
        return result["answer"]
    
    def process_large_content(self, content, series_name, num_episodes, progress_callback=None):
        """Büyük içerikleri parçalara ayırarak işler"""
        # İçeriği ön işle
        processed_content = self.preprocess_content(content)
        
        # İçeriği değerlendir ve parçalara ayır
        content_parts = self.split_large_content(processed_content)
        
        # Parça sayısını bildir
        if progress_callback:
            progress_callback(0.1, f"İçerik {len(content_parts)} parçaya ayrıldı, işleniyor...")
        
        # ThreadPool ile asenkron işleme
        all_results = []
        
        with ThreadPoolExecutor(max_workers=min(5, len(content_parts))) as executor:
            # İş parçacıklarını başlat
            future_to_chunk = {
                executor.submit(
                    self._process_chunk, 
                    idx, chunk, series_name, num_episodes, len(content_parts)
                ): (idx, chunk) for idx, chunk in enumerate(content_parts)
            }
            
            # Tamamlanan işleri izle
            for i, future in enumerate(as_completed(future_to_chunk)):
                if progress_callback:
                    progress_callback(
                        0.1 + 0.7 * ((i + 1) / len(content_parts)),
                        f"Bölüm {i+1}/{len(content_parts)} işleniyor..."
                    )
                
                try:
                    result = future.result()
                    idx = future_to_chunk[future][0]
                    all_results.append((idx, result))
                except Exception as e:
                    print(f"Parça işlenirken hata oluştu: {e}")
        
        # Parçaları sıralı birleştir
        sorted_results = sorted(all_results, key=lambda x: x[0])
        chapters = [result for _, result in sorted_results]
        
        if progress_callback:
            progress_callback(0.8, "Bölümler birleştiriliyor...")
        
        # Kitabın ön ve arka kısımlarını oluştur
        title_suggestions = self.content_processor.generate_title_suggestions(processed_content)
        book_title = title_suggestions[0] if title_suggestions else series_name
        
        # Varsayılan olarak bölüm sayısını kullan, yoksa 1 olsun
        if not isinstance(num_episodes, int) or num_episodes <= 0:
            if isinstance(num_episodes, str) and num_episodes.isdigit():
                num_episodes = int(num_episodes)
            else:
                num_episodes = 1
        
        front_matter = self._generate_front_matter(book_title, chapters, num_episodes)
        back_matter = self._generate_back_matter(book_title, processed_content)
        
        # Tüm kitabı birleştir
        full_book = front_matter + "\n\n" + "\n\n".join(chapters) + "\n\n" + back_matter
        
        # Son işlemler
        if progress_callback:
            progress_callback(0.9, "Son düzenlemeler yapılıyor...")
        
        # Tutarlılık kontrolü ve temizlik
        full_book = self._ensure_consistency(full_book)
        self._cleanup()
        
        return full_book
    
    def _generate_front_matter(self, book_title, chapters, num_episodes):
        """Kitabın ön kısmını (kapak, içindekiler, önsöz) oluşturur"""
        # Bölüm başlıklarını çıkar
        chapter_titles = []
        for chapter in chapters:
            # "# Bölüm X: Başlık" veya "# Bölüm X" formatını ara
            matches = re.findall(r'#\s+Bölüm\s+\d+[:\s]*(.*?)(?=\n|$)', chapter, re.IGNORECASE)
            if matches:
                chapter_titles.append(f"Bölüm {len(chapter_titles)+1}: {matches[0].strip()}")
            else:
                chapter_titles.append(f"Bölüm {len(chapter_titles)+1}")
        
        # İçindekiler oluştur
        toc = "# İçindekiler\n\n"
        page_num = 1
        
        # Ön kısım sayfaları
        toc += f"Önsöz ... {page_num}\n"
        page_num += 3
        
        toc += f"Giriş ... {page_num}\n"
        page_num += 5
        
        # Bölümler
        for title in chapter_titles:
            toc += f"{title} ... {page_num}\n"
            page_num += 15  # Her bölüm için varsayılan sayfa sayısı
        
        # Arka kısım
        toc += f"Sonuç ve Değerlendirme ... {page_num}\n"
        page_num += 3
        
        toc += f"Kavram Dizini ... {page_num}\n"
        
        # Önsöz oluştur
        preface = f"""# Önsöz

Bu kitap, {book_title} konusunu ele alan kapsamlı bir çalışmadır. Kitap, toplam {len(chapters)} bölümden oluşmakta ve konunun farklı yönlerini derinlemesine incelemektedir.

Kitabın amacı, okuyucuya bu konuda sağlam bir teorik çerçeve sunmak ve pratik uygulamalar hakkında fikir vermektir. Her bölüm, konunun belirli bir yönüne odaklanmakta ve okuyucuya sistematik bir bilgi aktarımı sağlamaktadır.

Bu çalışma, {num_episodes} bölümlük bir serinin kitaplaştırılmış halidir. Orijinal içeriğin akıcılığı ve bütünlüğü korunurken, akademik bir dil ve tutarlı bir yapı oluşturulmasına özen gösterilmiştir.

Keyifli okumalar dileriz.

"""
        
        # Giriş oluştur
        introduction = f"""# Giriş

{book_title} konusu, günümüzde büyük bir öneme sahiptir. Bu kitapta, konunun tarihsel gelişiminden güncel uygulamalarına kadar geniş bir yelpazede inceleme sunulacaktır.

Kitap boyunca, aşağıdaki ana bölümler ele alınacaktır:

"""
        
        for title in chapter_titles:
            introduction += f"- {title}\n"
        
        # Tüm ön kısmı birleştir
        front_matter = f"""# {book_title}

## {len(chapters)} Bölümlük Kapsamlı İnceleme

\n\n{toc}\n\n{preface}\n\n{introduction}
"""
        
        return front_matter
    
    def _generate_back_matter(self, book_title, content):
        """Kitabın arka kısmını (sonuç, kavram dizini) oluşturur"""
        # Anahtar kavramları çıkar
        key_concepts = self.content_processor.extract_key_concepts(content, n=30)
        
        # Sonuç bölümü
        conclusion = f"""# Sonuç ve Değerlendirme

Bu kitapta, {book_title} konusu detaylı olarak incelenmiştir. İncelenen konular ışığında, şu temel çıkarımlara varmak mümkündür:

1. Konu, günümüzde giderek artan bir öneme sahiptir.
2. Farklı bakış açıları, konunun zenginliğini ve derinliğini ortaya koymaktadır.
3. Teorik çerçeve ve pratik uygulamalar arasındaki denge, konunun anlaşılmasını kolaylaştırmaktadır.

Gelecekte bu konunun daha da gelişeceği ve yeni araştırmalara konu olacağı öngörülmektedir. Bu kitabın, okuyucuya sağlam bir temel sunduğuna ve konuya ilişkin daha ileri çalışmalara ilham vereceğine inanıyoruz.
"""
        
        # Kavram dizini
        index = "# Kavram Dizini\n\n"
        for word, freq in key_concepts:
            index += f"**{word.title()}**: Metinde {freq} kez geçmektedir.\n"
        
        return f"{conclusion}\n\n{index}"
    
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
            "Index": "Dizin",
            "Summary": "Özet"
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
    
    def create_book(self, content, series_name, num_episodes, output_file=None, progress_callback=None):
        """Tam kitap oluşturma süreci"""
        start_time = time.time()
        
        try:
            if progress_callback:
                progress_callback(0.05, "İçerik değerlendiriliyor...")
            
            # İçeriği değerlendir
            assessment = self.detect_content_size(content)
            
            # İçerik boyutuna göre uygun strateji seç
            if assessment["size"] in ["small", "medium"]:
                # Küçük ve orta boy içerikler için standard EnhancedBookCreator
                if progress_callback:
                    progress_callback(0.1, "Kitap yapısı oluşturuluyor...")
                
                book_content = self.book_creator.create_book(
                    content, series_name, num_episodes
                )
            else:
                # Büyük içerikler için parçalama stratejisi
                if progress_callback:
                    progress_callback(0.1, "Büyük içerik tespit edildi, bölümlere ayrılıyor...")
                
                book_content = self.process_large_content(
                    content, series_name, num_episodes, progress_callback
                )
            
            # Dosyaya kaydet
            if output_file and book_content:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(book_content)
                    
                if progress_callback:
                    progress_callback(1.0, f"Kitap '{output_file}' dosyasına kaydedildi.")
            
            elapsed_time = time.time() - start_time
            
            if progress_callback:
                progress_callback(1.0, f"Kitap oluşturma tamamlandı. ({elapsed_time:.2f} saniye)")
            
            return book_content
            
        except Exception as e:
            if progress_callback:
                progress_callback(1.0, f"Hata: {str(e)}")
            
            self._cleanup()
            raise e