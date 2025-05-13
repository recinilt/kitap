# app.py
import os
import sys
import time
import gradio as gr
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
            doc_count = rag_system.process_single_document(file_path)
            total_docs += doc_count
            
        elapsed_time = time.time() - start_time
        progress(1.0, desc="Tamamlandı!")
        
        return f"{total_docs} doküman parçası başarıyla işlendi ve vektör veritabanına kaydedildi. ({elapsed_time:.2f} saniye)"
    except Exception as e:
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
        
        for i, file_path in enumerate(file_paths):
            progress((i / total_files), desc=f"Dosya işleniyor: {os.path.basename(file_path.name)}")
            doc_count = rag_system.process_single_document(file_path.name)
            total_docs += doc_count
            
        elapsed_time = time.time() - start_time
        progress(1.0, desc="Tamamlandı!")
        
        return f"Toplam {total_docs} doküman parçası başarıyla işlendi ve vektör veritabanına kaydedildi. ({elapsed_time:.2f} saniye)"
    except Exception as e:
        return f"Hata: {str(e)}"

def query_system(question, progress=gr.Progress()):
    global rag_system
    
    if not check_system():
        return "Önce sistemi başlatmalısınız! Sistem Başlatma sekmesine gidip 'Sistemi Başlat' düğmesine tıklayın."
    
    try:
        progress(0, desc="Sorgu hazırlanıyor...")
        start_time = time.time()
        
        progress(0.3, desc="Belge parçaları getiriliyor...")
        result = rag_system.query(question)
        
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

def process_transcripts_directory(transcript_dir, series_name, num_episodes, progress=gr.Progress()):
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
        
        if total_files == 0:
            return None, "İşlenecek dosya bulunamadı. Dizinde .txt uzantılı dosya var mı?"
        
        # Her dosyayı işle ve ilerlemeyi göster
        for i, file_path in enumerate(all_files):
            progress((i / (total_files * 2)), desc=f"Dosya işleniyor: {os.path.basename(file_path)}")
            doc_count = rag_system.process_single_document(file_path)
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
            
        prompt = f"""'{series_name}' başlıklı {num_eps} bölümlük video serisini edebi bir dille kitaplaştır. 
        Kitabı, yayınlanabilir kalitede edebi bir dille yaz. 
        İçindekiler, tanımlar, bölümler ve alt başlıklar içeren tutarlı, bütünlüklü ve tekrarsız bir kitap formatında düzenle.
        Tek bölümlük olsa da, içeriği zenginleştir ve derinleştir.
        Kitap formatı şu şekilde olsun:
        1. Kapak sayfası ve kitap başlığı
        2. İçindekiler
        3. Giriş bölümü ve konuya genel bakış
        4. Kişilerin tanıtımı
        5. Terimlerin tanımları
        6. Ana bölümler (kavramsal olarak düzenlenmiş)
        7. Alt başlıklar ve detaylı açıklamalar
        8. Sonuç ve özet bölümü
        Yayınlanacak kalitede, akıcı, edebi bir dil kullan."""
        
        progress(0.6, desc="Kitap oluşturuluyor...")
        result = rag_system.query(prompt)
        progress(0.9, desc="Kitap formatlanıyor ve dosyaya kaydediliyor...")
        
        elapsed_time = time.time() - start_time
        
        # Dosyaya kaydet
        file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
        file_path = os.path.join(os.getcwd(), file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(result["answer"])
        
        progress(1.0, desc="Tamamlandı!")
        return file_path, f"Transkript klasörü başarıyla işlendi ({total_docs} parça).\n\n{result['answer']}\n\n---\nToplam işlem süresi: {elapsed_time:.2f} saniye\nİçerik '{file_name}' dosyasına kaydedildi."
    
    except Exception as e:
        return None, f"Transkript işleme veya kitaplaştırma sırasında hata oluştu: {str(e)}"

def process_transcript_files(file_paths, series_name, num_episodes, progress=gr.Progress()):
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
        
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            progress((i / (total_files * 2)), desc=f"Dosya işleniyor: {os.path.basename(file_path.name)}")
            doc_count = rag_system.process_single_document(file_path.name)
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
            
        prompt = f"""'{series_name}' başlıklı {num_eps} bölümlük video serisini edebi bir dille kitaplaştır. 
        Kitabı, yayınlanabilir kalitede edebi bir dille yaz. 
        İçindekiler, tanımlar, bölümler ve alt başlıklar içeren tutarlı, bütünlüklü ve tekrarsız bir kitap formatında düzenle.
        Tek bölümlük olsa da, içeriği zenginleştir ve derinleştir.
        Kitap formatı şu şekilde olsun:
        1. Kapak sayfası ve kitap başlığı
        2. İçindekiler
        3. Giriş bölümü ve konuya genel bakış
        4. Kişilerin tanıtımı
        5. Terimlerin tanımları
        6. Ana bölümler (kavramsal olarak düzenlenmiş)
        7. Alt başlıklar ve detaylı açıklamalar
        8. Sonuç ve özet bölümü
        Yayınlanacak kalitede, akıcı, edebi bir dil kullan."""
        
        progress(0.6, desc="Kitap oluşturuluyor...")
        result = rag_system.query(prompt)
        progress(0.9, desc="Kitap formatlanıyor ve dosyaya kaydediliyor...")
        
        elapsed_time = time.time() - start_time
        
        # Dosyaya kaydet
        file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
        file_path = os.path.join(os.getcwd(), file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(result["answer"])
        
        progress(1.0, desc="Tamamlandı!")
        return file_path, f"Transkript dosyaları başarıyla işlendi ({total_docs} parça).\n\n{result['answer']}\n\n---\nToplam işlem süresi: {elapsed_time:.2f} saniye\nİçerik '{file_name}' dosyasına kaydedildi."
    
    except Exception as e:
        return None, f"Transkript işleme veya kitaplaştırma sırasında hata oluştu: {str(e)}"

def create_book_from_videos(series_name, num_episodes, progress=gr.Progress()):
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
        prompt = f"""'{series_name}' başlıklı {num_eps} bölümlük video serisini edebi bir dille kitaplaştır. 
        Kitabı, yayınlanabilir kalitede edebi bir dille yaz. 
        İçindekiler, tanımlar, bölümler ve alt başlıklar içeren tutarlı, bütünlüklü ve tekrarsız bir kitap formatında düzenle.
        Tek bölümlük olsa da, içeriği zenginleştir ve derinleştir.
        Kitap formatı şu şekilde olsun:
        1. Kapak sayfası ve kitap başlığı
        2. İçindekiler
        3. Giriş bölümü ve konuya genel bakış
        4. Kişilerin tanıtımı
        5. Terimlerin tanımları
        6. Ana bölümler (kavramsal olarak düzenlenmiş)
        7. Alt başlıklar ve detaylı açıklamalar
        8. Sonuç ve özet bölümü
        Yayınlanacak kalitede, akıcı, edebi bir dil kullan."""
        
        progress(0.4, desc="Kitap oluşturuluyor...")
        start_time = time.time()
        result = rag_system.query(prompt)
        progress(0.8, desc="Kitap formatlanıyor ve dosyaya kaydediliyor...")
        
        elapsed_time = time.time() - start_time
        
        # Dosyaya kaydet
        file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
        file_path = os.path.join(os.getcwd(), file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(result["answer"])
        
        progress(1.0, desc="Tamamlandı!")
        return file_path, f"{result['answer']}\n\n---\nİşlem süresi: {elapsed_time:.2f} saniye\nİçerik '{file_name}' dosyasına kaydedildi."
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
        query_input = gr.Textbox(label="Sorgunuz veya Özet İsteğiniz", lines=3)
        query_button = gr.Button("Sorguyu Gönder")
        query_output = gr.Markdown(label="Yanıt")
        query_button.click(query_system, inputs=[query_input], outputs=[query_output])
    
    with gr.Tab("Video Kitaplaştırma"):
        gr.Markdown("## Video Serisi Kitaplaştırma")
        
        series_name = gr.Textbox(label="Video Serisi Adı", value="")
        num_episodes = gr.Number(label="Video Sayısı", minimum=1, step=1, value=1, precision=0)
        
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
        book_button.click(create_book_from_videos, inputs=[series_name, num_episodes], outputs=[book_output_file, book_output])
        trans_dir_process.click(process_transcripts_directory, inputs=[trans_dir_input, series_name, num_episodes], outputs=[trans_dir_output_file, trans_dir_output])
        trans_file_process.click(process_transcript_files, inputs=[trans_file_input, series_name, num_episodes], outputs=[trans_file_output_file, trans_file_output])

# Ana çalıştırma bloğu
if __name__ == "__main__":
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860)