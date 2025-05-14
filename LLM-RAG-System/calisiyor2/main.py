# main.py (güncellenmiş)
import os
import time
from rag_system import RAGSystem
from book_generator import generate_full_book

def main():
    # RAG sistemini başlat
    print("RAG sistemi başlatılıyor...")
    rag_system = RAGSystem()

    while True:
        print("\n=== LLM+RAG+FAISS Sistemi ===")
        print("1. Sistemi başlat")
        print("2. Doküman dizini işle")
        print("3. Tek dosya işle")
        print("4. Sorgu yap / Özet oluştur")
        print("5. Video transkriptlerini kitaplaştır")
        print("6. Çıkış")
        print("7. Bölüm bölüm tam kitap oluştur")

        choice = input("Seçiminiz (1-7): ")

        if choice == "1":
            rag_system.initialize()
            print("Sistem başlatıldı.")

        elif choice == "2":
            directory = input("İşlenecek dokümanların bulunduğu dizini girin: ")
            if os.path.isdir(directory):
                try:
                    start_time = time.time()
                    doc_count = rag_system.process_documents(directory)
                    elapsed_time = time.time() - start_time
                    print(f"{doc_count} doküman parçası başarıyla işlendi. ({elapsed_time:.2f} saniye)")
                except Exception as e:
                    print(f"Hata: {e}")
            else:
                print("Dizin bulunamadı!")

        elif choice == "3":
            file_path = input("İşlenecek dosyanın yolunu girin: ")
            if os.path.isfile(file_path):
                try:
                    start_time = time.time()
                    doc_count = rag_system.process_single_document(file_path)
                    elapsed_time = time.time() - start_time
                    print(f"{doc_count} doküman parçası başarıyla işlendi. ({elapsed_time:.2f} saniye)")
                except Exception as e:
                    print(f"Hata: {e}")
            else:
                print("Dosya bulunamadı!")

        elif choice == "4":
            if not hasattr(rag_system, 'qa_chain') or rag_system.qa_chain is None:
                print("Önce sistemi başlatmalısınız (Seçenek 1)")
                continue

            query = input("Sorgunuzu girin (veya özet oluşturmak istediğiniz kitabın başlığını): ")
            try:
                start_time = time.time()
                result = rag_system.query(query)
                elapsed_time = time.time() - start_time

                print("\n=== YANIT ===")
                print(result["answer"])
                print(f"\nİşlem süresi: {elapsed_time:.2f} saniye")

                print("\n=== KAYNAK BELGELER ===")
                for i, doc in enumerate(result["source_documents"][:3]):
                    print(f"Belge {i+1}: {doc.metadata.get('source', 'Bilinmeyen')} (İlk 100 karakter):")
                    print(f"{doc.page_content[:100]}...\n")

            except Exception as e:
                print(f"Hata: {e}")

        elif choice == "5":
            print("Bu seçenek GUI üzerinden çalıştırılmalıdır.")

        elif choice == "6":
            print("Program sonlandırılıyor...")
            break

        elif choice == "7":
            series_name = input("Kitap başlığı: ")
            file_path = input("Özet alınacak dosya yolu: ")

            with open(file_path, "r", encoding="utf-8") as f:
                summary_text = f.read()

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

            full_text = generate_full_book(rag_system, series_name, summary_text, sections)

            out_file = f"{series_name.replace(' ', '_')}_tam_kitap.txt"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(full_text)

            print(f"Kitap başarıyla oluşturuldu: {out_file}")

if __name__ == "__main__":
    main()