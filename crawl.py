import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Konfigurasi
BASE_URL = "https://website-yang-ingin-di-crawl.com" # GANTI DENGAN URL ANDA
DB_PATH = "db_faiss"
EMBEDDING_MODEL = "nomic-embed-text"

def get_text_from_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Hapus script dan style
        for script in soup(["script", "style"]):
            script.extract()
        
        text = soup.get_text(separator=' ', strip=True)
        return text
    except Exception as e:
        print(f"Gagal crawl {url}: {e}")
        return None

def crawl_website(start_url, max_pages=50):
    visited = set()
    to_visit = [start_url]
    documents = []
    
    print(f"Memulai crawl dari {start_url}...")

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
            
        visited.add(url)
        text = get_text_from_url(url)
        
        if text:
            print(f"-> Mengambil konten: {url}")
            # Simpan ke Dokumen dengan Metadata URL
            doc = Document(page_content=text, metadata={"source": url})
            documents.append(doc)
            
            # Cari link baru (simple crawler)
            try:
                soup = BeautifulSoup(requests.get(url, timeout=5).content, 'lxml')
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    # Hanya crawl domain yang sama
                    if urlparse(full_url).netloc == urlparse(start_url).netloc:
                        if full_url not in visited:
                            to_visit.append(full_url)
            except:
                pass

    return documents

def main():
    # 1. Crawl Data
    raw_docs = crawl_website(BASE_URL)
    if not raw_docs:
        print("Tidak ada data yang di-crawl.")
        return

    # 2. Split Text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = text_splitter.split_documents(raw_docs)
    
    # 3. Buat Embeddings & Simpan ke FAISS
    print("Membuat vektor database (Ini mungkin butuh waktu)...")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    # Simpan ke disk
    db = FAISS.from_documents(split_docs, embeddings)
    db.save_local(DB_PATH)
    print(f"Database disimpan di folder '{DB_PATH}'")

if __name__ == "__main__":
    main()
