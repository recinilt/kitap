# app.py - Gradio'nun kendi dosya seçicilerini kullanan sürüm
import gradio as gr
from rag_system import RAGSystem
import os
import time

# RAG sistemini oluştur
rag_system = RAGSystem()
system_initialized = False

def initialize_system():
    global rag_system, system_initialized
    try:
        rag_system.initialize()
        system_initialized = True
        return "Sistem başarıyla başlatıldı. LLM ve vektör veritabanı yüklendi."
    except Exception as e:
        return f"Sistem başlatılırken hata oluştu: {str(e)}"

def process_directory(directory):
    global rag_system, system_initialized
    if not system_initialized:
        return "Önce sistemi başlatmalısınız!"
    
    if not directory or not os.path.isdir(directory):
        return f"Geçerli bir dizin seçilmedi veya dizin bulunamadı."
    
    try:
        start_time = time.time()
        doc_count = rag_system.process_documents(directory)
        elapsed_time = time.time() - start_time
        return f"{doc_count} doküman parçası başarıyla işlendi ve vektör veritabanına kaydedildi. ({elapsed_time:.2f} saniye)"
    except Exception as e:
        return f"Hata: {str(e)}"

def process_file(file_paths):
    global rag_system, system_initialized
    
    if not system_initialized:
        return "Önce sistemi başlatmalısınız!"
    
    if not file_paths:
        return "Hiçbir dosya seçilmedi."
    
    try:
        total_docs = 0
        start_time = time.time()
        
        for file_path in file_paths:
            doc_count = rag_system.process_single_document(file_path.name)
            total_docs += doc_count
            
        elapsed_time = time.time() - start_time
        return f"Toplam {total_docs} doküman parçası başarıyla işlendi ve vektör veritabanına kaydedildi. ({elapsed_time:.2f} saniye)"
    except Exception as e:
        return f"Hata: {str(e)}"

def query_system(question):
    global rag_system, system_initialized
    if not system_initialized:
        return "Önce sistemi başlatmalısınız!"
    
    try:
        start_time = time.time()
        result = rag_system.query(question)
        elapsed_time = time.time() - start_time
        
        answer = result["answer"]
        sources = "\n\n**KAYNAKLAR:**\n"
        for i, doc in enumerate(result["source_documents"][:3]):
            sources += f"- Belge {i+1}: {doc.metadata.get('source', 'Bilinmeyen')}\n"
        
        return f"{answer}\n\n---\nİşlem süresi: {elapsed_time:.2f} saniye\n{sources}"
    except Exception as e:
        return f"Sorgu işlenirken hata oluştu: {str(e)}"

def process_transcripts_directory(transcript_dir, series_name, num_episodes):
    """Video transkript klasörünü işleyip kitaplaştırır"""
    global rag_system, system_initialized
    
    if not system_initialized:
        return "Önce sistemi başlatmalısınız!"
    
    if not transcript_dir or not os.path.isdir(transcript_dir):
        return f"Geçerli bir transkript dizini seçilmedi veya bulunamadı."
    
    try:
        # Önce transkript klasörünü işle
        start_time = time.time()
        doc_count = rag_system.process_documents(transcript_dir)
        
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
        4. Ana bölümler (kavramsal olarak düzenlenmiş)
        5. Alt başlıklar ve detaylı açıklamalar
        6. Sonuç ve özet bölümü
        Yayınlanacak kalitede, akıcı, edebi bir dil kullan."""
        
        result = rag_system.query(prompt)
        elapsed_time = time.time() - start_time
        
        # Dosyaya kaydet
        file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(result["answer"])
        
        return f"Transkript klasörü başarıyla işlendi ({doc_count} parça).\n\n{result['answer']}\n\n---\nToplam işlem süresi: {elapsed_time:.2f} saniye\nİçerik '{file_name}' dosyasına kaydedildi."
    
    except Exception as e:
        return f"Transkript işleme veya kitaplaştırma sırasında hata oluştu: {str(e)}"

def process_transcript_files(file_paths, series_name, num_episodes):
    """Transkript dosyalarını işleyip kitaplaştırır"""
    global rag_system, system_initialized
    
    if not system_initialized:
        return "Önce sistemi başlatmalısınız!"
    
    if not file_paths:
        return "Hiçbir transkript dosyası seçilmedi."
    
    try:
        # Önce transkript dosyalarını işle
        start_time = time.time()
        total_docs = 0
        
        for file_path in file_paths:
            doc_count = rag_system.process_single_document(file_path.name)
            total_docs += doc_count
        
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
        4. Ana bölümler (kavramsal olarak düzenlenmiş)
        5. Alt başlıklar ve detaylı açıklamalar
        6. Sonuç ve özet bölümü
        Yayınlanacak kalitede, akıcı, edebi bir dil kullan."""
        
        result = rag_system.query(prompt)
        elapsed_time = time.time() - start_time
        
        # Dosyaya kaydet
        file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(result["answer"])
        
        return f"Transkript dosyaları başarıyla işlendi ({total_docs} parça).\n\n{result['answer']}\n\n---\nToplam işlem süresi: {elapsed_time:.2f} saniye\nİçerik '{file_name}' dosyasına kaydedildi."
    
    except Exception as e:
        return f"Transkript işleme veya kitaplaştırma sırasında hata oluştu: {str(e)}"

def create_book_from_videos(series_name, num_episodes):
    global rag_system, system_initialized
    if not system_initialized:
        return "Önce sistemi başlatmalısınız!"
    
    try:
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
            
        prompt = f"""'{series_name}' başlıklı {num_eps} bölümlük video serisini edebi bir dille kitaplaştır. 
        Kitabı, yayınlanabilir kalitede edebi bir dille yaz. 
        İçindekiler, tanımlar, bölümler ve alt başlıklar içeren tutarlı, bütünlüklü ve tekrarsız bir kitap formatında düzenle.
        Tek bölümlük olsa da, içeriği zenginleştir ve derinleştir.
        Kitap formatı şu şekilde olsun:
        1. Kapak sayfası ve kitap başlığı
        2. İçindekiler
        3. Giriş bölümü ve konuya genel bakış
        4. Ana bölümler (kavramsal olarak düzenlenmiş)
        5. Alt başlıklar ve detaylı açıklamalar
        6. Sonuç ve özet bölümü
        Yayınlanacak kalitede, akıcı, edebi bir dil kullan."""
        
        start_time = time.time()
        result = rag_system.query(prompt)
        elapsed_time = time.time() - start_time
        
        # Dosyaya kaydet
        file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(result["answer"])
        
        return f"{result['answer']}\n\n---\nİşlem süresi: {elapsed_time:.2f} saniye\nİçerik '{file_name}' dosyasına kaydedildi."
    except Exception as e:
        return f"Kitaplaştırma işlemi sırasında hata oluştu: {str(e)}"

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
        
        with gr.Accordion("Transkript Klasöründen Kitaplaştırma", open=False):
            trans_dir_input = gr.Textbox(label="Transkript Klasörü Yolu")
            trans_dir_process = gr.Button("Klasörü İşle ve Kitaplaştır")
        
        with gr.Accordion("Transkript Dosyalarından Kitaplaştırma", open=False):
            trans_file_input = gr.File(label="Transkript Dosyaları", file_count="multiple")
            trans_file_process = gr.Button("Dosyaları İşle ve Kitaplaştır")
        
        book_output = gr.Markdown(label="Oluşturulan Kitap")
        
        # Kitaplaştırma işlemleri
        book_button.click(create_book_from_videos, inputs=[series_name, num_episodes], outputs=[book_output])
        trans_dir_process.click(process_transcripts_directory, inputs=[trans_dir_input, series_name, num_episodes], outputs=[book_output])
        trans_file_process.click(process_transcript_files, inputs=[trans_file_input, series_name, num_episodes], outputs=[book_output])

if __name__ == "__main__":
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860)