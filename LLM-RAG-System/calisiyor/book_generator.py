# book_generator.py dosyasına ekle
import os
from langchain.schema import Document

def process_txt_folder_and_generate_book(rag_system, folder_path, title, progress=None):
    """
    Belirtilen klasördeki tüm .txt dosyalarını işler ve sonra kitaplaştırır.
    - rag_system: initialize edilmiş RAGSystem nesnesi
    - folder_path: txt dosyalarının bulunduğu klasör
    - title: kitap başlığı
    - progress: Gradio progress callback (isteğe bağlı)
    """
    # 1. TXT dosyalarını al
    txt_files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    if not txt_files:
        raise ValueError("Klasörde hiç .txt dosyası bulunamadı.")

    full_text = ""
    processed_docs = 0
    for idx, filename in enumerate(txt_files):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            full_text += f"\n\n--- {filename} ---\n\n" + content
        try:
            if progress:
                progress(0.1 + idx / len(txt_files) * 0.4, desc=f"{filename} işleniyor...")
        except:
            pass

        # Dokümanı işle ve vektör veritabanına ekle
        try:
            # Dokümanı parçalara ayır
            docs = rag_system.document_processor.load_and_split_documents(file_path)
            # Vektör veritabanına ekle
            rag_system.vector_store.create_vector_store(docs)
            processed_docs += len(docs)
        except Exception as e:
            print(f"Hata: {file_path} işlenirken sorun oluştu: {str(e)}")
            # Alternatif olarak basit bir ekleme yap
            rag_system.vector_store.add_texts([content], [{"source": file_path}])
            processed_docs += 1

    # 2. Kitaplaştır
    if progress:
        progress(0.6, desc="Kitap hazırlanıyor...")
    full_book = generate_smart_book(rag_system, title, full_text)

    # 3. Kayıt
    output_file = os.path.join(folder_path, f"{title.replace(' ', '_')}_toplu_kitap.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_book)

    if progress:
        progress(1.0, desc="Tamamlandı.")

    return output_file, f"✅ {len(txt_files)} dosyadan kitap oluşturuldu: {output_file}"


def generate_full_book(rag_system, title, summary_text, sections):
    """
    Bölüm bölüm kitap oluşturan sistem.
    - rag_system: initialize edilmiş RAGSystem nesnesi
    - title: kitap başlığı (örneğin "İnsanın Sosyal Evrimi")
    - summary_text: tüm içeriğin kısa özeti (ilk 1000 karakter yeterli)
    - sections: ['Kapak', 'Önsöz', ...] gibi bölüm başlıkları listesi
    """
    full_book = f"Başlık: {title}\n\n"

    for i, section in enumerate(sections, 1):
        print(f"[+] Bölüm oluşturuluyor: {section}")

        prompt = f"""
'{title}' adlı serinin '{section}' başlığını edebi ve bilimsel bir dille yaz. 

İçerik özeti:
{summary_text[:1000]}...

Kurallar:
- Tamamen TÜRKÇE yaz.
- Uydurma bilgi verme, sadece içeriği yorumla ve dönüştür.
- Edebi dil kullan, ama akademik tutarlılığı koru.
- Bölüm başlığını açıkça yaz, alt başlıklar da kullan.
- Gerekiyorsa örneklerle zenginleştir.
- Bölüm uzunluğu bu başlığın önemine göre serbesttir.
"""

        try:
            result = rag_system.query(prompt)
            content = result["answer"]
        except Exception as e:
            content = f"[HATA] {section} bölümü oluşturulamadı: {e}"

        full_book += f"\n\n=== {section.upper()} ===\n\n" + content.strip() + "\n"

    return full_book


def generate_summary_book(rag_system, title, content):
    prompt = f"""
'{title}' başlığı altında aşağıdaki içeriğe dayanarak edebi ve bilimsel bir geniş özet hazırla:

{content[:3000]}...

Kurallar:
- Tamamen TÜRKÇE yaz.
- Edebi, akıcı ve anlam bütünlüğü olan bir özet üret.
- Başlık ve alt başlıklar kullan.
- Uydurma bilgi verme, sadece verilen içerikten anlam üret.
"""
    try:
        result = rag_system.query(prompt)
        return result["answer"]
    except Exception as e:
        return f"[HATA] Geniş özet oluşturulamadı: {e}"


def analyze_text_length(text):
    length = len(text)
    if length < 3000:
        return "short"
    elif length < 15000:
        return "medium"
    elif length < 60000:
        return "long"
    else:
        return "epic"


def suggest_section_titles(rag_system, text):
    try:
        prompt = f"İçeriğe göre 5 ila 10 adet edebi kitap bölümü başlığı öner.\n\nMetin:\n{text[:2000]}"
        result = rag_system.query(prompt)
        titles = [t.strip("-• ") for t in result["answer"].split("\n") if len(t.strip()) > 3]
        return titles if titles else ["Giriş", "Gelişme", "Sonuç"]
    except:
        return ["Giriş", "Gelişme", "Sonuç"]


def generate_smart_book(rag_system, title, content):
    length_class = analyze_text_length(content)
    print(f"[+] İçerik uzunluk sınıfı: {length_class}")

    if length_class == "short":
        print("[!] Kısa içerik: Geniş özet hazırlanıyor...")
        return generate_summary_book(rag_system, title, content)

    else:
        print("[!] İçerik yeterli: Tam kitap hazırlanıyor...")
        sections = suggest_section_titles(rag_system, content)
        return generate_full_book(rag_system, title, content, sections)