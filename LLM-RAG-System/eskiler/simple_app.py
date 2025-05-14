# simple_app.py
# En basit haliyle kitaplaştırma uygulaması
import os
import gradio as gr
from lightweight_book_creator import LightweightBookCreator
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Basit kitap oluşturucu
book_creator = LightweightBookCreator()

def get_video_id_from_url(url):
    """YouTube URL'sinden video ID'sini çıkarır"""
    parsed_url = urlparse(url)
    if parsed_url.hostname in ['youtu.be']:
        return parsed_url.path[1:]
    elif parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        query = parse_qs(parsed_url.query)
        return query.get("v", [None])[0]
    return None

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

def process_youtube_links(youtube_links, series_name, num_episodes, progress=gr.Progress()):
    """YouTube linklerini işleyip kitaplaştırır"""
    try:
        # Linkleri satır satır ayır
        links = [link.strip() for link in youtube_links.strip().split('\n') if link.strip()]
        
        if not links:
            return None, "Hiçbir YouTube linki girilmedi."
        
        progress(0, desc="Başlatılıyor...")
        
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
                
                # İçeriği topla
                all_content += content + "\n\n"
        
        if not temp_files:
            return None, f"Hiçbir transkript indirilemedi. İndirme günlüğü:\n\n" + "\n".join(download_log)
        
        progress(0.5, desc="Transkriptler indirildi, kitaplaştırma başlıyor...")
        
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
        
        # Kitap oluştur
        book_content = book_creator.create_book(
            all_content, 
            series_name, 
            num_eps, 
            file_path, 
            update_progress
        )
        
        # Transkript indirme günlüğü ekle
        with open(f"{series_name.replace(' ', '_')}_indirme_gunlugu.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(download_log))
        
        progress(1.0, desc="Tamamlandı!")
        
        # Başarı mesajı
        return file_path, f"{book_content}\n\n---\nKitap '{file_name}' dosyasına kaydedildi."
    
    except Exception as e:
        return None, f"YouTube transkriptlerini işleme veya kitaplaştırma sırasında hata oluştu: {str(e)}"

def process_transcript_files(file_paths, series_name, num_episodes, progress=gr.Progress()):
    """Transkript dosyalarını işleyip kitaplaştırır"""
    if not file_paths:
        return None, "Hiçbir transkript dosyası seçilmedi."
    
    try:
        # Önce transkript dosyalarını işle
        progress(0, desc="Başlatılıyor...")
        all_content = ""
        
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            progress((i / (total_files * 2)), desc=f"Dosya işleniyor: {os.path.basename(file_path.name)}")
            
            # Dosyayı oku
            with open(file_path.name, 'r', encoding='utf-8') as f:
                content = f.read()
                all_content += content + "\n\n"
        
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
            num_eps = 1  # En az 1 bölüm olmalı
        
        # Dosya adı oluştur
        file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
        file_path = os.path.join(os.getcwd(), file_name)
        
        # Progress callback
        def update_progress(progress_value, desc):
            progress(0.5 + progress_value * 0.5, desc=desc)
        
        # Kitap oluştur
        book_content = book_creator.create_book(
            all_content, 
            series_name, 
            num_eps, 
            file_path, 
            update_progress
        )
        
        progress(1.0, desc="Tamamlandı!")
        
        # Başarı mesajı
        return file_path, f"{book_content}\n\n---\nKitap '{file_name}' dosyasına kaydedildi."
    
    except Exception as e:
        return None, f"Transkript işleme veya kitaplaştırma sırasında hata oluştu: {str(e)}"

# Gradio arayüzü
def create_interface():
    with gr.Blocks(title="Basit Kitaplaştırma Sistemi") as demo:
        gr.Markdown("# 📚 Basit Kitaplaştırma Sistemi")
        
        with gr.Tab("Video Kitaplaştırma"):
            gr.Markdown("## Video Serisi Kitaplaştırma")
            
            with gr.Row():
                series_name = gr.Textbox(label="Video Serisi Adı", value="")
                num_episodes = gr.Number(label="Bölüm Sayısı", minimum=1, step=1, value=1, precision=0)
            
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
                process_youtube_links,
                inputs=[youtube_links, series_name, num_episodes],
                outputs=[youtube_output_file, youtube_output]
            )
            
            trans_file_process.click(
                process_transcript_files, 
                inputs=[trans_file_input, series_name, num_episodes], 
                outputs=[trans_file_output_file, trans_file_output]
            )
        
        with gr.Tab("Hakkında"):
            gr.Markdown("""
            # Basit Kitaplaştırma Sistemi
            
            Bu sistem, transkriptleri ve metin içeriklerini kitaplara dönüştürmek için tasarlanmış basit bir araçtır.
            
            ## Özellikler
            
            - **YouTube Entegrasyonu:** YouTube videolarından transkript indirme
            - **Metin İşleme:** İçeriği analiz ederek tutarlı kitap yapısı oluşturma
            - **Bölümleme:** İçeriği anlamlı bölümlere ayırma
            - **Tam Kitap Yapısı:** Kapak, içindekiler, önsöz, ana bölümler, sonuç ve kavram dizini
            
            ## Kullanım
            
            1. **Video Kitaplaştırma:** YouTube videoları veya mevcut transkriptlerden kitap oluşturun
            
            ## Geliştirici
            
            Bu sistem minimal bağımlılıklar kullanılarak geliştirilmiştir.
            """)
    
    return demo

if __name__ == "__main__":
    demo = create_interface()
    #demo.launch(share=False, server_name="127.0.0.1", server_port=7860)
    #demo.launch(share=False, server_name="127.0.0.1", server_port=7861)  # Port numarasını 7860'tan 7861'e değiştirdik
    demo.launch(server_name="127.0.0.1", server_port=7861, share=False, favicon_path=None, show_api=False, inbrowser=True)