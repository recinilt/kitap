# content_processor.py
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter
import numpy as np

class ContentProcessor:
    """Metin içeriklerini işlemek, analiz etmek ve zenginleştirmek için gelişmiş araçlar sunar"""
    
    def __init__(self):
        """İşlemci sınıfını başlatır ve gerekli NLTK verilerini yükler"""
        # NLTK verilerini yüklemeyi dene
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        # Türkçe durak kelimeleri
        self.stopwords_tr = set(stopwords.words('turkish')) if 'turkish' in stopwords._fileids else set()
        # Özel Türkçe durak kelimeleri ekleme
        custom_stopwords = {"bir", "ve", "bu", "için", "ile", "da", "de", "ki", "mı", "mu", "mi", "dır", "dir", "çok", "ama", "fakat", "ancak", "şey", "olarak", "gibi", "kadar", "kez", "kere", "çünkü", "böylece", "dolayısıyla", "sonra", "önce", "ise", "ama", "lakin", "yani", "eğer", "şayet", "belki", "galiba", "sanırım", "sanki", "hatta", "üstelik", "ayrıca"}
        self.stopwords_tr.update(custom_stopwords)
    
    def preprocess_transcript(self, text):
        """Transkript metnini ön işlemden geçirerek temizler"""
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
    
    def extract_key_concepts(self, text, n=20):
        """Metinden anahtar kavramları çıkarır"""
        # Metni kelimelere ayır
        words = word_tokenize(text.lower())
        
        # Durak kelimeleri ve noktalama işaretlerini kaldır
        words = [word for word in words if word.isalnum() and word not in self.stopwords_tr and len(word) > 2]
        
        # Kelime frekanslarını hesapla
        word_freq = Counter(words)
        
        # En sık kullanılan kelimeleri döndür
        return word_freq.most_common(n)
    
    def calculate_readability(self, text):
        """Metnin okunabilirlik düzeyini hesaplar (Türkçe için uyarlanmış)"""
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        
        # Cümle ve kelime sayısı
        num_sentences = len(sentences)
        num_words = len(words)
        
        if num_sentences == 0 or num_words == 0:
            return {
                "sentence_count": 0,
                "word_count": 0,
                "avg_words_per_sentence": 0,
                "avg_syllables_per_word": 0,
                "readability_score": 0
            }
        
        # Hece sayısını tahmin et (Türkçe için basit yaklaşım)
        def count_syllables_tr(word):
            # Türkçe sesli harfler
            vowels = 'aeıioöuüAEIİOÖUÜ'
            
            # Kelime içindeki sesli harf sayısını say
            count = sum(1 for char in word if char in vowels)
            
            # En az 1 hece varsay
            return max(1, count)
        
        syllable_count = sum(count_syllables_tr(word) for word in words)
        
        # Ortalama istatistikler
        avg_words_per_sentence = num_words / num_sentences
        avg_syllables_per_word = syllable_count / num_words
        
        # Türkçe için uyarlanmış okunabilirlik skoru (ARI benzeri)
        readability_score = 4.71 * (syllable_count / num_words) + 0.5 * (num_words / num_sentences) - 21.43
        
        return {
            "sentence_count": num_sentences,
            "word_count": num_words,
            "avg_words_per_sentence": avg_words_per_sentence,
            "avg_syllables_per_word": avg_syllables_per_word,
            "readability_score": readability_score
        }
    
    def assess_content_quality(self, text):
        """İçerik kalitesini değerlendirir"""
        # Temel istatistikler
        readability = self.calculate_readability(text)
        
        # Tekrar oranını hesapla
        words = word_tokenize(text.lower())
        word_count = len(words)
        unique_words = len(set(words))
        
        if word_count == 0:
            repetition_rate = 0
        else:
            repetition_rate = 1 - (unique_words / word_count)
        
        # İçerik yoğunluğu (anahtar kelimeler / toplam kelimeler)
        key_concepts = self.extract_key_concepts(text, n=min(50, word_count // 20 if word_count > 0 else 1))
        key_concept_count = sum(freq for _, freq in key_concepts)
        
        if word_count == 0:
            content_density = 0
        else:
            content_density = key_concept_count / word_count
        
        return {
            "readability": readability,
            "repetition_rate": repetition_rate,
            "content_density": content_density,
            "unique_word_ratio": unique_words / word_count if word_count > 0 else 0,
            "quality_score": (
                (1 - repetition_rate) * 0.4 +  # Düşük tekrar oranı daha iyi
                content_density * 0.3 +  # Yüksek içerik yoğunluğu daha iyi
                (min(readability["avg_words_per_sentence"], 25) / 25) * 0.3  # Optimal cümle uzunluğu
            ) * 10  # 0-10 arası puan
        }
    
    def generate_structure_from_content(self, text, min_chapters=3, max_chapters=15):
        """Metin içeriğine göre otomatik kitap yapısı oluşturur"""
        # Metni cümlelere ayır
        sentences = sent_tokenize(text)
        
        # Çok kısa metinler için basit yapı
        if len(sentences) < 20:
            return self._generate_simple_structure(text, min_chapters)
        
        # Tematik analiz - anahtar kelimeleri grupla
        key_concepts = self.extract_key_concepts(text, n=min(100, len(sentences) // 5))
        
        # Cümleleri anahtar kelimelerle eşleştir
        sentence_topics = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            topics = []
            
            for word, _ in key_concepts:
                if word in sentence_lower:
                    topics.append(word)
            
            sentence_topics.append((sentence, topics))
        
        # Konuları gruplayarak bölümleri belirle
        topic_groups = {}
        for word, _ in key_concepts[:20]:  # En sık kullanılan 20 kelimeyi kullan
            topic_sentences = []
            for sentence, topics in sentence_topics:
                if word in topics:
                    topic_sentences.append(sentence)
            
            if topic_sentences:
                # Benzersiz grup adı oluştur
                group_key = word
                counter = 1
                while group_key in topic_groups and counter < 10:
                    group_key = f"{word}_{counter}"
                    counter += 1
                
                topic_groups[group_key] = topic_sentences
        
        # Konu gruplarını birleştir (çok benzer grupları tek grup yap)
        merged_groups = {}
        used_keys = set()
        
        sorted_groups = sorted(topic_groups.items(), key=lambda x: len(x[1]), reverse=True)
        
        for key1, sentences1 in sorted_groups:
            if key1 in used_keys:
                continue
                
            merged_key = key1
            merged_sentences = set(sentences1)
            
            # Benzer grupları bul
            for key2, sentences2 in sorted_groups:
                if key2 != key1 and key2 not in used_keys:
                    # Gruplarda ortak cümle oranı
                    common_sentences = set(sentences1) & set(sentences2)
                    similarity_ratio = len(common_sentences) / min(len(sentences1), len(sentences2))
                    
                    # Benzerlik oranı yüksekse birleştir
                    if similarity_ratio > 0.5:
                        merged_sentences.update(sentences2)
                        used_keys.add(key2)
            
            used_keys.add(key1)
            merged_groups[merged_key] = list(merged_sentences)
        
        # Grubun içerik yoğunluğuna göre sırala
        sorted_merged_groups = sorted(merged_groups.items(), 
                                     key=lambda x: len(x[1]), 
                                     reverse=True)
        
        # Bölüm ve alt bölüm yapısı oluştur
        chapter_count = min(max(min_chapters, len(sorted_merged_groups)), max_chapters)
        
        chapters = []
        for i in range(min(chapter_count, len(sorted_merged_groups))):
            key, sentences = sorted_merged_groups[i]
            
            # Bölüm başlığı oluştur
            clean_key = key.replace("_", " ").title()
            chapter_title = f"Bölüm {i+1}: {clean_key}"
            
            # Alt bölümler için cümleleri grupla
            if len(sentences) < 5:
                subchapters = [{"title": f"{clean_key} Detayları", "key_concepts": [key]}]
            else:
                # Cümleleri daha küçük gruplara böl
                subchapter_count = min(5, max(2, len(sentences) // 10))
                subchapters = []
                
                # Alt bölüm başlıkları için sözcük grupları bul
                sentence_text = " ".join(sentences)
                subconcepts = self.extract_key_concepts(sentence_text, n=subchapter_count*2)
                
                for j in range(subchapter_count):
                    if j < len(subconcepts):
                        subkey = subconcepts[j][0].title()
                        subchapters.append({
                            "title": f"{subkey}",
                            "key_concepts": [concept for concept, _ in subconcepts[j:j+2]]
                        })
            
            # Bölüm bilgilerini ekle
            chapter_info = {
                "title": chapter_title,
                "importance_level": 5 - min(4, i),  # İlk bölümler daha önemli
                "estimated_pages": max(5, min(50, len(sentences) // 5)),  # Her 5 cümle 1 sayfa varsay
                "subchapters": subchapters
            }
            
            chapters.append(chapter_info)
        
        # Metin analiz sonuçları
        readability = self.calculate_readability(text)
        quality = self.assess_content_quality(text)
        
        # Kitap metadatası
        book_structure = {
            "book_title": "İçerik Analizi Kitabı",  # Bu isim daha sonra değiştirilecek
            "book_subtitle": "Kapsamlı Bir İnceleme",
            "estimated_page_count": max(50, readability["word_count"] // 300),  # Her 300 kelime 1 sayfa varsay
            "chapters": chapters,
            "content_stats": {
                "readability": readability,
                "quality": quality
            }
        }
        
        return book_structure
    
    def _generate_simple_structure(self, text, min_chapters=3):
        """Kısa metinler için basit kitap yapısı oluşturur"""
        # Basit istatistikler
        readability = self.calculate_readability(text)
        word_count = readability["word_count"]
        
        # En az bölüm sayısına göre yapı oluştur
        chapters = []
        for i in range(min_chapters):
            if i == 0:
                chapter_title = "Giriş"
            elif i == min_chapters - 1:
                chapter_title = "Sonuç ve Değerlendirme"
            else:
                chapter_title = f"Bölüm {i}"
            
            chapters.append({
                "title": chapter_title,
                "importance_level": 3,
                "estimated_pages": max(3, word_count // (300 * min_chapters)),
                "subchapters": [
                    {
                        "title": f"{chapter_title} Detayları",
                        "key_concepts": ["Kavram 1", "Kavram 2"]
                    }
                ]
            })
        
        return {
            "book_title": "Kısa İçerik Analizi",
            "book_subtitle": "Özet İnceleme",
            "estimated_page_count": max(10, word_count // 300),
            "chapters": chapters
        }
    
    def generate_title_suggestions(self, text, count=5):
        """Metin içeriğine göre kitap başlığı önerileri üretir"""
        # Anahtar kavramları çıkar
        key_concepts = self.extract_key_concepts(text, n=10)
        
        # Cümleleri analiz et
        sentences = sent_tokenize(text)
        
        # İlk ve son cümleler genellikle önemlidir
        first_sentences = sentences[:min(3, len(sentences))]
        last_sentences = sentences[max(0, len(sentences)-3):]
        
        # Önemli cümleleri seç (anahtar kelimeleri içeren)
        important_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            importance = sum(1 for word, _ in key_concepts if word in sentence_lower)
            
            if importance >= 2:  # En az 2 anahtar kelime içeren cümleler
                important_sentences.append(sentence)
        
        # Öneriler listesi
        suggestions = []
        
        # Anahtar kelimelerden başlık oluştur
        for i in range(min(count, len(key_concepts))):
            word, _ = key_concepts[i]
            suggestions.append(f"{word.title()}: Kapsamlı Bir İnceleme")
        
        # Önemli cümlelerden çıkarım yap
        for sentence in important_sentences[:count]:
            # Cümleleri kısalt
            if len(sentence) > 60:
                shortened = sentence[:57] + "..."
                suggestions.append(shortened)
        
        # Önerileri benzersiz hale getir ve kısalt
        unique_suggestions = []
        for suggestion in suggestions:
            # Çok uzun başlıkları kısalt
            if len(suggestion) > 70:
                suggestion = suggestion[:67] + "..."
            
            if suggestion not in unique_suggestions:
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:count]
    
    def extract_questions_from_text(self, text, count=5):
        """Metin içeriğinden yanıtlanabilir sorular çıkarır"""
        # Cümleleri analiz et
        sentences = sent_tokenize(text)
        
        # Anahtar kavramları çıkar
        key_concepts = self.extract_key_concepts(text, n=10)
        key_words = [word for word, _ in key_concepts]
        
        # Soru ifadeleri için şablonlar
        question_templates = [
            "{}?",
            "{} nedir?",
            "{} nasıl {}?",
            "{} niçin önemlidir?",
            "{} neden {}?",
            "{} hangi {} ile ilişkilidir?",
            "{} nasıl gelişmiştir?",
            "{} hangi sonuçları doğurmuştur?"
        ]
        
        # Anahtar kelimelerden sorular oluştur
        questions = []
        
        # İlk olarak mevcut soru cümlelerini bul
        existing_questions = [s for s in sentences if s.strip().endswith("?")]
        
        # Mevcut soruları ekle
        for question in existing_questions[:count//2]:
            questions.append(question)
        
        # Anahtar kelimelerden yeni sorular oluştur
        for word in key_words:
            if len(questions) >= count:
                break
                
            # Rastgele şablon seç
            template = np.random.choice(question_templates)
            
            if "{}" in template:
                if template.count("{}") == 1:
                    question = template.format(word.title())
                elif template.count("{}") == 2:
                    # İkinci bir kelime bul
                    other_words = [w for w in key_words if w != word]
                    if other_words:
                        other_word = np.random.choice(other_words)
                        question = template.format(word.title(), other_word)
                    else:
                        question = template.format(word.title(), "gelişir")
            else:
                question = template
            
            if question not in questions:
                questions.append(question)
        
        return questions[:count]
    
    def generate_book_sections(self, text):
        """Kitap için standart bölümler oluşturur"""
        # Kitap yapısını analiz et
        structure = self.generate_structure_from_content(text)
        
        # Başlık önerileri
        title_suggestions = self.generate_title_suggestions(text)
        if title_suggestions:
            structure["book_title"] = title_suggestions[0]
        
        # Sorular oluştur
        questions = self.extract_questions_from_text(text)
        
        # Önsöz için metin
        preface = f"""# Önsöz

Bu kitap, {structure["book_title"]} konusunda kapsamlı bir inceleme sunmaktadır. Kitabın amacı, okuyucuya bu konuda derinlemesine bilgi sağlamak ve farklı bakış açıları sunmaktır.

Kitap içerisinde toplam {len(structure["chapters"])} ana bölüm bulunmaktadır. Bu bölümler, konunun farklı yönlerini ele almakta ve detaylı analizler sunmaktadır. Kitapta yanıt aranan temel sorular şunlardır:

"""
        
        for question in questions:
            preface += f"- {question}\n"
        
        # Giriş bölümü
        introduction = f"""# Giriş

{structure["book_title"]} konusu, günümüzde büyük önem taşımaktadır. Bu kitapta, konunun tarihsel gelişiminden güncel uygulamalarına kadar geniş bir yelpazede inceleme sunulacaktır.

## Genel Kavramsal Çerçeve

Kitap boyunca sık sık karşılaşacağınız temel kavramlar şunlardır:

"""
        
        # Anahtar kavramları ekle
        key_concepts = self.extract_key_concepts(text, n=10)
        for word, freq in key_concepts:
            introduction += f"- **{word.title()}**: Metinde {freq} kez geçmektedir ve konunun temel yapı taşlarından biridir.\n"
        
        introduction += "\n## Tarihsel Bağlam\n\nBu konu tarihsel olarak şu aşamalardan geçmiştir...\n"
        
        # Sonuç bölümü
        conclusion = f"""# Sonuç ve Değerlendirme

Bu kitapta, {structure["book_title"]} konusu detaylı olarak incelenmiştir. İncelenen konular ışığında şu çıkarımlara varmak mümkündür:

- Çıkarım 1
- Çıkarım 2
- Çıkarım 3

Gelecekte bu konunun daha da gelişeceği ve yeni araştırmalara konu olacağı öngörülmektedir.
"""
        
        # Kavram dizini
        index = "# Kavram Dizini\n\n"
        for word, freq in self.extract_key_concepts(text, n=30):
            index += f"**{word.title()}**: Metinde {freq} kez geçmektedir.\n"
        
        return {
            "structure": structure,
            "preface": preface,
            "introduction": introduction,
            "conclusion": conclusion,
            "index": index,
            "questions": questions,
            "title_suggestions": title_suggestions
        }