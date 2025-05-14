import time
import gradio as gr
import re
from rag_system import RAGSystem
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs
from book_generator import generate_full_book
#from book_generator import generate_smart_book
from book_generator import *
import os
from book_generator import process_txt_folder_and_generate_book


def run_process_txt_folder_and_generate_book(folder_path, title):
    return process_txt_folder_and_generate_book(rag_system, folder_path, title)



def smart_book_interface(series_name, file_obj, progress=gr.Progress()):
    global rag_system

    if not check_system():
        return None, "❌ Önce sistemi başlatmalısınız!"

    try:
        progress(0.1, desc="Dosya okunuyor...")
        content = file_obj.read().decode("utf-8")
        file_obj.close()

        progress(0.3, desc="Kitap oluşturuluyor...")
        result_text = generate_smart_book(rag_system, series_name, content)

        output_file = f"{series_name.replace(' ', '_')}_akilli_kitap.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result_text)

        progress(1.0, desc="Tamamlandı.")
        return output_file, f"✅ Kitap oluşturuldu: {output_file}"

    except Exception as e:
        return None, f"❌ Hata oluştu: {str(e)}"




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

def get_video_id_from_url(url):
    """YouTube URL'sinden video ID'sini çıkarır"""
    parsed_url = urlparse(url)
    if parsed_url.hostname in ['youtu.be']:
        return parsed_url.path[1:]
    elif parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        query = parse_qs(parsed_url.query)
        return query.get("v", [None])[0]
    return None

def sanitize_filename(name):
    """Dosya adını temizler"""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def download_transcript_from_url(url, lang="tr"):
    """YouTube video URL'sinden transkript indirir"""
    video_id = get_video_id_from_url(url)
    if not video_id:
        return None, f"❌ Geçerli bir YouTube video bağlantısı değil: {url}"

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang, "en"])
        filename = f"{video_id}.txt"
        filepath = os.path.join(os.getcwd(), filename)

        # Transkripti tek bir metin olarak birleştir
        transcript_text = "\n".join([entry['text'] for entry in transcript])
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(transcript_text)

        return filepath, f"✅ Transkript başarıyla '{filename}' olarak kaydedildi."

    except TranscriptsDisabled:
        return None, f"❌ Video için transkript devre dışı: {url}"
    except NoTranscriptFound:
        return None, f"❌ Video için '{lang}' veya 'en' dilinde transkript bulunamadı: {url}"
    except Exception as e:
        return None, f"❌ Transkript indirme hatası ({url}): {str(e)}"

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
    elif prompt_type == "documentary":
        return f"""'{series_name}' başlıklı {num_episodes} bölümlük belgesel serisini edebi bir dille kitaplaştır.

    İÇERİK HAKKINDA ÖZET: {content_summary}

    ÖNEMLİ KURALLAR:
    1. Kitabı tamamen TÜRKÇE olarak yaz. Hiçbir şekilde İngilizce veya başka dil kullanma.
    2. Kitap, akademik bir belgesel kitabı düzeyinde, yayınlanabilir kalitede edebi bir dille yazılmalıdır.
    3. Metni kitap formatında düzenle, tutarlı ve bütünlüklü bir akış sağla.
    4. Belgeseldeki teknik terim ve kavramları doğru şekilde kullan ve gerektiğinde açıkla.
    5. Görsel anlatımları yazılı dile uygun şekilde çevir. Anlaşılması güç olan ifadeleri düzelt.
    6. Kronolojik ve tematik akışı koru, ana konuları ve temel düşünceleri öne çıkar.
    7. Belgeselde sunulan bilimsel veriler, tarihi olaylar ve uzman görüşlerini koruyarak aktır.
    8. Verilen içerikten fazlasını ekleme, uydurma; sadece içeriği düzenle ve zenginleştir.

    KİTABIN YAPI VE BÖLÜMLERİ:
    1. Kapak sayfası ve kitap başlığı - Çarpıcı ve içeriği yansıtan bir başlık
    2. İçindekiler - Detaylı bölüm listesi
    3. Önsöz - Belgeselin amacı ve kapsamı hakkında özet
    4. Giriş - Belgesel konusunun genel çerçevesi ve önemi
    5. Her bölüm için ayrı kısımlar (belgesel bölümlerine paralel olarak)
    - Her bölümün ana teması ve öne çıkan noktaları
    - Röportajlardan önemli alıntılar
    - Görüntülenen olayların ve yerlerin detaylı betimlemeleri
    6. Tematik analiz bölümleri - Belgeselin ele aldığı ana temaların derinlemesine incelenmesi
    7. Sonuç ve Değerlendirme - Belgeselin vardığı sonuçlar ve çıkarımlar
    8. Ek Bilgiler - Belgeselde kısaca değinilen ancak daha fazla bilgi gerektiren konular
    9. Kaynakça - Belgeselde kullanılan kaynaklar (eğer belirtilmişse)

    Paragraflar akıcı, açık ve anlaşılır olmalı. Belgesel içeriğinin ciddiyetini ve bilimsel değerini korurken, okuyucu için ilgi çekici bir anlatım kullan."""
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
    temp_files = []
    
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

def process_youtube_links(youtube_links, series_name, num_episodes, custom_prompt, use_default_prompt, progress=gr.Progress()):
    """YouTube linklerini işleyip kitaplaştırır"""
    global rag_system
    
    if not check_system():
        return None, "Önce sistemi başlatmalısınız! Sistem Başlatma sekmesine gidip 'Sistemi Başlat' düğmesine tıklayın."
    
    try:
        # Linkleri satır satır ayır
        links = [link.strip() for link in youtube_links.strip().split('\n') if link.strip()]
        
        if not links:
            return None, "Hiçbir YouTube linki girilmedi."
        
        progress(0, desc="Başlatılıyor...")
        start_time = time.time()
        
        # Transkriptleri indir
        temp_files = []
        all_content = ""
        download_log = []
        
        for i, link in enumerate(links):
            progress((i / (len(links) * 2)), desc=f"Transkript indiriliyor: {link}")
            
            # URL'den video ID'sini çıkar ve transkripti indir
            if "&" in link:
                link = link.split("&")[0]  # URL parametrelerini temizle
                
            file_path, log_message = download_transcript_from_url(link)
            download_log.append(log_message)
            
            if file_path:
                temp_files.append(file_path)
                
                # Dosyayı oku
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # İçeriği ön işlemden geçir ve topla
                processed_content = preprocess_transcript(content)
                all_content += processed_content + "\n\n"
                
                # İşlenmek üzere geçici dosyayı vektör veritabanına ekle
                doc_count = rag_system.process_single_document(file_path)
        
        if not temp_files:
            return None, f"Hiçbir transkript indirilemedi. İndirme günlüğü:\n\n" + "\n".join(download_log)
        
        progress(0.5, desc="Transkriptler indirildi ve işlendi, kitaplaştırma başlıyor...")
        
        # Sayı doğrulamasını iyileştir
        if isinstance(num_episodes, str):
            num_episodes = num_episodes.strip()
            if num_episodes == "":
                num_episodes = len(links)  # Link sayısı kadar bölüm
            else:
                try:
                    num_episodes = float(num_episodes)
                except:
                    num_episodes = len(links)
        
        num_eps = int(num_episodes)
        if num_eps <= 0:
            num_eps = len(links)  # Link sayısı kadar bölüm
        
        # İçerik özeti oluştur (ilk 1000 karakter)
        content_summary = all_content[:1000] + "..."
            
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
            
        # Transkript indirme günlüğü ekle
        with open(f"{series_name.replace(' ', '_')}_indirme_gunlugu.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(download_log))
        
        progress(1.0, desc="Tamamlandı!")
        return file_path, f"YouTube transkriptleri başarıyla indirildi ve işlendi ({len(temp_files)} video).\n\n{book_content}\n\n---\nToplam işlem süresi: {elapsed_time:.2f} saniye\nİçerik '{file_name}' dosyasına kaydedildi."
    
    except Exception as e:
        return None, f"YouTube transkriptlerini işleme veya kitaplaştırma sırasında hata oluştu: {str(e)}"

def process_multiple_youtube_series(youtube_links, series_name, custom_prompt, use_default_prompt, prompt_type="documentary", progress=gr.Progress()):
    """Çoklu YouTube serisini işleyip kitaplaştırır"""
    global rag_system
    
    if not check_system():
        return None, "Önce sistemi başlatmalısınız! Sistem Başlatma sekmesine gidip 'Sistemi Başlat' düğmesine tıklayın."
    
    try:
        # Linkleri satır satır ayır
        links = [link.strip() for link in youtube_links.strip().split('\n') if link.strip()]
        
        if not links:
            return None, "Hiçbir YouTube linki girilmedi."
        
        progress(0, desc="Başlatılıyor...")
        start_time = time.time()
        
        # Klasör oluştur
        temp_folder = f"temp_{int(start_time)}"
        os.makedirs(temp_folder, exist_ok=True)
        
        # Transkriptleri indir
        temp_files = []
        all_content = ""
        download_log = []
        processed_docs = 0
        
        progress(0.05, desc="Transkriptler indiriliyor...")
        
        # 1. Tüm transkriptleri indir ve işle
        for i, link in enumerate(links):
            progress_val = 0.05 + (i / len(links) * 0.45)
            progress(progress_val, desc=f"Transkript indiriliyor ({i+1}/{len(links)}): {link}")
            
            # URL'den video ID'sini çıkar ve transkripti indir
            if "&" in link:
                link = link.split("&")[0]  # URL parametrelerini temizle
                
            file_path, log_message = download_transcript_from_url(link)
            download_log.append(log_message)
            
            if file_path:
                # Dosyayı geçici klasöre taşı
                new_file_path = os.path.join(temp_folder, os.path.basename(file_path))
                os.rename(file_path, new_file_path)
                temp_files.append(new_file_path)
                
                # Dosyayı oku
                with open(new_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # İçeriği ön işlemden geçir
                processed_content = preprocess_transcript(content)
                
                # İşlenmiş içeriği yeni dosyaya yaz
                processed_file_path = f"{new_file_path}.processed"
                with open(processed_file_path, 'w', encoding='utf-8') as f:
                    f.write(processed_content)
                
                # İçeriği topla
                all_content += processed_content + "\n\n" + f"--- Video {i+1} Sonu ---\n\n"
                
                # İşlenmek üzere geçici dosyayı vektör veritabanına ekle
                doc_count = rag_system.process_single_document(processed_file_path)
                processed_docs += doc_count
                
                # İşlenmiş dosyayı sil
                if os.path.exists(processed_file_path):
                    os.remove(processed_file_path)
        
        if not temp_files:
            # Geçici klasörü temizle
            if os.path.exists(temp_folder):
                import shutil
                shutil.rmtree(temp_folder)
            return None, f"Hiçbir transkript indirilemedi. İndirme günlüğü:\n\n" + "\n".join(download_log)
        
        progress(0.5, desc=f"Tüm transkriptler indirildi ve işlendi ({len(temp_files)} video, {processed_docs} parça)")
        
        # 2. Kitaplaştırma
        progress(0.6, desc="Kitap oluşturuluyor...")
        
        # İçerik özeti oluştur (ilk 1000 karakter)
        content_summary = all_content[:1000] + "..."
            
        # Hangi promptu kullanacağımızı belirle
        prompt_to_use = ""
        if use_default_prompt:
            # Varsayılan promptu kullan
            prompt_to_use = get_default_prompt(prompt_type, series_name, len(links), content_summary)
        else:
            # Kullanıcı tanımlı promptu kullan
            prompt_to_use = custom_prompt.format(
                series_name=series_name,
                num_episodes=len(links),
                content_summary=content_summary
            )
        
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
        
        # 3. Dosyaları kaydet
        file_name = f"{series_name.replace(' ', '_')}_belgesel_kitabi.txt"
        file_path = os.path.join(os.getcwd(), file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(book_content)
            
        # Transkript indirme günlüğü ekle
        log_file = f"{series_name.replace(' ', '_')}_indirme_gunlugu.txt"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("\n".join(download_log))
        
        # Tüm transkriptleri tek bir dosyada topla
        all_transcripts_file = f"{series_name.replace(' ', '_')}_tum_transkriptler.txt"
        with open(all_transcripts_file, "w", encoding="utf-8") as f:
            f.write(all_content)
        
        # Temizlik
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        # Geçici klasörü temizle
        if os.path.exists(temp_folder):
            os.rmdir(temp_folder)
        
        progress(1.0, desc="Tamamlandı!")
        
        result_message = (
            f"✅ Belgesel serisi kitaplaştırma tamamlandı!\n\n"
            f"- {len(temp_files)} video transkripti işlendi\n"
            f"- {processed_docs} doküman parçası vektör veritabanına eklendi\n"
            f"- İşlem süresi: {elapsed_time:.2f} saniye\n\n"
            f"Çıktı dosyaları:\n"
            f"1. {file_name} - Oluşturulan kitap\n"
            f"2. {all_transcripts_file} - Tüm transkriptler\n"
            f"3. {log_file} - İndirme günlüğü\n\n"
            f"Kitap içeriği önizleme:\n\n{book_content[:500]}...\n\n"
            f"[Not: Tam kitap içeriği '{file_name}' dosyasında bulunmaktadır.]"
        )
        
        return file_path, result_message
    
    except Exception as e:
        # Hata durumunda temizlik yap
        try:
            # Geçici klasörü temizle
            if os.path.exists(temp_folder):
                import shutil
                shutil.rmtree(temp_folder)
        except:
            pass
            
        return None, f"Belgesel serisi kitaplaştırma sırasında hata oluştu: {str(e)}"

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

def generate_book_by_sections(series_name, file_obj, progress=gr.Progress()):
    global rag_system

    if not check_system():
        return None, "❌ Önce sistemi başlatmalısınız!"

    try:
        progress(0, desc="Dosya okunuyor...")
        summary_text = file_obj.read().decode("utf-8")
        file_obj.close()

        sections = [
            "Kapak ve Başlık",
            "Önsöz",
            "Giriş: Kavramsal ve Tarihsel Çerçeve",
            "Yerleşik Düzene Geçiş",
            "Toplumsal Dönüşümler",
            "Sosyal Davranışların Evrimi",
            "Bireyin Psikolojik Değişimi",
            "Kolektif Bilinç ve Kültür",
            "Modern Hayata Etkileri",
            "Sonuç ve Değerlendirme",
            "Kavram Dizini"
        ]

        progress(0.3, desc="Bölüm bölüm kitap üretiliyor...")
        full_text = generate_full_book(rag_system, series_name, summary_text, sections)

        out_file = f"{series_name.replace(' ', '_')}_tam_kitap.txt"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(full_text)

        progress(1.0, desc="Tamamlandı.")
        return out_file, f"✅ Kitap başarıyla oluşturuldu: {out_file}"

    except Exception as e:
        return None, f"❌ Hata oluştu: {str(e)}"



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
        
        with gr.Accordion("YouTube Linklerinden Kitaplaştırma", open=True):
            gr.Markdown("Her satıra bir YouTube linki girin. Sistem, bu videolardan transkriptleri indirecek ve kitaplaştıracaktır.")
            youtube_links = gr.Textbox(
                label="YouTube Linkleri (Her satıra bir link)", 
                lines=5,
                placeholder="https://www.youtube.com/watch?v=VIDEO_ID_1\nhttps://www.youtube.com/watch?v=VIDEO_ID_2"
            )
            youtube_process = gr.Button("YouTube Linklerini İşle ve Kitaplaştır")
            youtube_output_file = gr.File(label="Oluşturulan Kitap Dosyası", interactive=False)
            youtube_output = gr.Markdown(label="Oluşturulan Kitap İçeriği")
        
        with gr.Accordion("Mevcut Verilerle Kitaplaştırma", open=False):
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
        youtube_process.click(
            process_youtube_links,
            inputs=[youtube_links, series_name, num_episodes, custom_prompt, use_default_prompt],
            outputs=[youtube_output_file, youtube_output]
        )
        
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
        with gr.Accordion("🧩 Bölüm Bölüm Tam Kitaplaştırma", open=False):
            section_series_name = gr.Textbox(label="Kitap Başlığı")
            section_input_file = gr.File(label="İçerik Özeti Dosyası (.txt)")
            section_run = gr.Button("Bölüm Bölüm Kitaplaştır")
            section_output_file = gr.File(label="Oluşturulan Kitap Dosyası", interactive=False)
            section_output = gr.Markdown(label="İşlem Sonucu")

            section_run.click(
                generate_book_by_sections,
                inputs=[section_series_name, section_input_file],
                outputs=[section_output_file, section_output]
        )
            
        with gr.Accordion("🤖 Akıllı Kitaplaştırıcı (Geniş Özet + Tam Kitap)", open=False):
            smart_series_name = gr.Textbox(label="Kitap Başlığı")
            smart_file_input = gr.File(label="İçerik Dosyası (.txt)")
            smart_run_button = gr.Button("Akıllı Kitaplaştır")
            smart_file_output = gr.File(label="Çıktı Dosyası", interactive=False)
            smart_output_text = gr.Markdown(label="İşlem Durumu")

            smart_run_button.click(
                smart_book_interface,
                inputs=[smart_series_name, smart_file_input],
                outputs=[smart_file_output, smart_output_text]
        )

    with gr.Tab("📺 Belgesel Serisi Kitaplaştırma"):
        gr.Markdown("## Belgesel Serisi Kitaplaştırma")
        gr.Markdown("Bu sekme birden fazla belgesel/video linkini işleyerek kapsamlı bir kitap oluşturur.")
        
        with gr.Row():
            doc_series_name = gr.Textbox(label="Belgesel/Video Serisi Adı", value="", placeholder="Örn: Evrenin Gizemi")
        
        doc_use_default_prompt = gr.Checkbox(label="Varsayılan belgesel istemini kullan", value=True)
        
        with gr.Group():
            doc_custom_prompt = gr.Textbox(
                label="Özel İstem (Prompt)", 
                lines=20,
                value=get_default_prompt("documentary", "{series_name}", "{num_episodes}", "{content_summary}"),
                interactive=True
            )
        
        # Checkbox değiştiğinde promptu güncelle
        doc_use_default_prompt.change(
            update_prompt_interactivity, 
            inputs=[doc_use_default_prompt], 
            outputs=[doc_custom_prompt]
        )
        
        doc_youtube_links = gr.Textbox(
            label="YouTube Linkleri (Her satıra bir link)", 
            lines=10,
            placeholder=(
                "https://www.youtube.com/watch?v=VIDEO_ID_1\n"
                "https://www.youtube.com/watch?v=VIDEO_ID_2\n"
                "https://www.youtube.com/watch?v=VIDEO_ID_3\n"
                "... (istediğiniz kadar link ekleyebilirsiniz)"
            )
        )
        
        doc_process_button = gr.Button("🎬 Belgesel Serisini İşle ve Kitaplaştır", variant="primary")
        doc_output_file = gr.File(label="Oluşturulan Kitap Dosyası")
        doc_output = gr.Markdown(label="İşlem Sonucu")
        
        # Belgesel serisi kitaplaştırma fonksiyonu bağlantısı
        doc_process_button.click(
            process_multiple_youtube_series,
            inputs=[doc_youtube_links, doc_series_name, doc_custom_prompt, doc_use_default_prompt],
            outputs=[doc_output_file, doc_output]
        )

    with gr.Tab("📁 Klasörden Kitap Üret"):
        folder_input = gr.Textbox(label="Klasör Yolu (tam yol gir)")
        folder_title = gr.Textbox(label="Kitap Başlığı")
        run_button = gr.Button("🧠 Tüm Klasörü İşle ve Kitaplaştır")
        output_file = gr.File(label="Çıktı Dosyası")
        output_msg = gr.Markdown()

        run_button.click(
            run_process_txt_folder_and_generate_book,
            inputs=[folder_input, folder_title],
            outputs=[output_file, output_msg]
        )





    

# Ana çalıştırma bloğu
if __name__ == "__main__":
    #demo.launch(share=False, server_name="127.0.0.1", server_port=7860)
    demo.queue().launch(share=False, server_name="127.0.0.1", server_port=7863)
