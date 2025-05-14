# app_simplified.py
# Basitleştirilmiş uygulama
import os
import sys
import gradio as gr
from simplified_rag_system import SimplifiedRAGSystem
from app_integration import AppIntegration

# Global değişkenler
rag_system = SimplifiedRAGSystem()
app = AppIntegration(rag_system)

# Gradio arayüzünü oluştur ve başlat
def main():
    demo = app.create_gradio_interface()
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860)

if __name__ == "__main__":
    main()