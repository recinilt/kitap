@echo off
echo LLM+RAG+FAISS Edebi Icerik Uretim Sistemi Kurulum Scripti
echo --------------------------------------------------------

:: Python kontrolü
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python bulunamadi! Lutfen Python 3.10 veya ustunu yukleyin.
    exit /b 1
)

:: Sanal ortam oluşturma
echo Sanal ortam olusturuluyor...
python -m venv venv
call venv\Scripts\activate

:: Gereksinimlerin kurulumu
echo Gereksinimler yukleniyor...
pip install -U pip
pip install -r requirements.txt

echo Kurulum tamamlandi!
echo Sistemi baslatmak icin run.bat dosyasini calistirin.
pause