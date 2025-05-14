# language_model.py
from langchain_community.llms import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

class LanguageModel:
    def __init__(self, model_name="tiiuae/falcon-rw-1b", device="cuda" if torch.cuda.is_available() else "cpu"):
        self.model_name = model_name
        self.device = device
        self.tokenizer = None
        self.model = None
        self.llm = None

    def load_quantized_model(self):
        """Küçük, hafif bir model yükler ve LLM olarak döner"""
        try:
            print(f"[INFO] Model yükleniyor: {self.model_name} ({self.device})")

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # 8-bit quantization ekleyebilirsiniz (daha az RAM kullanır)
            model_loading_params = {
                "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
                "device_map": "auto"
            }
            
            # GPU belleği yeterliyse 8-bit quantization ekleyebilirsiniz
            # Eğer GPU belleği 6GB ise bu özelliği açabilirsiniz
            if torch.cuda.is_available() and torch.cuda.get_device_properties(0).total_memory > 6 * 1024 * 1024 * 1024:
                model_loading_params["load_in_8bit"] = True
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_loading_params
            )

            # Tokenizer ayarlamaları
            if not self.tokenizer.pad_token:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Bağlam penceresini 2048'den 4096'ya çıkarma (model destekliyorsa)
            try:
                max_model_length = self.model.config.max_position_embeddings
                print(f"[INFO] Model maksimum bağlam penceresi: {max_model_length} token")
                max_length = min(4096, max_model_length)  # 4096 veya model limitinin düşük olanını kullan
            except:
                max_length = 2048  # Varsayılan değer
            
            text_gen = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_length=max_length,  # Toplam maksimum uzunluk
                max_new_tokens=2048,   # Üretilecek maksimum yeni token sayısı
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.pad_token_id
            )

            self.llm = HuggingFacePipeline(pipeline=text_gen)
            print("[SUCCESS] Model başarıyla yüklendi.")
            return self.llm

        except Exception as e:
            print(f"[ERROR] Model yüklenemedi: {e}")
            raise e