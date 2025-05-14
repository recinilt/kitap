# document_processor.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
import os

class DocumentProcessor:
    def __init__(self, chunk_size=512, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
    
    def load_and_split_documents(self, file_path):
        """Tek bir dosyayı yükler ve parçalara ayırır"""
        if os.path.isfile(file_path):
            loader = TextLoader(file_path, encoding="utf-8")
            documents = loader.load()
            split_docs = self.text_splitter.split_documents(documents)
            return split_docs
        else:
            raise FileNotFoundError(f"{file_path} bulunamadı")
    
    def load_and_split_directory(self, directory_path, glob="**/*.txt"):
        """Dizindeki tüm .txt dosyalarını yükler ve parçalara ayırır"""
        if os.path.isdir(directory_path):
            loader = DirectoryLoader(directory_path, glob=glob, loader_cls=TextLoader)
            documents = loader.load()
            split_docs = self.text_splitter.split_documents(documents)
            return split_docs
        else:
            raise FileNotFoundError(f"{directory_path} bulunamadı")