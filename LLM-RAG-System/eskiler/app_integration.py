# app_integration.py
import os
import sys
import time
import re
import gradio as gr
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from book_generation_service import BookGenerationService
from content_processor import ContentProcessor

class AppIntegration:
    """RAG sistemini Gradio arayüzüne entegre eder ve kitap oluşturma işlemlerini yönetir"""
    
    def __init__(self, rag_system):
        """
        RAG sistemini uygulama arayüzüne entegre eder
        
        Args:
            rag_system: Mevcut RAG sistemi
        """
        self.rag_system = rag_system
        self.book_service = BookGenerationService(rag_system)
        self.content_processor = ContentProcessor()
        self.system_initialized = False
    
    def initialize_system(self):
        """Sistemi başlatır"""
        try:
            self.rag_system.initialize()
            self.system_initialized = True
            return "Sistem başarıyla başlatıldı. LLM ve vektör veritabanı yüklendi."
        except Exception as e:
            self.system_initialized = False
            return f"Sistem başlatılırken hata oluştu: {str(e)}"
    
    def check_system(self):
        """Sistemin başlatılıp başlatılmadığını kontrol eder"""
        if not self.system_initialized or not hasattr(self.rag_system, 'llm') or self.rag_system.llm is None:
            try:
                self.rag_system.initialize()
                self.system_initialized = True
                return True
            except:
                return False
        return True
    
    def get_video_id_from_url(self, url):
        """YouTube URL'sinden video ID'sini çıkarır"""
        parsed_url = urlparse(url)
        if parsed_url.hostname in ['youtu.be']:
            return parsed_url.path[1:]
        elif parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
            query = parse_qs(parsed_url.query)
            return query.get("v", [None])[0]
        return None
    
    def sanitize_filename(self, name):
        """Dosya adını temizler"""
        return re.sub(r'[\\/*?:"<>|]', "", name).strip()
    
    def download_transcript_from_url(self, url, lang="tr"):
        """YouTube video URL'sinden transkript indirir"""
        video_id = self.get_video_id_from_url(url)
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
    
    def process_youtube_links(self, youtube_links, series_name, num_episodes, custom_prompt, use_default_prompt, progress=gr.Progress()):
        """YouTube linklerini işleyip kitaplaştırır"""
        if not self.check_system():
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
                    
                file_path, log_message = self.download_transcript_from_url(link)
                download_log.append(log_message)
                
                if file_path:
                    temp_files.append(file_path)
                    
                    # Dosyayı oku
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # İçeriği ön işlemden geçir ve topla
                    processed_content = self.content_processor.preprocess_transcript(content)
                    all_content += processed_content + "\n\n"
                    
                    # İşlenmek üzere geçici dosyayı vektör veritabanına ekle
                    doc_count = self.rag_system.process_single_document(file_path)
            
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
            
            # Dosya adı oluştur
            file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
            file_path = os.path.join(os.getcwd(), file_name)
            
            # Progress callback
            def update_progress(progress_value, desc):
                progress(0.5 + progress_value * 0.5, desc=desc)
            
            # Kitap oluşturma hizmetini kullanarak kitap oluştur
            book_content = self.book_service.create_book(
                all_content, 
                series_name, 
                num_eps, 
                file_path, 
                update_progress
            )
            
            # Transkript indirme günlüğü ekle
            with open(f"{series_name.replace(' ', '_')}_indirme_gunlugu.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(download_log))
            
            elapsed_time = time.time() - start_time
            progress(1.0, desc="Tamamlandı!")
            
            # Kısa bir özet oluştur
            content_stats = self.content_processor.calculate_readability(book_content)
            
            stats_summary = f"""
            # Kitap İstatistikleri
            - **Toplam Cümle Sayısı:** {content_stats['sentence_count']}
            - **Toplam Kelime Sayısı:** {content_stats['word_count']}
            - **Ortalama Cümle Uzunluğu:** {content_stats['avg_words_per_sentence']:.2f} kelime
            - **Tahmini Sayfa Sayısı:** {content_stats['word_count'] // 300} sayfa
            - **İşlem Süresi:** {elapsed_time:.2f} saniye
            
            İçerik '{file_name}' dosyasına kaydedildi.
            """
            
            return file_path, f"{book_content}\n\n---\n{stats_summary}"
        
        except Exception as e:
            return None, f"YouTube transkriptlerini işleme veya kitaplaştırma sırasında hata oluştu: {str(e)}"
    
    def process_transcript_files(self, file_paths, series_name, num_episodes, custom_prompt, use_default_prompt, progress=gr.Progress()):
        """Transkript dosyalarını işleyip kitaplaştırır"""
        if not self.check_system():
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
                
                # Dosyayı işle
                doc_count = self.rag_system.process_single_document(file_path.name)
                total_docs += doc_count
            
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
            
            # Dosya adı oluştur
            file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
            file_path = os.path.join(os.getcwd(), file_name)
            
            # Progress callback
            def update_progress(progress_value, desc):
                progress(0.5 + progress_value * 0.5, desc=desc)
            
            # Kitap oluşturma hizmetini kullanarak kitap oluştur
            book_content = self.book_service.create_book(
                all_content, 
                series_name, 
                num_eps, 
                file_path, 
                update_progress
            )
            
            elapsed_time = time.time() - start_time
            progress(1.0, desc="Tamamlandı!")
            
            # Kısa bir özet oluştur
            content_stats = self.content_processor.calculate_readability(book_content)
            
            stats_summary = f"""
            # Kitap İstatistikleri
            - **Toplam Cümle Sayısı:** {content_stats['sentence_count']}
            - **Toplam Kelime Sayısı:** {content_stats['word_count']}
            - **Ortalama Cümle Uzunluğu:** {content_stats['avg_words_per_sentence']:.2f} kelime
            - **Tahmini Sayfa Sayısı:** {content_stats['word_count'] // 300} sayfa
            - **İşlem Süresi:** {elapsed_time:.2f} saniye
            
            İçerik '{file_name}' dosyasına kaydedildi.
            """
            
            return file_path, f"{book_content}\n\n---\n{stats_summary}"
        
        except Exception as e:
            return None, f"Transkript işleme veya kitaplaştırma sırasında hata oluştu: {str(e)}"
    
    def process_directory(self, directory, progress=gr.Progress()):
        """Dizindeki tüm dokümanları işler"""
        if not self.check_system():
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
                    f.write(self.content_processor.preprocess_transcript(content))
                
                # Geçici dosyayı işle
                doc_count = self.rag_system.process_single_document(temp_file_path)
                total_docs += doc_count
                
                # Geçici dosyayı sil
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                
            elapsed_time = time.time() - start_time
            progress(1.0, desc="Tamamlandı!")
            
            return f"{total_docs} doküman parçası başarıyla işlendi ve vektör veritabanına kaydedildi. ({elapsed_time:.2f} saniye)"
        except Exception as e:
            return f"Hata: {str(e)}"
    
    def process_file(self, file_paths, progress=gr.Progress()):
        """Seçilen dosyaları işler"""
        if not self.check_system():
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
                    f.write(self.content_processor.preprocess_transcript(content))
                
                temp_files.append(temp_file_path)
                
                # Geçici dosyayı işle
                doc_count = self.rag_system.process_single_document(temp_file_path)
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
    
    def query_system(self, query_prompt, question, use_default_prompt, progress=gr.Progress()):
        """RAG sistemine sorgu yapar"""
        if not self.check_system():
            return "Önce sistemi başlatmalısınız! Sistem Başlatma sekmesine gidip 'Sistemi Başlat' düğmesine tıklayın."
        
        try:
            progress(0, desc="Sorgu hazırlanıyor...")
            start_time = time.time()
            
            # Hangi promptu kullanacağımızı belirle
            prompt_to_use = question
            if use_default_prompt:
                # Varsayılan promptu kullan
                prompt_to_use = f"""
                Aşağıdaki soru veya konuyla ilgili kapsamlı bir yanıt hazırla:

                {question}

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

                Doğru, tarafsız ve eğitici bir içerik oluştur.
                """
            else:
                # Kullanıcı tanımlı promptu kullan
                prompt_to_use = query_prompt
            
            progress(0.3, desc="Belge parçaları getiriliyor...")
            result = self.rag_system.query(prompt_to_use)
            
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
    
    def create_gradio_interface(self):
        """Gradio arayüzünü oluşturur"""
        with gr.Blocks(title="Gelişmiş Kitaplaştırma Sistemi") as demo:
            gr.Markdown("# 📚 Gelişmiş Kitaplaştırma ve İçerik Analiz Sistemi")
            
            with gr.Tab("Sistem Başlatma"):
                gr.Markdown("## Sistem Başlatma")
                init_button = gr.Button("Sistemi Başlat")
                init_output = gr.Textbox(label="Durum")
                init_button.click(self.initialize_system, inputs=[], outputs=[init_output])
            
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
                
                dir_button.click(self.process_directory, inputs=[dir_input], outputs=[process_output])
                file_button.click(self.process_file, inputs=[file_input], outputs=[process_output])
            
            with gr.Tab("Sorgu & Özet"):
                gr.Markdown("## Sorgu Yapma / Özet Oluşturma")
                
                use_default_query_prompt = gr.Checkbox(label="Varsayılan istemi kullan", value=True)
                
                with gr.Group():
                    query_custom_prompt = gr.Textbox(
                        label="Özel İstem (Prompt)", 
                        lines=10,
                        value="""
                        Aşağıdaki soru veya konuyla ilgili kapsamlı bir yanıt hazırla:

                        {question}

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

                        Doğru, tarafsız ve eğitici bir içerik oluştur.
                        """,
                        interactive=False
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
                    self.query_system, 
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
                        value="""
                        '{series_name}' başlıklı {num_episodes} bölümlük video serisini edebi bir dille kitaplaştır. 

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

                        Paragraflar akıcı, açık ve anlaşılır olmalı. Bilimsel bir metinde olması gerektiği gibi objektif ve tutarlı bir dil kullan. Yeri geldiğinde örneklerle açıkla. Anlatımda felsefi derinlik ve edebi üslup dengesi kur.
                        """,
                        interactive=False
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
                
                with gr.Accordion("Transkript Dosyalarından Kitaplaştırma", open=False):
                    trans_file_input = gr.File(label="Transkript Dosyaları", file_count="multiple")
                    trans_file_process = gr.Button("Dosyaları İşle ve Kitaplaştır")
                    trans_file_output_file = gr.File(label="Oluşturulan Kitap Dosyası", interactive=False)
                    trans_file_output = gr.Markdown(label="Oluşturulan Kitap İçeriği")
                
                # Kitaplaştırma işlemleri
                youtube_process.click(
                    self.process_youtube_links,
                    inputs=[youtube_links, series_name, num_episodes, custom_prompt, use_default_prompt],
                    outputs=[youtube_output_file, youtube_output]
                )
                
                trans_file_process.click(
                    self.process_transcript_files, 
                    inputs=[trans_file_input, series_name, num_episodes, custom_prompt, use_default_prompt], 
                    outputs=[trans_file_output_file, trans_file_output]
                )
            
            with gr.Tab("Hakkında"):
                gr.Markdown("""
                # Gelişmiş Kitaplaştırma ve İçerik Analiz Sistemi
                
                Bu sistem, transkriptleri ve metin içeriklerini işleyerek yüksek kaliteli kitaplar oluşturmak için tasarlanmıştır.
                
                ## Özellikler
                
                - **İçerik Analizi:** Metin içeriğini analiz ederek otomatik kitap yapısı oluşturma
                - **Akıllı Bölümleme:** Büyük içerikleri otomatik olarak parçalara ayırma ve işleme
                - **Tutarlı Kitap Yapısı:** Ön kısım (kapak, içindekiler, önsöz) ve arka kısım (sonuç, kavram dizini) oluşturma
                - **YouTube Entegrasyonu:** YouTube videolarından transkript indirme ve kitaplaştırma
                - **RAG Desteği:** Vektör tabanlı benzerlik araması ile ilgili içerikleri tespit etme
                - **Çoklu Dil Desteği:** Türkçe içerikler için optimize edilmiş işleme
                
                ## Kullanım
                
                1. **Sistem Başlatma:** İlk olarak "Sistem Başlatma" sekmesinden sistemi başlatın
                2. **Doküman İşleme:** İşlemek istediğiniz dokümanları yükleyin veya dizin seçin
                3. **Video Kitaplaştırma:** YouTube videoları veya mevcut transkriptlerden kitap oluşturun
                4. **Sorgu & Özet:** Belirli bir konuda sorgu yapın veya özet oluşturun

                ## Geliştirici
                
                Bu sistem, açık kaynaklı LLM ve RAG teknolojileri kullanılarak geliştirilmiştir.
                """)
            
        return demo