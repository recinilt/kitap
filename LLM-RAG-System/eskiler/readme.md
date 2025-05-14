# README.md
# Geliştirilmiş Kitaplaştırma ve İçerik Analiz Sistemi

Bu sistem, video transkriptlerini ve metin içeriklerini yüksek kaliteli kitaplara dönüştüren, yapay zeka destekli bir çözümdür.

## Özellikler

- **İçerik Analizi:** Metinleri otomatik analiz ederek optimal kitap yapısı oluşturma
- **Akıllı Bölümleme:** Büyük içerikleri otomatik olarak anlamlı parçalara ayırıp işleme
- **YouTube Entegrasyonu:** YouTube videolarından otomatik transkript indirme ve kitaplaştırma
- **RAG (Retrieval Augmented Generation):** İlgili içerikleri vektör tabanlı benzerlik aramasıyla tespit etme
- **Kitap Yapısı Optimizasyonu:** İçerik boyutuna göre otomatik bölüm, alt bölüm ve sayfa sayısı ayarlama
- **Tutarlı İçerik:** Kapak, içindekiler, önsöz, ana bölümler, sonuç ve kavram dizini ile eksiksiz kitap formatı
- **Türkçe İçerik Desteği:** Türkçe içerikler için optimize edilmiş işlemler ve analiz

## Kullanım

1. Sistemi başlatın:
   ```
   python app.py
   ```

2. Web tarayıcınızda `http://127.0.0.1:7860` adresine gidin

3. Kullanım seçenekleri:
   - **Sistem Başlatma:** İlk olarak LLM ve vektör veritabanını yükleyin
   - **Doküman İşleme:** Transkript ve metin dosyalarını yükleyin veya işleyin
   - **Video Kitaplaştırma:** YouTube linklerinden veya mevcut transkriptlerden kitap oluşturun
   - **Sorgu & Özet:** Belirli konularda sorgu yapın veya özetler oluşturun

## Sistem Bileşenleri

- `app.py`: Ana uygulama başlatma dosyası
- `app_integration.py`: Gradio arayüzü ve uygulama entegrasyonu
- `book_generation_service.py`: Kitap oluşturma ve işleme hizmeti
- `content_processor.py`: İçerik analizi ve işleme araçları
- `enhanced_book_creator.py`: Gelişmiş kitap oluşturma sistemi
- `rag_system.py`: Retrieval Augmented Generation sistemi
- `vector_store.py`: Vektör veritabanı ve gömme (embedding) işlemleri
- `document_processor.py`: Belge işleme ve bölümleme
- `language_model.py`: Yerel dil modeli entegrasyonu

## Teknik Özellikler

- **Dil Modeli:** İşlemler için HuggingFace modelleri (varsayılan: Mistral-7B-Instruct-v0.2)
- **Vektör Veritabanı:** FAISS ve Chroma DB ile hızlı benzerlik araması
- **Gömme (Embedding):** Sentence-transformers/all-MiniLM-L6-v2 modeli
- **Arayüz:** Gradio ile kullanıcı dostu web arayüzü
- **Çok İş Parçacıklı İşleme:** Büyük içerikler için ThreadPoolExecutor ile paralel işleme
- **İçerik Analizi:** NLTK ve özel algoritmalarla metin analizi ve yapılandırma

## Büyük İçerikler İçin Özellikler

Sistem, içerik boyutunu otomatik olarak algılar ve uygun stratejiyi belirler:

- **Küçük İçerikler (< 1.000 kelime):** Standart işleme
- **Orta Boy İçerikler (1.000-5.000 kelime):** Temel bölümleme
- **Büyük İçerikler (5.000-20.000 kelime):** Akıllı bölümleme ve paralel işleme
- **Çok Büyük İçerikler (> 20.000 kelime):** İleri düzey bölümleme, paralel işleme ve bellek yönetimi

## Kurulum

1. Gerekli Python paketlerini yükleyin:
   ```
   pip install -r requirements.txt
   ```

2. NLTK verilerini indirin:
   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('stopwords')
   ```

3. Sistemi başlatın:
   ```
   python app.py
   ```

## Geliştirme ve Özelleştirme

- **Dil Modeli Değiştirme:** `language_model.py` dosyasında `model_name` parametresini değiştirin
- **Belge Bölümleme Ayarları:** `document_processor.py` dosyasında `chunk_size` ve `chunk_overlap` parametrelerini ayarlayın
- **Özel İstemler (Prompts):** Kullanıcı arayüzünden istemleri (prompts) özelleştirebilirsiniz

## Teknik Katkılar

Bu proje, LangChain, HuggingFace Transformers, FAISS, Chroma DB ve diğer açık kaynaklı kütüphaneleri kullanmaktadır.