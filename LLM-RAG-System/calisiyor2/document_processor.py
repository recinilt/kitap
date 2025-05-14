# document_processor.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
import os

class DocumentProcessor:
    def __init__(self, chunk_size=384, chunk_overlap=50):
        self.chunk_size = chunk_size  # Daha küçük parçalar kullan (512 yerine 384)
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]  # Daha akıllı ayırıcılar
        )
    
    def load_and_split_documents(self, file_path):
        """Tek bir dosyayı yükler ve parçalara ayırır"""
        if os.path.isfile(file_path):
            try:
                loader = TextLoader(file_path, encoding="utf-8")
                documents = loader.load()
                split_docs = self.text_splitter.split_documents(documents)
                print(f"[INFO] {file_path} dosyası {len(split_docs)} parçaya bölündü.")
                return split_docs
            except UnicodeDecodeError:
                # UTF-8 ile açılamazsa latin-1 dene
                print(f"[WARNING] {file_path} UTF-8 ile açılamadı, latin-1 deneniyor...")
                loader = TextLoader(file_path, encoding="latin-1")
                documents = loader.load()
                split_docs = self.text_splitter.split_documents(documents)
                print(f"[INFO] {file_path} dosyası {len(split_docs)} parçaya bölündü.")
                return split_docs
        else:
            raise FileNotFoundError(f"{file_path} bulunamadı")
    
    def load_and_split_directory(self, directory_path, glob="**/*.txt"):
        """Dizindeki tüm .txt dosyalarını yükler ve parçalara ayırır"""
        if os.path.isdir(directory_path):
            loader = DirectoryLoader(directory_path, glob=glob, loader_cls=TextLoader)
            documents = loader.load()
            split_docs = self.text_splitter.split_documents(documents)
            print(f"[INFO] {directory_path} dizinindeki dosyalar toplam {len(split_docs)} parçaya bölündü.")
            return split_docs
        else:
            raise FileNotFoundError(f"{directory_path} bulunamadı")