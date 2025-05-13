# app.py
import gradio as gr
from rag_system import RAGSystem
import os
import time
import tkinter as tk
from tkinter import filedialog

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

def browse_directory():
    """Windows dosya gezgini ile klasör seçimi"""
    root = tk.Tk()
    root.withdraw()  # Tkinter ana penceresini gizle
    folder_path = filedialog.askdirectory(title="Doküman Klasörünü Seçin")
    root.destroy()
    return folder_path

def browse_file():
    """Windows dosya gezgini ile dosya seçimi"""
    root = tk.Tk()
    root.withdraw()  # Tkinter ana penceresini gizle
    file_path = filedialog.askopenfilename(
        title="Doküman Dosyasını Seçin", 
        filetypes=[("Metin Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")]
    )
    root.destroy()
    return file_path

def browse_transcript_directory():
    """Windows dosya gezgini ile video transkript klasör seçimi"""
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Video Transkript Klasörünü Seçin")
    root.destroy()
    return folder_path

def browse_transcript_file():
    """Windows dosya gezgini ile video transkript dosya seçimi"""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Video Transkript Dosyasını Seçin",
        filetypes=[("Metin Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")]
    )
    root.destroy()
    return file_path

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

def process_file(file_path):
    global rag_system, system_initialized
    if not system_initialized:
        return "Önce sistemi başlatmalısınız!"
    
    if not file_path or not os.path.isfile(file_path):
        return f"Geçerli bir dosya seçilmedi veya dosya bulunamadı."
    
    try:
        start_time = time.time()
        doc_count = rag_system.process_single_document(file_path)
        elapsed_time = time.time() - start_time
        return f"{doc_count} doküman parçası başarıyla işlendi ve vektör veritabanına kaydedildi. ({elapsed_time:.2f} saniye)"
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

def process_transcripts_directory(directory, series_name, num_episodes):
    """Video transkript klasörünü işleyip kitaplaştırır"""
    global rag_system, system_initialized
    
    if not system_initialized:
        return "Önce sistemi başlatmalısınız!"
    
    if not directory or not os.path.isdir(directory):
        return f"Geçerli bir transkript dizini seçilmedi veya bulunamadı."
    
    try:
        # Önce transkript klasörünü işle
        start_time = time.time()
        doc_count = rag_system.process_documents(directory)
        
        # Sonra kitaplaştırma sorgusunu yap
        try:
            num_eps = int(num_episodes)
            if num_eps <= 0:
                return "Video sayısı sıfırdan büyük olmalıdır."
                
            prompt = f"""'{series_name}' başlıklı {num_eps} bölümlük video serisini edebi bir dille kitaplaştır. 
            İçindekiler, tanımlar, bölümler ve alt başlıklar içeren tutarlı, bütünlüklü ve tekrarsız bir kitap formatında düzenle."""
            
            result = rag_system.query(prompt)
            elapsed_time = time.time() - start_time
            
            # Dosyaya kaydet
            file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(result["answer"])
            
            return f"Transkript klasörü başarıyla işlendi ({doc_count} parça).\n\n{result['answer']}\n\n---\nToplam işlem süresi: {elapsed_time:.2f} saniye\nİçerik '{file_name}' dosyasına kaydedildi."
        
        except ValueError:
            return "Geçersiz video sayısı! Lütfen geçerli bir sayı girin."
    except Exception as e:
        return f"Transkript işleme veya kitaplaştırma sırasında hata oluştu: {str(e)}"

def process_transcript_file(file_path, series_name, num_episodes):
    """Tek bir transkript dosyasını işleyip kitaplaştırır"""
    global rag_system, system_initialized
    
    if not system_initialized:
        return "Önce sistemi başlatmalısınız!"
    
    if not file_path or not os.path.isfile(file_path):
        return f"Geçerli bir transkript dosyası seçilmedi veya bulunamadı."
    
    try:
        # Önce transkript dosyasını işle
        start_time = time.time()
        doc_count = rag_system.process_single_document(file_path)
        
        # Sonra kitaplaştırma sorgusunu yap
        try:
            num_eps = int(num_episodes)
            if num_eps <= 0:
                return "Video sayısı sıfırdan büyük olmalıdır."
                
            prompt = f"""'{series_name}' başlıklı {num_eps} bölümlük video serisini edebi bir dille kitaplaştır. 
            İçindekiler, tanımlar, bölümler ve alt başlıklar içeren tutarlı, bütünlüklü ve tekrarsız bir kitap formatında düzenle."""
            
            result = rag_system.query(prompt)
            elapsed_time = time.time() - start_time
            
            # Dosyaya kaydet
            file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(result["answer"])
            
            return f"Transkript dosyası başarıyla işlendi ({doc_count} parça).\n\n{result['answer']}\n\n---\nToplam işlem süresi: {elapsed_time:.2f} saniye\nİçerik '{file_name}' dosyasına kaydedildi."
        
        except ValueError:
            return "Geçersiz video sayısı! Lütfen geçerli bir sayı girin."
    except Exception as e:
        return f"Transkript işleme veya kitaplaştırma sırasında hata oluştu: {str(e)}"

def create_book_from_videos(series_name, num_episodes):
    global rag_system, system_initialized
    if not system_initialized:
        return "Önce sistemi başlatmalısınız!"
    
    try:
        num_eps = int(num_episodes)
        if num_eps <= 0:
            return "Video sayısı sıfırdan büyük olmalıdır."
            
        prompt = f"""'{series_name}' başlıklı {num_eps} bölümlük video serisini edebi bir dille kitaplaştır. 
        İçindekiler, tanımlar, bölümler ve alt başlıklar içeren tutarlı, bütünlüklü ve tekrarsız bir kitap formatında düzenle."""
        
        start_time = time.time()
        result = rag_system.query(prompt)
        elapsed_time = time.time() - start_time
        
        # Dosyaya kaydet
        file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(result["answer"])
        
        return f"{result['answer']}\n\n---\nİşlem süresi: {elapsed_time:.2f} saniye\nİçerik '{file_name}' dosyasına kaydedildi."
    except ValueError:
        return "Geçersiz video sayısı! Lütfen geçerli bir sayı girin."
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
                dir_browse = gr.Button("Klasör Seç")
                dir_button = gr.Button("Dizini İşle")
            with gr.Column():
                file_input = gr.Textbox(label="Tek Dosya Yolu")
                file_browse = gr.Button("Dosya Seç")
                file_button = gr.Button("Dosyayı İşle")
        process_output = gr.Textbox(label="İşlem Sonucu")
        
        # Klasör seçme düğmesine tıklandığında çalışacak fonksiyon
        dir_browse.click(browse_directory, inputs=[], outputs=[dir_input])
        
        # Dosya seçme düğmesine tıklandığında çalışacak fonksiyon
        file_browse.click(browse_file, inputs=[], outputs=[file_input])
        
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
        
        series_name = gr.Textbox(label="Video Serisi Adı")
        num_episodes = gr.Number(label="Video Sayısı", minimum=1, step=1, value=1)
        
        gr.Markdown("### Mevcut Verilerle Kitaplaştırma")
        book_button = gr.Button("Mevcut Verilerle Kitaplaştır")
        
        gr.Markdown("### Transkript Klasöründen Kitaplaştırma")
        trans_dir_input = gr.Textbox(label="Transkript Klasörü Yolu")
        trans_dir_browse = gr.Button("Transkript Klasörü Seç")
        trans_dir_process = gr.Button("Klasörü İşle ve Kitaplaştır")
        
        gr.Markdown("### Transkript Dosyasından Kitaplaştırma")
        trans_file_input = gr.Textbox(label="Transkript Dosyası Yolu")
        trans_file_browse = gr.Button("Transkript Dosyası Seç")
        trans_file_process = gr.Button("Dosyayı İşle ve Kitaplaştır")
        
        book_output = gr.Markdown(label="Oluşturulan Kitap")
        
        # Transkript klasörü ve dosyası seçme
        trans_dir_browse.click(browse_transcript_directory, inputs=[], outputs=[trans_dir_input])
        trans_file_browse.click(browse_transcript_file, inputs=[], outputs=[trans_file_input])
        
        # Kitaplaştırma işlemleri
        book_button.click(create_book_from_videos, inputs=[series_name, num_episodes], outputs=[book_output])
        trans_dir_process.click(process_transcripts_directory, inputs=[trans_dir_input, series_name, num_episodes], outputs=[book_output])
        trans_file_process.click(process_transcript_file, inputs=[trans_file_input, series_name, num_episodes], outputs=[book_output])

if __name__ == "__main__":
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860)