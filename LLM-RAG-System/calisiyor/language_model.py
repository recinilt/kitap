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
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto"
            )

            text_gen = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                #max_length=1024,
                max_new_tokens=1024,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1
            )

            self.llm = HuggingFacePipeline(pipeline=text_gen)
            print("[SUCCESS] Model başarıyla yüklendi.")
            return self.llm

        except Exception as e:
            print(f"[ERROR] Model yüklenemedi: {e}")
            raise e
