# lightweight_book_creator.py
# Bağımlılık gerektirmeyen basit kitap oluşturma sistemi
import os
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor

class LightweightBookCreator:
    """
    Hafif kitap oluşturma sınıfı - Transformers, HuggingFace veya embedding gerektirmeden çalışır
    """
    
    def __init__(self):
        self.temp_files = []
        self.stopwords = set([
            "bir", "ve", "bu", "için", "ile", "da", "de", "ki", "mı", "mu", "mi", "dır", 
            "dir", "çok", "ama", "fakat", "ancak", "şey", "olarak", "gibi", "kadar", 
            "kez", "kere", "çünkü", "böylece", "dolayısıyla", "sonra", "önce", "ise", 
            "ama", "lakin", "yani", "eğer", "şayet", "belki", "galiba", "sanırım", 
            "sanki", "hatta", "üstelik", "ayrıca"
        ])

    def _cleanup(self):
        """Geçici dosyaları temizler"""
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
        self.temp_files = []
    
    def preprocess_transcript(self, text):
        """Transkript metnini ön işlemden geçirerek temizler"""
        # "[Müzik]" gibi parantez içindeki ifadeleri kaldır
        text = re.sub(r'\[\s*[^\]]+\s*\]', '', text)
        
        # Tekrarlanan satırları temizle (tam olarak aynı olan satırlar)
        lines = text.split('\n')
        unique_lines = []
        seen_lines = set()
        
        for line in lines:
            line = line.strip()
            if line and line not in seen_lines:
                unique_lines.append(line)
                seen_lines.add(line)
        
        # Tekrarlanan paragrafları temizle
        cleaned_text = '\n'.join(unique_lines)
        paragraphs = re.split(r'\n\s*\n', cleaned_text)
        unique_paragraphs = []
        seen_paragraphs = set()
        
        for para in paragraphs:
            para = para.strip()
            if para and para not in seen_paragraphs:
                unique_paragraphs.append(para)
                seen_paragraphs.add(para)
        
        return '\n\n'.join(unique_paragraphs)

    def extract_keywords(self, text, max_keywords=20):
        """Metinden anahtar kelimeleri çıkarır"""
        # Kelime frekanslarını hesapla
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = {}
        
        for word in words:
            if len(word) > 2 and word not in self.stopwords:
                if word not in word_freq:
                    word_freq[word] = 0
                word_freq[word] += 1
        
        # Frekansa göre sırala
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # En sık geçen kelimeleri döndür
        return sorted_words[:max_keywords]

    def split_into_chapters(self, text, num_chapters=5):
        """Metni bölümlere ayırır"""
        # Metni yaklaşık eşit uzunlukta paragraflara böl
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Çok az paragraf varsa, doğrudan döndür
        if len(paragraphs) <= num_chapters:
            return paragraphs
        
        # Paragrafları bölümlere dağıt
        chapters = []
        paragraphs_per_chapter = len(paragraphs) // num_chapters
        
        for i in range(num_chapters):
            start_idx = i * paragraphs_per_chapter
            end_idx = start_idx + paragraphs_per_chapter if i < num_chapters - 1 else len(paragraphs)
            chapter_text = '\n\n'.join(paragraphs[start_idx:end_idx])
            chapters.append(chapter_text)
        
        return chapters

    def generate_title(self, text):
        """Metinden başlık önerir"""
        keywords = self.extract_keywords(text, 5)
        if not keywords:
            return "İçerik Analizi"
        
        main_keyword = keywords[0][0].title()
        return f"{main_keyword}: Kapsamlı Bir İnceleme"

    def create_chapter_titles(self, chapters, series_name):
        """Bölüm başlıkları oluşturur"""
        chapter_titles = []
        
        for i, chapter in enumerate(chapters):
            # Her bölüm için anahtar kelimeler çıkar
            keywords = self.extract_keywords(chapter, 3)
            
            if keywords:
                main_keyword = keywords[0][0].title()
                chapter_titles.append(f"Bölüm {i+1}: {main_keyword}")
            else:
                chapter_titles.append(f"Bölüm {i+1}")
        
        return chapter_titles

    def generate_book_structure(self, content, series_name, num_episodes):
        """Kitap yapısı oluşturur"""
        # İçeriği temizle
        content = self.preprocess_transcript(content)
        
        # Başlık öner
        book_title = self.generate_title(content) if not series_name else series_name
        
        # Bölüm sayısını belirle
        num_chapters = max(3, min(7, num_episodes if isinstance(num_episodes, int) else 5))
        
        # Bölümlere ayır
        chapters = self.split_into_chapters(content, num_chapters)
        
        # Bölüm başlıkları
        chapter_titles = self.create_chapter_titles(chapters, book_title)
        
        # Anahtar kelimeler
        keywords = self.extract_keywords(content, 30)
        
        return {
            "title": book_title,
            "num_chapters": len(chapters),
            "chapters": chapters,
            "chapter_titles": chapter_titles,
            "keywords": keywords
        }

    def generate_table_of_contents(self, chapter_titles):
        """İçindekiler tablosu oluşturur"""
        toc = "# İçindekiler\n\n"
        page = 1
        
        # Ön kısım
        toc += f"Önsöz ... {page}\n"
        page += 3
        
        toc += f"Giriş ... {page}\n"
        page += 5
        
        # Bölümler
        for title in chapter_titles:
            toc += f"{title} ... {page}\n"
            page += 15
        
        # Son kısım
        toc += f"Sonuç ve Değerlendirme ... {page}\n"
        page += 3
        
        toc += f"Kavram Dizini ... {page}\n"
        
        return toc

    def generate_preface(self, book_title, num_chapters):
        """Önsöz bölümü oluşturur"""
        return f"""# Önsöz

Bu kitap, {book_title} konusunu ele alan kapsamlı bir çalışmadır. Kitap, toplam {num_chapters} bölümden oluşmakta ve konunun farklı yönlerini derinlemesine incelemektedir.

Kitabın amacı, okuyucuya bu konuda sağlam bir teorik çerçeve sunmak ve pratik uygulamalar hakkında fikir vermektir. Her bölüm, konunun belirli bir yönüne odaklanmakta ve okuyucuya sistematik bir bilgi aktarımı sağlamaktadır.

Bu çalışma, orijinal içeriğin akıcılığı ve bütünlüğü korunurken, akademik bir dil ve tutarlı bir yapı oluşturulmasına özen gösterilmiştir.

Keyifli okumalar dileriz.
"""

    def generate_introduction(self, book_title, chapter_titles, keywords):
        """Giriş bölümü oluşturur"""
        intro = f"""# Giriş

{book_title} konusu, günümüzde büyük bir öneme sahiptir. Bu kitapta, konunun farklı yönlerini kapsamlı bir şekilde ele alacağız.

## Kitap Yapısı

Kitap boyunca, aşağıdaki ana bölümler ele alınacaktır:

"""
        # Bölümleri listele
        for title in chapter_titles:
            intro += f"- {title}\n"
        
        # Anahtar kavramlar
        intro += "\n## Temel Kavramlar\n\nBu kitapta sıkça karşılaşacağınız temel kavramlar şunlardır:\n\n"
        
        for keyword, freq in keywords[:10]:
            intro += f"- **{keyword.title()}**: Bu kavram kitap boyunca sıkça kullanılmaktadır.\n"
        
        return intro

    def generate_conclusion(self, book_title):
        """Sonuç bölümü oluşturur"""
        return f"""# Sonuç ve Değerlendirme

Bu kitapta, {book_title} konusu detaylı olarak incelenmiştir. İncelenen konular ışığında, şu temel çıkarımlara varmak mümkündür:

1. Konu, günümüzde giderek artan bir öneme sahiptir.
2. Farklı bakış açıları, konunun zenginliğini ve derinliğini ortaya koymaktadır.
3. Teorik çerçeve ve pratik uygulamalar arasındaki denge, konunun anlaşılmasını kolaylaştırmaktadır.

Gelecekte bu konunun daha da gelişeceği ve yeni araştırmalara konu olacağı öngörülmektedir. Bu kitabın, okuyucuya sağlam bir temel sunduğuna ve konuya ilişkin daha ileri çalışmalara ilham vereceğine inanıyoruz.
"""

    def generate_index(self, keywords):
        """Kavram dizini oluşturur"""
        index = "# Kavram Dizini\n\n"
        
        for keyword, freq in keywords:
            index += f"**{keyword.title()}**: Metinde {freq} kez geçmektedir.\n"
        
        return index

    def improve_chapters(self, chapters, chapter_titles):
        """Bölümleri iyileştirir ve düzenler"""
        improved_chapters = []
        
        for i, (chapter, title) in enumerate(zip(chapters, chapter_titles)):
            # Bölüm başlığını ekle
            improved_chapter = f"# {title}\n\n"
            
            # Paragrafları böl
            paragraphs = chapter.split('\n\n')
            
            # Alt başlıklar için metni incele
            keywords = self.extract_keywords(chapter, 5)
            subsection_count = min(3, len(paragraphs) // 3 + 1)
            subsections = []
            
            # Alt başlıklar oluştur
            for j in range(subsection_count):
                if j < len(keywords):
                    subsections.append(f"## {keywords[j][0].title()}")
                else:
                    subsections.append(f"## Alt Bölüm {j+1}")
            
            # Paragrafları alt başlıklara dağıt
            paragraphs_per_subsection = len(paragraphs) // len(subsections)
            
            for j, subsection in enumerate(subsections):
                improved_chapter += subsection + "\n\n"
                
                start_idx = j * paragraphs_per_subsection
                end_idx = start_idx + paragraphs_per_subsection if j < len(subsections) - 1 else len(paragraphs)
                
                # Alt başlık içeriğini ekle
                improved_chapter += '\n\n'.join(paragraphs[start_idx:end_idx]) + "\n\n"
            
            improved_chapters.append(improved_chapter)
        
        return improved_chapters

    def fix_text_issues(self, text):
        """Metin sorunlarını düzeltir"""
        # Doldurma kelimeleri temizle
        text = re.sub(r'\b(eee|ııı|hmm|şey)\b', '', text, flags=re.IGNORECASE)
        
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
        lines = text.split('\n')
        cleaned_lines = []
        prev_line = ""
        
        for line in lines:
            if line.strip() and line.strip() != prev_line.strip():
                cleaned_lines.append(line)
            prev_line = line
        
        return '\n'.join(cleaned_lines)

    def create_book(self, content, series_name, num_episodes, output_file=None, progress_callback=None):
        """Kitap oluşturma ana fonksiyonu"""
        try:
            start_time = time.time()
            
            if progress_callback:
                progress_callback(0.1, "İçerik analiz ediliyor...")
            
            # Kitap yapısını oluştur
            book_structure = self.generate_book_structure(content, series_name, num_episodes)
            
            if progress_callback:
                progress_callback(0.3, "Bölümler düzenleniyor...")
            
            # Bölümleri iyileştir
            improved_chapters = self.improve_chapters(
                book_structure["chapters"], 
                book_structure["chapter_titles"]
            )
            
            if progress_callback:
                progress_callback(0.5, "Kitap bölümleri birleştiriliyor...")
            
            # İçindekiler tablosu
            toc = self.generate_table_of_contents(book_structure["chapter_titles"])
            
            # Ön ve arka kısımlar
            preface = self.generate_preface(book_structure["title"], book_structure["num_chapters"])
            introduction = self.generate_introduction(
                book_structure["title"], 
                book_structure["chapter_titles"], 
                book_structure["keywords"]
            )
            conclusion = self.generate_conclusion(book_structure["title"])
            index = self.generate_index(book_structure["keywords"])
            
            # Tüm kitabı birleştir
            full_book = f"""# {book_structure["title"]}

## {book_structure["num_chapters"]} Bölümlük Kapsamlı İnceleme

{toc}

{preface}

{introduction}

{"".join(improved_chapters)}

{conclusion}

{index}
"""
            
            if progress_callback:
                progress_callback(0.7, "Metin düzeltmeleri yapılıyor...")
            
            # Metin düzeltmeleri
            full_book = self.fix_text_issues(full_book)
            
            # Dosyaya kaydet
            if output_file and full_book:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(full_book)
                
                if progress_callback:
                    progress_callback(0.9, f"Kitap '{output_file}' dosyasına kaydedildi.")
            
            elapsed_time = time.time() - start_time
            
            if progress_callback:
                progress_callback(1.0, f"Kitap oluşturma tamamlandı. ({elapsed_time:.2f} saniye)")
            
            return full_book
        
        except Exception as e:
            if progress_callback:
                progress_callback(1.0, f"Hata: {str(e)}")
            
            self._cleanup()
            raise e

# Test için örnek kullanım
if __name__ == "__main__":
    creator = LightweightBookCreator()
    
    with open("example.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    book = creator.create_book(
        content, 
        "Örnek Kitap Başlığı", 
        5, 
        "ornek_kitap.txt",
        lambda progress, desc: print(f"{progress*100:.0f}% - {desc}")
    )
    
    print("Kitap oluşturuldu!")