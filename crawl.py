import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# === KONFIGURASI ===
DAFTAR_URL = [
    "https://id.wikipedia.org/wiki/Kecerdasan_buatan",
    # Tambahkan URL lain di sini
]

DB_PATH = "db_faiss"
EMBEDDING_MODEL = "nomic-embed-text"
MAX_PAGES_TOTAL = 20

def get_text_from_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'lxml')
        
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
        
        text = soup.get_text(separator=' ', strip=True)
        return text
    except Exception as e:
        print(f"Gagal crawl {url}: {e}")
        return None

def main():
    allowed_domains = [urlparse(u).netloc for u in DAFTAR_URL]
    visited = set()
    to_visit = list(DAFTAR_URL)
    documents = []
    
    print(f"Memulai crawl dari {len(DAFTAR_URL)} website sumber...")

    while to_visit and len(visited) < MAX_PAGES_TOTAL:
        url = to_visit.pop(0)
        if url in visited: continue
            
        visited.add(url)
        text = get_text_from_url(url)
        
        if text:
            print(f"-> Mengambil konten: {url}")
            doc = Document(page_content=text, metadata={"source": url})
            documents.append(doc)
            
            try:
                soup = BeautifulSoup(requests.get(url, timeout=5, headers={'User-Agent':'Mozilla/5.0'}).content, 'lxml')
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    domain = urlparse(full_url).netloc
                    if domain in allowed_domains and full_url not in visited:
                        to_visit.append(full_url)
            except: pass

    if not documents:
        print("Tidak ada data yang di-crawl.")
        return

    print(f"Total halaman diambil: {len(documents)}. Memproses teks...")
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = text_splitter.split_documents(documents)
    
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    if not os.path.exists(DB_PATH): os.makedirs(DB_PATH)

    db = FAISS.from_documents(split_docs, embeddings)
    db.save_local(DB_PATH)
    print(f"Database disimpan di folder '{DB_PATH}'")

if __name__ == "__main__":
    main()
