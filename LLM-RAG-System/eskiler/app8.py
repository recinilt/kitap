# app.py
import os
import sys
import time
import gradio as gr
import re
from rag_system import RAGSystem

# Global değişkenler
rag_system = RAGSystem()
system_initialized = False

def initialize_system():
    global rag_system, system_initialized
    try:
        rag_system.initialize()
        system_initialized = True
        return "Sistem başarıyla başlatıldı. LLM ve vektör veritabanı yüklendi."
    except Exception as e:
        system_initialized = False
        return f"Sistem başlatılırken hata oluştu: {str(e)}"

def check_system():
    """Sistemin başlatılıp başlatılmadığını kontrol eder"""
    global rag_system, system_initialized
    
    if not system_initialized or not hasattr(rag_system, 'llm') or rag_system.llm is None:
        try:
            rag_system.initialize()
            system_initialized = True
            return True
        except:
            return False
    return True

def preprocess_transcript(text):
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

def get_default_prompt(prompt_type, series_name="", num_episodes="", content_summary=""):
    """İstem tipine göre varsayılan promptu oluşturur"""
    if prompt_type == "book":
        return f"""'{series_name}' başlıklı {num_episodes} bölümlük video serisini edebi bir dille kitaplaştır. 

İÇERİK HAKKINDA ÖZET: {content_summary}

ÖNEMLİ KURALLAR:
1. Kitabı tamamen TÜRKÇE olarak yaz. Hiçbir şekilde İngilizce veya başka dil kullanma.
2. Kitap, akademik bir çalışma düzeyinde, yayınlanabilir kalitede edebi bir dille yazılmalıdır.
3. Metni kitap formatında düzenle, tutarlı ve bütünlüklü bir akış sağla.
4. Transkriptteki tekrarları ve doldurma kelimeleri ("Eee", "yani", "işte" gibi) temizle.
5. Konuşma dilinden yazı diline uygun şekilde çevir. Anlaşılması güç olan ifadeleri düzelt.
6. Mantık akışını koru, ana argümanları ve temel düşünceleri öne çıkar.
7. Diyalektik, yerleşik düzen, toplumsal değişim gibi konuları vurgula.
8. Verilen içerikten fazlasını ekleme, uydurma; sadece içeriği düzenle ve zenginleştir.

KİTABIN YAPI VE BÖLÜMLERİ:
1. Kapak sayfası ve kitap başlığı - Çarpıcı ve içeriği yansıtan bir başlık seç
2. İçindekiler - Detaylı bölüm listesi
3. Önsöz - Konu ve temel yaklaşımın özeti
4. Giriş - Genel kavramsal çerçeve ve tarihsel bağlam
5. Temel Kavramlar ve Tanımlar - İçerikte geçen teknik terimlerin tanımlanması
6. Ana bölümler (içerik analizi sonucu belirlenmeli, yaklaşık 3-7 ana bölüm)
   - Her ana bölüm kendi içinde alt başlıklara ayrılmalı
   - Yerleşik düzene geçiş olgusunun farklı boyutları ele alınmalı
   - Toplumsal dönüşümün etkileri ayrı bölümlerde incelenmeli
7. Sonuç ve Değerlendirme - Ana argümanların özeti ve çıkarımlar
8. Kavram Dizini - Metinde geçen önemli kavramların listesi

Paragraflar akıcı, açık ve anlaşılır olmalı. Bilimsel bir metinde olması gerektiği gibi objektif ve tutarlı bir dil kullan. Yeri geldiğinde örneklerle açıkla. Anlatımda felsefi derinlik ve edebi üslup dengesi kur."""
    elif prompt_type == "summary":
        return f"""Aşağıdaki metni özetlemen gerekiyor:

{content_summary}

ÖNEMLİ KURALLAR:
1. Özeti tamamen TÜRKÇE olarak yaz.
2. Metnin ana fikrini, temel argümanlarını ve önemli detaylarını koru.
3. Gereksiz tekrarları, doldurma ifadeleri ve önemsiz ayrıntıları çıkar.
4. Özeti bölümlere ayır ve mantıklı bir akış sağla.
5. Metnin orijinal yapısını ve akışını koru.
6. Anlaşılması güç ifadeleri daha açık hale getir.
7. Kendi yorumunu katma, sadece metindeki bilgileri özetle.

ÖZET BÖLÜMLERİ:
1. Giriş - Metnin ana konusu ve amacı
2. Ana Bölüm - Temel argümanlar ve önemli noktalar
3. Sonuç - Metnin vardığı sonuçlar ve çıkarımlar

Özetin, orijinal metnin yaklaşık %25-30'u kadar olmalı. Akademik ve nesnel bir dil kullan."""
    elif prompt_type == "query":
        return f"""Aşağıdaki soru veya konuyla ilgili kapsamlı bir yanıt hazırla:

{content_summary}

ÖNEMLİ KURALLAR:
1. Yanıtı tamamen TÜRKÇE olarak yaz.
2. Konuyla ilgili tüm önemli bilgileri kapsamlı şekilde açıkla.
3. Yanıtı mantıklı bir yapıda organize et.
4. Bilimsel ve nesnel bir dil kullan.
5. Gerektiğinde örnekler ver ve karmaşık kavramları açıkla.
6. Kaynakları belirt ve güvenilir bilgiler sun.
7. Mümkün olduğunca güncel ve doğru bilgi ver.

YANIT YAPISI:
1. Giriş - Konunun genel çerçevesi ve önemini belirten kısa bir giriş
2. Ana Bölüm - Konunun farklı yönlerini detaylı şekilde açıklayan bölümler
3. Sonuç - Bilgilerin özeti ve varsa genel çıkarımlar

Doğru, tarafsız ve eğitici bir içerik oluştur."""
    else:
        return ""

def process_directory(directory, progress=gr.Progress()):
    global rag_system
    
    if not check_system():
        return "Önce sistemi başlatmalısınız! Sistem Başlatma sekmesine gidip 'Sistemi Başlat' düğmesine tıklayın."
    
    if not directory or not os.path.isdir(directory):
        return f"Geçerli bir dizin seçilmedi veya dizin bulunamadı."
    
    try:
        progress(0, desc="Başlatılıyor...")
        start_time = time.time()
        
        # Dosya listesini al
        all_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.txt'):
                    all_files.append(os.path.join(root, file))
        
        total_files = len(all_files)
        total_docs = 0
        
        if total_files == 0:
            return "İşlenecek dosya bulunamadı. Dizinde .txt uzantılı dosya var mı?"
        
        # Her dosyayı işle ve ilerlemeyi göster
        for i, file_path in enumerate(all_files):
            progress((i / total_files), desc=f"Dosya işleniyor: {os.path.basename(file_path)}")
            
            # Dosyayı oku ve ön işlemden geçir
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Ön işlemden geçirilmiş içeriği geçici bir dosyaya yaz
            temp_file_path = f"{file_path}.temp"
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(preprocess_transcript(content))
            
            # Geçici dosyayı işle
            doc_count = rag_system.process_single_document(temp_file_path)
            total_docs += doc_count
            
            # Geçici dosyayı sil
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
        elapsed_time = time.time() - start_time
        progress(1.0, desc="Tamamlandı!")
        
        return f"{total_docs} doküman parçası başarıyla işlendi ve vektör veritabanına kaydedildi. ({elapsed_time:.2f} saniye)"
    except Exception as e:
        # Temizlik: Hata durumunda geçici dosyaları temizle
        for file_path in all_files:
            temp_file_path = f"{file_path}.temp"
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        return f"Hata: {str(e)}"

def process_file(file_paths, progress=gr.Progress()):
    global rag_system
    
    if not check_system():
        return "Önce sistemi başlatmalısınız! Sistem Başlatma sekmesine gidip 'Sistemi Başlat' düğmesine tıklayın."
    
    if not file_paths:
        return "Hiçbir dosya seçilmedi."
    
    try:
        progress(0, desc="Başlatılıyor...")
        total_docs = 0
        start_time = time.time()
        
        total_files = len(file_paths)
        temp_files = []
        
        for i, file_path in enumerate(file_paths):
            progress((i / total_files), desc=f"Dosya işleniyor: {os.path.basename(file_path.name)}")
            
            # Dosyayı oku ve ön işlemden geçir
            with open(file_path.name, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Ön işlemden geçirilmiş içeriği geçici bir dosyaya yaz
            temp_file_path = f"{file_path.name}.temp"
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(preprocess_transcript(content))
            
            temp_files.append(temp_file_path)
            
            # Geçici dosyayı işle
            doc_count = rag_system.process_single_document(temp_file_path)
            total_docs += doc_count
            
        # Temizlik: Geçici dosyaları sil
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
        elapsed_time = time.time() - start_time
        progress(1.0, desc="Tamamlandı!")
        
        return f"Toplam {total_docs} doküman parçası başarıyla işlendi ve vektör veritabanına kaydedildi. ({elapsed_time:.2f} saniye)"
    except Exception as e:
        # Temizlik: Hata durumunda geçici dosyaları temizle
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return f"Hata: {str(e)}"

def query_system(query_prompt, question, use_default_prompt, progress=gr.Progress()):
    global rag_system
    
    if not check_system():
        return "Önce sistemi başlatmalısınız! Sistem Başlatma sekmesine gidip 'Sistemi Başlat' düğmesine tıklayın."
    
    try:
        progress(0, desc="Sorgu hazırlanıyor...")
        start_time = time.time()
        
        # Hangi promptu kullanacağımızı belirle
        prompt_to_use = question
        if use_default_prompt:
            # Varsayılan promptu kullan ama soru kısmını değiştir
            default_prompt = get_default_prompt("query", content_summary=question)
            prompt_to_use = default_prompt
        else:
            # Kullanıcı tanımlı promptu kullan
            prompt_to_use = query_prompt
        
        progress(0.3, desc="Belge parçaları getiriliyor...")
        result = rag_system.query(prompt_to_use)
        
        progress(0.8, desc="Yanıt formatlanıyor...")
        elapsed_time = time.time() - start_time
        
        answer = result["answer"]
        sources = "\n\n**KAYNAKLAR:**\n"
        for i, doc in enumerate(result["source_documents"][:3]):
            sources += f"- Belge {i+1}: {doc.metadata.get('source', 'Bilinmeyen')}\n"
        
        progress(1.0, desc="Tamamlandı!")
        return f"{answer}\n\n---\nİşlem süresi: {elapsed_time:.2f} saniye\n{sources}"
    except Exception as e:
        return f"Sorgu işlenirken hata oluştu: {str(e)}"

def process_transcripts_directory(transcript_dir, series_name, num_episodes, custom_prompt, use_default_prompt, progress=gr.Progress()):
    """Video transkript klasörünü işleyip kitaplaştırır"""
    global rag_system
    
    if not check_system():
        return None, "Önce sistemi başlatmalısınız! Sistem Başlatma sekmesine gidip 'Sistemi Başlat' düğmesine tıklayın."
    
    if not transcript_dir or not os.path.isdir(transcript_dir):
        return None, f"Geçerli bir transkript dizini seçilmedi veya bulunamadı."
    
    try:
        # Önce transkript klasörünü işle
        progress(0, desc="Başlatılıyor...")
        start_time = time.time()
        
        # Dosya listesini al
        all_files = []
        for root, dirs, files in os.walk(transcript_dir):
            for file in files:
                if file.endswith('.txt'):
                    all_files.append(os.path.join(root, file))
        
        total_files = len(all_files)
        total_docs = 0
        temp_files = []
        all_content = ""
        
        if total_files == 0:
            return None, "İşlenecek dosya bulunamadı. Dizinde .txt uzantılı dosya var mı?"
        
        # Her dosyayı işle ve ilerlemeyi göster
        for i, file_path in enumerate(all_files):
            progress((i / (total_files * 2)), desc=f"Dosya işleniyor: {os.path.basename(file_path)}")
            
            # Dosyayı oku
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                all_content += content + "\n\n"
            
            # Ön işlemden geçirilmiş içeriği geçici bir dosyaya yaz
            temp_file_path = f"{file_path}.temp"
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(preprocess_transcript(content))
            
            temp_files.append(temp_file_path)
            
            # Geçici dosyayı işle
            doc_count = rag_system.process_single_document(temp_file_path)
            total_docs += doc_count
        
        progress(0.5, desc="Transkriptler işlendi, kitaplaştırma başlıyor...")
        
        # Temizlik: Geçici dosyaları sil
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        # Sayı doğrulamasını iyileştir
        if isinstance(num_episodes, str):
            num_episodes = num_episodes.strip()
            if num_episodes == "":
                num_episodes = 1
            else:
                try:
                    num_episodes = float(num_episodes)
                except:
                    num_episodes = 1
        
        num_eps = int(num_episodes)
        if num_eps <= 0:
            num_eps = 1  # En az 1 video olmalı
        
        # İçerik özeti oluştur (ilk 1000 karakter)
        content_summary = preprocess_transcript(all_content)[:1000] + "..."
        
        # Hangi promptu kullanacağımızı belirle
        prompt_to_use = ""
        if use_default_prompt:
            # Varsayılan promptu kullan
            prompt_to_use = get_default_prompt("book", series_name, num_eps, content_summary)
        else:
            # Kullanıcı tanımlı promptu kullan
            prompt_to_use = custom_prompt.format(
                series_name=series_name,
                num_episodes=num_eps,
                content_summary=content_summary
            )
        
        progress(0.6, desc="Kitap oluşturuluyor...")
        result = rag_system.query(prompt_to_use)
        progress(0.9, desc="Kitap formatlanıyor ve dosyaya kaydediliyor...")
        
        # Sonuçtaki İngilizce içerikleri kontrol et
        book_content = result["answer"]
        
        # Belirgin İngilizce pasajları kontrol et
        english_sections = re.findall(r'\b(Introduction|Title|Subtitle|Author|Publisher|ISBN|Cover Image|Section \d+:|Example \d+:|Conclusion)\b', book_content)
        if english_sections:
            # İngilizce başlıkları Türkçe'ye çevir
            book_content = book_content.replace("Introduction:", "Giriş:")
            book_content = book_content.replace("Introduction", "Giriş")
            book_content = book_content.replace("Title:", "Başlık:")
            book_content = book_content.replace("Subtitle:", "Alt Başlık:")
            book_content = book_content.replace("Author:", "Yazar:")
            book_content = book_content.replace("Publisher:", "Yayıncı:")
            book_content = book_content.replace("ISBN:", "ISBN:")
            book_content = book_content.replace("Cover Image:", "Kapak Resmi:")
            book_content = book_content.replace("Section", "Bölüm")
            book_content = book_content.replace("Example", "Örnek")
            book_content = book_content.replace("Conclusion:", "Sonuç:")
            book_content = book_content.replace("Conclusion", "Sonuç")
        
        elapsed_time = time.time() - start_time
        
        # Dosyaya kaydet
        file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
        file_path = os.path.join(os.getcwd(), file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(book_content)
        
        progress(1.0, desc="Tamamlandı!")
        return file_path, f"Transkript klasörü başarıyla işlendi ({total_docs} parça).\n\n{book_content}\n\n---\nToplam işlem süresi: {elapsed_time:.2f} saniye\nİçerik '{file_name}' dosyasına kaydedildi."
    
    except Exception as e:
        # Temizlik: Hata durumunda geçici dosyaları temizle
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return None, f"Transkript işleme veya kitaplaştırma sırasında hata oluştu: {str(e)}"

def process_transcript_files(file_paths, series_name, num_episodes, custom_prompt, use_default_prompt, progress=gr.Progress()):
    """Transkript dosyalarını işleyip kitaplaştırır"""
    global rag_system
    
    if not check_system():
        return None, "Önce sistemi başlatmalısınız! Sistem Başlatma sekmesine gidip 'Sistemi Başlat' düğmesine tıklayın."
    
    if not file_paths:
        return None, "Hiçbir transkript dosyası seçilmedi."
    
    try:
        # Önce transkript dosyalarını işle
        progress(0, desc="Başlatılıyor...")
        start_time = time.time()
        total_docs = 0
        temp_files = []
        all_content = ""
        
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            progress((i / (total_files * 2)), desc=f"Dosya işleniyor: {os.path.basename(file_path.name)}")
            
            # Dosyayı oku
            with open(file_path.name, 'r', encoding='utf-8') as f:
                content = f.read()
                all_content += content + "\n\n"
            
            # Ön işlemden geçirilmiş içeriği geçici bir dosyaya yaz
            temp_file_path = f"{file_path.name}.temp"
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(preprocess_transcript(content))
            
            temp_files.append(temp_file_path)
            
            # Geçici dosyayı işle
            doc_count = rag_system.process_single_document(temp_file_path)
            total_docs += doc_count
        
        # Temizlik: Geçici dosyaları sil
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        progress(0.5, desc="Transkriptler işlendi, kitaplaştırma başlıyor...")
        
        # Sayı doğrulamasını iyileştir
        if isinstance(num_episodes, str):
            num_episodes = num_episodes.strip()
            if num_episodes == "":
                num_episodes = 1
            else:
                try:
                    num_episodes = float(num_episodes)
                except:
                    num_episodes = 1
        
        num_eps = int(num_episodes)
        if num_eps <= 0:
            num_eps = 1  # En az 1 video olmalı
        
        # İçerik özeti oluştur (ilk 1000 karakter)
        content_summary = preprocess_transcript(all_content)[:1000] + "..."
            
        # Hangi promptu kullanacağımızı belirle
        prompt_to_use = ""
        if use_default_prompt:
            # Varsayılan promptu kullan
            prompt_to_use = get_default_prompt("book", series_name, num_eps, content_summary)
        else:
            # Kullanıcı tanımlı promptu kullan
            prompt_to_use = custom_prompt.format(
                series_name=series_name,
                num_episodes=num_eps,
                content_summary=content_summary
            )
        
        progress(0.6, desc="Kitap oluşturuluyor...")
        result = rag_system.query(prompt_to_use)
        progress(0.9, desc="Kitap formatlanıyor ve dosyaya kaydediliyor...")
        
        # Sonuçtaki İngilizce içerikleri kontrol et
        book_content = result["answer"]
        
        # Belirgin İngilizce pasajları kontrol et
        english_sections = re.findall(r'\b(Introduction|Title|Subtitle|Author|Publisher|ISBN|Cover Image|Section \d+:|Example \d+:|Conclusion)\b', book_content)
        if english_sections:
            # İngilizce başlıkları Türkçe'ye çevir
            book_content = book_content.replace("Introduction:", "Giriş:")
            book_content = book_content.replace("Introduction", "Giriş")
            book_content = book_content.replace("Title:", "Başlık:")
            book_content = book_content.replace("Subtitle:", "Alt Başlık:")
            book_content = book_content.replace("Author:", "Yazar:")
            book_content = book_content.replace("Publisher:", "Yayıncı:")
            book_content = book_content.replace("ISBN:", "ISBN:")
            book_content = book_content.replace("Cover Image:", "Kapak Resmi:")
            book_content = book_content.replace("Section", "Bölüm")
            book_content = book_content.replace("Example", "Örnek")
            book_content = book_content.replace("Conclusion:", "Sonuç:")
            book_content = book_content.replace("Conclusion", "Sonuç")
        
        elapsed_time = time.time() - start_time
        
        # Dosyaya kaydet
        file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
        file_path = os.path.join(os.getcwd(), file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(book_content)
        
        progress(1.0, desc="Tamamlandı!")
        return file_path, f"Transkript dosyaları başarıyla işlendi ({total_docs} parça).\n\n{book_content}\n\n---\nToplam işlem süresi: {elapsed_time:.2f} saniye\nİçerik '{file_name}' dosyasına kaydedildi."
    
    except Exception as e:
        # Temizlik: Hata durumunda geçici dosyaları temizle
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return None, f"Transkript işleme veya kitaplaştırma sırasında hata oluştu: {str(e)}"

def create_book_from_videos(series_name, num_episodes, custom_prompt, use_default_prompt, progress=gr.Progress()):
    global rag_system
    
    if not check_system():
        return None, "Önce sistemi başlatmalısınız! Sistem Başlatma sekmesine gidip 'Sistemi Başlat' düğmesine tıklayın."
    
    try:
        progress(0, desc="Başlatılıyor...")
        # Farklı formatlardaki giriş değerlerini düzgün bir şekilde işle
        if isinstance(num_episodes, str):
            num_episodes = num_episodes.strip()
            if num_episodes == "":
                num_episodes = 1
            else:
                try:
                    num_episodes = float(num_episodes)
                except:
                    num_episodes = 1
        
        num_eps = int(num_episodes)
        if num_eps <= 0:
            num_eps = 1  # En az 1 video olmalı
        
        progress(0.2, desc="Kitap içeriği hazırlanıyor...")
        
        # Hangi promptu kullanacağımızı belirle
        prompt_to_use = ""
        if use_default_prompt:
            # Varsayılan promptu kullan
            prompt_to_use = get_default_prompt("book", series_name, num_eps)
        else:
            # Kullanıcı tanımlı promptu kullan
            prompt_to_use = custom_prompt.format(
                series_name=series_name,
                num_episodes=num_eps,
                content_summary=""
            )
        
        progress(0.4, desc="Kitap oluşturuluyor...")
        start_time = time.time()
        result = rag_system.query(prompt_to_use)
        progress(0.8, desc="Kitap formatlanıyor ve dosyaya kaydediliyor...")
        
        # Sonuçtaki İngilizce içerikleri kontrol et
        book_content = result["answer"]
        
        # Belirgin İngilizce pasajları kontrol et
        english_sections = re.findall(r'\b(Introduction|Title|Subtitle|Author|Publisher|ISBN|Cover Image|Section \d+:|Example \d+:|Conclusion)\b', book_content)
        if english_sections:
            # İngilizce başlıkları Türkçe'ye çevir
            book_content = book_content.replace("Introduction:", "Giriş:")
            book_content = book_content.replace("Introduction", "Giriş")
            book_content = book_content.replace("Title:", "Başlık:")
            book_content = book_content.replace("Subtitle:", "Alt Başlık:")
            book_content = book_content.replace("Author:", "Yazar:")
            book_content = book_content.replace("Publisher:", "Yayıncı:")
            book_content = book_content.replace("ISBN:", "ISBN:")
            book_content = book_content.replace("Cover Image:", "Kapak Resmi:")
            book_content = book_content.replace("Section", "Bölüm")
            book_content = book_content.replace("Example", "Örnek")
            book_content = book_content.replace("Conclusion:", "Sonuç:")
            book_content = book_content.replace("Conclusion", "Sonuç")
        
        elapsed_time = time.time() - start_time
        
        # Dosyaya kaydet
        file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
        file_path = os.path.join(os.getcwd(), file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(book_content)
        
        progress(1.0, desc="Tamamlandı!")
        return file_path, f"{book_content}\n\n---\nİşlem süresi: {elapsed_time:.2f} saniye\nİçerik '{file_name}' dosyasına kaydedildi."
    except Exception as e:
        return None, f"Kitaplaştırma işlemi sırasında hata oluştu: {str(e)}"

# Gradio arayüzü
with gr.Blocks(title="LLM+RAG+FAISS Sistemi") as demo:
    gr.Markdown("# 📚 LLM+RAG+FAISS Edebi İçerik Üretim Sistemi")
    
    with gr.Tab("Sistem Başlatma"):
        gr.Markdown("## Sistem Başlatma")
        init_button = gr.Button("Sistemi Başlat")
        init_output = gr.Textbox(label="Durum")
        init_button.click(initialize_system, inputs=[], outputs=[init_output])
    
    with gr.Tab("Doküman İşleme"):
        gr.Markdown("## Doküman İşleme")
        with gr.Row():
            with gr.Column():
                dir_input = gr.Textbox(label="Doküman Dizini Yolu")
                dir_button = gr.Button("Dizini İşle")
            with gr.Column():
                file_input = gr.File(label="Doküman Dosyaları", file_count="multiple")
                file_button = gr.Button("Dosyaları İşle")
        process_output = gr.Textbox(label="İşlem Sonucu")
        
        dir_button.click(process_directory, inputs=[dir_input], outputs=[process_output])
        file_button.click(process_file, inputs=[file_input], outputs=[process_output])
    
    with gr.Tab("Sorgu & Özet"):
        gr.Markdown("## Sorgu Yapma / Özet Oluşturma")
        
        use_default_query_prompt = gr.Checkbox(label="Varsayılan istemi kullan", value=True)
        
        with gr.Group():
            query_custom_prompt = gr.Textbox(
                label="Özel İstem (Prompt)", 
                lines=10,
                value=get_default_prompt("query", content_summary="{question}"),
                interactive=True
            )
        
        query_input = gr.Textbox(label="Sorgunuz veya Özet İsteğiniz", lines=3)
        query_button = gr.Button("Sorguyu Gönder")
        query_output = gr.Markdown(label="Yanıt")
        
        # Checkbox değiştiğinde promptu güncelle
        def update_query_prompt_interactivity(use_default):
            return gr.Textbox.update(interactive=not use_default)
        
        use_default_query_prompt.change(
            update_query_prompt_interactivity, 
            inputs=[use_default_query_prompt], 
            outputs=[query_custom_prompt]
        )
        
        query_button.click(
            query_system, 
            inputs=[query_custom_prompt, query_input, use_default_query_prompt], 
            outputs=[query_output]
        )
    
    with gr.Tab("Video Kitaplaştırma"):
        gr.Markdown("## Video Serisi Kitaplaştırma")
        
        with gr.Row():
            series_name = gr.Textbox(label="Video Serisi Adı", value="")
            num_episodes = gr.Number(label="Video Sayısı", minimum=1, step=1, value=1, precision=0)
        
        use_default_prompt = gr.Checkbox(label="Varsayılan istemi kullan", value=True)
        
        with gr.Group():
            custom_prompt = gr.Textbox(
                label="Özel İstem (Prompt)", 
                lines=20,
                value=get_default_prompt("book", "{series_name}", "{num_episodes}", "{content_summary}"),
                interactive=True
            )
        
        # Checkbox değiştiğinde promptu güncelle
        def update_prompt_interactivity(use_default):
            return gr.Textbox.update(interactive=not use_default)
        
        use_default_prompt.change(
            update_prompt_interactivity, 
            inputs=[use_default_prompt], 
            outputs=[custom_prompt]
        )
        
        with gr.Accordion("Mevcut Verilerle Kitaplaştırma", open=True):
            book_button = gr.Button("Mevcut Verilerle Kitaplaştır")
            book_output_file = gr.File(label="Oluşturulan Kitap Dosyası", interactive=False)
            book_output = gr.Markdown(label="Oluşturulan Kitap İçeriği")
        
        with gr.Accordion("Transkript Klasöründen Kitaplaştırma", open=False):
            trans_dir_input = gr.Textbox(label="Transkript Klasörü Yolu")
            trans_dir_process = gr.Button("Klasörü İşle ve Kitaplaştır")
            trans_dir_output_file = gr.File(label="Oluşturulan Kitap Dosyası", interactive=False)
            trans_dir_output = gr.Markdown(label="Oluşturulan Kitap İçeriği")
        
        with gr.Accordion("Transkript Dosyalarından Kitaplaştırma", open=False):
            trans_file_input = gr.File(label="Transkript Dosyaları", file_count="multiple")
            trans_file_process = gr.Button("Dosyaları İşle ve Kitaplaştır")
            trans_file_output_file = gr.File(label="Oluşturulan Kitap Dosyası", interactive=False)
            trans_file_output = gr.Markdown(label="Oluşturulan Kitap İçeriği")
        
        # Kitaplaştırma işlemleri
        book_button.click(
            create_book_from_videos, 
            inputs=[series_name, num_episodes, custom_prompt, use_default_prompt], 
            outputs=[book_output_file, book_output]
        )
        trans_dir_process.click(
            process_transcripts_directory, 
            inputs=[trans_dir_input, series_name, num_episodes, custom_prompt, use_default_prompt], 
            outputs=[trans_dir_output_file, trans_dir_output]
        )
        trans_file_process.click(
            process_transcript_files, 
            inputs=[trans_file_input, series_name, num_episodes, custom_prompt, use_default_prompt], 
            outputs=[trans_file_output_file, trans_file_output]
        )

# Ana çalıştırma bloğu
if __name__ == "__main__":
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860)