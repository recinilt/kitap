# very_simple_app.py
# En basit haliyle kitaplaştırma uygulaması, tkinter kullanır
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

class SimpleBookCreator:
    """Çok basit kitap oluşturucu - hiçbir karmaşık bağımlılık yok"""
    
    def __init__(self):
        """İşlemci sınıfını başlatır"""
        self.temp_files = []
    
    def preprocess_transcript(self, text):
        """Transkript metnini ön işlemden geçirerek temizler"""
        import re
        
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
    
    def create_book(self, content, title, num_chapters=5):
        """Basit kitap oluşturma"""
        import re
        
        # İçeriği temizle
        content = self.preprocess_transcript(content)
        
        # Metni yaklaşık eşit uzunlukta bölümlere böl
        paragraphs = re.split(r'\n\s*\n', content)
        total_paragraphs = len(paragraphs)
        
        # Bölüm başlıklarını belirleme
        chapters = []
        if total_paragraphs <= num_chapters:
            # Çok az paragraf varsa, her biri bir bölüm olsun
            for i, para in enumerate(paragraphs):
                chapters.append(f"# Bölüm {i+1}\n\n{para}")
        else:
            # Paragrafları bölümlere dağıt
            paragraphs_per_chapter = total_paragraphs // num_chapters
            
            for i in range(num_chapters):
                start_idx = i * paragraphs_per_chapter
                end_idx = start_idx + paragraphs_per_chapter if i < num_chapters - 1 else total_paragraphs
                
                chapter_content = '\n\n'.join(paragraphs[start_idx:end_idx])
                chapters.append(f"# Bölüm {i+1}\n\n{chapter_content}")
        
        # İçindekiler oluştur
        toc = "# İçindekiler\n\n"
        for i in range(num_chapters):
            toc += f"Bölüm {i+1} ... {i*10+1}\n"
        
        # Kitap başlangıç kısmı
        front_matter = f"""# {title}

## {num_chapters} Bölümlük Kapsamlı İnceleme

{toc}

# Önsöz

Bu kitap, {title} konusunu ele alan kapsamlı bir çalışmadır. Kitap, toplam {num_chapters} bölümden oluşmakta ve konunun farklı yönlerini incelemektedir.

# Giriş

{title} konusu, önemli bir çalışma alanıdır. Bu kitapta, konunun çeşitli yönlerini ele alacağız.

"""
        # Kitap sonu
        back_matter = f"""
# Sonuç ve Değerlendirme

Bu kitapta, {title} konusu detaylı olarak incelenmiştir. İncelenen konular ışığında, bir dizi çıkarım yapılabilir.
"""
        
        # Tüm kitabı birleştir
        full_book = front_matter + "\n\n" + "\n\n".join(chapters) + "\n\n" + back_matter
        
        return full_book

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

class BookCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Basit Kitaplaştırma Uygulaması")
        self.root.geometry("800x600")
        
        self.book_creator = SimpleBookCreator()
        
        # Ana frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Başlık
        ttk.Label(main_frame, text="Basit Kitaplaştırma Uygulaması", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Kitap bilgileri
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(form_frame, text="Video Serisi Adı:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.series_name = ttk.Entry(form_frame, width=40)
        self.series_name.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(form_frame, text="Bölüm Sayısı:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.num_chapters = ttk.Spinbox(form_frame, from_=1, to=20, width=5)
        self.num_chapters.set("5")
        self.num_chapters.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # YouTube sekmesi
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        youtube_frame = ttk.Frame(notebook)
        file_frame = ttk.Frame(notebook)
        
        notebook.add(youtube_frame, text="YouTube Linklerinden")
        notebook.add(file_frame, text="Transkript Dosyalarından")
        
        # YouTube linki girişi
        ttk.Label(youtube_frame, text="YouTube Linkleri (Her satıra bir link):").pack(anchor=tk.W, pady=5)
        self.youtube_links = scrolledtext.ScrolledText(youtube_frame, height=10)
        self.youtube_links.pack(fill=tk.BOTH, expand=True, pady=5)
        
        youtube_button = ttk.Button(youtube_frame, text="YouTube Linklerini İşle ve Kitaplaştır", command=self.process_youtube_links)
        youtube_button.pack(pady=10)
        
        # Dosya seçimi
        ttk.Label(file_frame, text="Transkript Dosyaları:").pack(anchor=tk.W, pady=5)
        
        file_button_frame = ttk.Frame(file_frame)
        file_button_frame.pack(fill=tk.X, pady=5)
        
        self.selected_files_label = ttk.Label(file_button_frame, text="Henüz dosya seçilmedi")
        self.selected_files_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        select_files_button = ttk.Button(file_button_frame, text="Dosya Seç", command=self.select_files)
        select_files_button.pack(side=tk.RIGHT)
        
        process_files_button = ttk.Button(file_frame, text="Dosyaları İşle ve Kitaplaştır", command=self.process_files)
        process_files_button.pack(pady=10)
        
        # Çıktı alanı
        ttk.Label(main_frame, text="Oluşturulan Kitap İçeriği:").pack(anchor=tk.W, pady=5)
        self.output_text = scrolledtext.ScrolledText(main_frame, height=15)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Durum çubuğu
        self.status_var = tk.StringVar()
        self.status_var.set("Hazır")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # İlerleme çubuğu
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Kaydet butonu
        save_button = ttk.Button(main_frame, text="Kitabı Kaydet", command=self.save_book)
        save_button.pack(pady=10)
        
        # Dosya değişkenleri
        self.selected_files = []
        self.current_book_content = ""
        
    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Transkript Dosyalarını Seç",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if files:
            self.selected_files = files
            if len(files) == 1:
                self.selected_files_label.config(text=f"1 dosya seçildi: {os.path.basename(files[0])}")
            else:
                self.selected_files_label.config(text=f"{len(files)} dosya seçildi")
        else:
            self.selected_files = []
            self.selected_files_label.config(text="Henüz dosya seçilmedi")
    
    def process_youtube_links(self):
        """YouTube linklerini işleyip kitaplaştırır"""
        links_text = self.youtube_links.get("1.0", tk.END).strip()
        series_name = self.series_name.get().strip()
        
        if not links_text:
            messagebox.showerror("Hata", "YouTube linki girilmedi!")
            return
        
        if not series_name:
            messagebox.showerror("Hata", "Video serisi adı girilmedi!")
            return
        
        # Linkleri satır satır ayır
        links = [link.strip() for link in links_text.split('\n') if link.strip()]
        
        if not links:
            messagebox.showerror("Hata", "Geçerli bir YouTube linki bulunamadı!")
            return
        
        try:
            self.status_var.set("Transkriptler indiriliyor...")
            self.progress['value'] = 10
            self.root.update_idletasks()
            
            # Transkriptleri indir
            temp_files = []
            all_content = ""
            download_log = []
            
            for i, link in enumerate(links):
                self.status_var.set(f"Transkript indiriliyor: {link}")
                self.progress['value'] = 10 + (i / len(links) * 30)
                self.root.update_idletasks()
                
                # URL'den transkripti indir
                file_path, log_message = download_transcript_from_url(link)
                download_log.append(log_message)
                
                if file_path:
                    temp_files.append(file_path)
                    
                    # Dosyayı oku
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # İçeriği ön işlemden geçir ve topla
                    processed_content = self.book_creator.preprocess_transcript(content)
                    all_content += processed_content + "\n\n"
            
            if not temp_files:
                error_message = "Hiçbir transkript indirilemedi.\n\n" + "\n".join(download_log)
                messagebox.showerror("Hata", error_message)
                return
            
            self.status_var.set("Kitap oluşturuluyor...")
            self.progress['value'] = 50
            self.root.update_idletasks()
            
            # Bölüm sayısını al
            try:
                num_chapters = int(self.num_chapters.get())
                if num_chapters <= 0:
                    num_chapters = len(links)  # Link sayısı kadar bölüm
            except:
                num_chapters = len(links)  # Link sayısı kadar bölüm
            
            # Kitap oluştur
            book_content = self.book_creator.create_book(all_content, series_name, num_chapters)
            
            self.status_var.set("Kitap oluşturuldu")
            self.progress['value'] = 100
            self.root.update_idletasks()
            
            # Sonucu göster
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, book_content)
            
            # Güncel kitap içeriğini sakla
            self.current_book_content = book_content
            
            # İndirme günlüğünü kaydet
            log_filename = f"{series_name.replace(' ', '_')}_indirme_gunlugu.txt"
            with open(log_filename, "w", encoding="utf-8") as f:
                f.write("\n".join(download_log))
            
            messagebox.showinfo("Başarılı", f"Kitap oluşturuldu! İndirme günlüğü '{log_filename}' dosyasına kaydedildi.")
            
        except Exception as e:
            self.status_var.set("Hata oluştu")
            self.progress['value'] = 0
            messagebox.showerror("Hata", f"İşlem sırasında hata oluştu: {str(e)}")
    
    def process_files(self):
        """Transkript dosyalarını işleyip kitaplaştırır"""
        if not self.selected_files:
            messagebox.showerror("Hata", "Önce dosya seçmelisiniz!")
            return
        
        series_name = self.series_name.get().strip()
        if not series_name:
            messagebox.showerror("Hata", "Video serisi adı girilmedi!")
            return
        
        try:
            self.status_var.set("Dosyalar işleniyor...")
            self.progress['value'] = 10
            self.root.update_idletasks()
            
            # Dosyaları oku
            all_content = ""
            
            for i, file_path in enumerate(self.selected_files):
                self.status_var.set(f"Dosya işleniyor: {os.path.basename(file_path)}")
                self.progress['value'] = 10 + (i / len(self.selected_files) * 30)
                self.root.update_idletasks()
                
                # Dosyayı oku
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # İçeriği ön işlemden geçir ve topla
                processed_content = self.book_creator.preprocess_transcript(content)
                all_content += processed_content + "\n\n"
            
            self.status_var.set("Kitap oluşturuluyor...")
            self.progress['value'] = 50
            self.root.update_idletasks()
            
            # Bölüm sayısını al
            try:
                num_chapters = int(self.num_chapters.get())
                if num_chapters <= 0:
                    num_chapters = len(self.selected_files)  # Dosya sayısı kadar bölüm
            except:
                num_chapters = len(self.selected_files)  # Dosya sayısı kadar bölüm
            
            # Kitap oluştur
            book_content = self.book_creator.create_book(all_content, series_name, num_chapters)
            
            self.status_var.set("Kitap oluşturuldu")
            self.progress['value'] = 100
            self.root.update_idletasks()
            
            # Sonucu göster
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, book_content)
            
            # Güncel kitap içeriğini sakla
            self.current_book_content = book_content
            
            messagebox.showinfo("Başarılı", "Kitap oluşturuldu!")
            
        except Exception as e:
            self.status_var.set("Hata oluştu")
            self.progress['value'] = 0
            messagebox.showerror("Hata", f"İşlem sırasında hata oluştu: {str(e)}")
    
    def save_book(self):
        """Kitabı dosyaya kaydeder"""
        if not self.current_book_content:
            messagebox.showerror("Hata", "Kaydedilecek kitap içeriği yok!")
            return
        
        series_name = self.series_name.get().strip()
        default_filename = f"{series_name.replace(' ', '_')}_kitap.txt" if series_name else "kitap.txt"
        
        file_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.current_book_content)
                
                self.status_var.set(f"Kitap '{file_path}' dosyasına kaydedildi")
                messagebox.showinfo("Başarılı", f"Kitap '{file_path}' dosyasına kaydedildi.")
            except Exception as e:
                messagebox.showerror("Hata", f"Dosyaya yazma hatası: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BookCreatorApp(root)
    root.mainloop()