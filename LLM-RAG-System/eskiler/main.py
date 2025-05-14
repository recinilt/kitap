# main.py
import os
import time
from rag_system import RAGSystem

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
        
        choice = input("Seçiminiz (1-6): ")
        
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
                
                # Kaynak belgeleri göster
                print("\n=== KAYNAK BELGELER ===")
                for i, doc in enumerate(result["source_documents"][:3]):
                    print(f"Belge {i+1}: {doc.metadata.get('source', 'Bilinmeyen')} (İlk 100 karakter):")
                    print(f"{doc.page_content[:100]}...\n")
                
            except Exception as e:
                print(f"Hata: {e}")
                
        elif choice == "5":
            if not hasattr(rag_system, 'qa_chain') or rag_system.qa_chain is None:
                print("Önce sistemi başlatmalısınız (Seçenek 1)")
                continue
                
            series_name = input("Video serisi adını girin: ")
            num_episodes = input("Video sayısını girin: ")
            
            try:
                num_episodes = int(num_episodes)
                prompt = f"""'{series_name}' başlıklı {num_episodes} bölümlük video serisini edebi bir dille kitaplaştır. 
                İçindekiler, tanımlar, bölümler ve alt başlıklar içeren tutarlı, bütünlüklü ve tekrarsız bir kitap formatında düzenle."""
                
                start_time = time.time()
                result = rag_system.query(prompt)
                elapsed_time = time.time() - start_time
                
                print("\n=== KİTAPLAŞTIRILMIŞ İÇERİK ===")
                print(result["answer"])
                print(f"\nİşlem süresi: {elapsed_time:.2f} saniye")
                
                save_option = input("Bu içeriği kaydetmek ister misiniz? (E/H): ")
                if save_option.lower() == 'e':
                    file_name = f"{series_name.replace(' ', '_')}_kitap.txt"
                    with open(file_name, "w", encoding="utf-8") as f:
                        f.write(result["answer"])
                    print(f"İçerik '{file_name}' dosyasına kaydedildi.")
                
            except ValueError:
                print("Geçersiz video sayısı!")
            except Exception as e:
                print(f"Hata: {e}")
                
        elif choice == "6":
            print("Program sonlandırılıyor...")
            break
            
        else:
            print("Geçersiz seçenek! Lütfen 1-6 arasında bir seçenek girin.")

if __name__ == "__main__":
    main()