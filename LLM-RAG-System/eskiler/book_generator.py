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