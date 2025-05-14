# app.py (Yeni Versiyon)
import os
import sys
import gradio as gr
from rag_system import RAGSystem
from app_integration import AppIntegration

# Global değişkenler
rag_system = RAGSystem()
app = AppIntegration(rag_system)

# Gradio arayüzünü oluştur ve başlat
def main():
    demo = app.create_gradio_interface()
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860)

if __name__ == "__main__":
    main()