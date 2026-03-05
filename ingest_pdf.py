import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_DIR = "data"
DB_PATH = "db_faiss"
EMBEDDING_MODEL = "nomic-embed-text"

def main():
    all_docs = []
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Folder '{DATA_DIR}' dibuat. Silakan masukkan file PDF ke dalamnya.")
        return

    for file in os.listdir(DATA_DIR):
        if file.endswith(".pdf"):
            path = os.path.join(DATA_DIR, file)
            print(f"Memproses PDF: {file}")
            loader = PyPDFLoader(path)
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = f"File PDF: {file}"
            all_docs.extend(docs)

    if not all_docs:
        print("Tidak ada file PDF ditemukan di folder data.")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = text_splitter.split_documents(all_docs)

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    if os.path.exists(DB_PATH):
        print("Menggabungkan dengan database yang ada...")
        db = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
        db.add_documents(split_docs)
    else:
        print("Membuat database baru...")
        db = FAISS.from_documents(split_docs, embeddings)

    db.save_local(DB_PATH)
    print("Ingest PDF selesai!")

if __name__ == "__main__":
    main()
