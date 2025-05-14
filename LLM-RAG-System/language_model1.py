# language_model.py
from langchain_community.llms import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

class LanguageModel:
    def __init__(self, model_name="TheBloke/Mistral-7B-Instruct-v0.2-GPTQ", device="cuda:0"):
        self.model_name = model_name
        self.device = device
        self.tokenizer = None
        self.model = None
        self.llm = None
    
    def load_quantized_model(self):
        """GPTQ formatında quantized model yükler - Bitsandbytes'ı kullanmadan"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="auto",
                trust_remote_code=True
            )
            
            # Text generation pipeline
            text_pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_length=4096,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.15
            )
            
            self.llm = HuggingFacePipeline(pipeline=text_pipeline)
            return self.llm
        except Exception as e:
            print(f"Model yükleme hatası: {e}")
            print("Alternatif model yükleniyor...")
            #self.model_name = "tiiuae/falcon-rw-1b"  # Fallback
            
            # Alternatif, daha küçük bir model yükle
            self.model_name = "TheBloke/Mistral-7B-Instruct-v0.2-GPTQ"
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="auto",
                trust_remote_code=True
            )
            
            text_pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_length=4096,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.15
            )
            
            self.llm = HuggingFacePipeline(pipeline=text_pipeline)
            return self.llm