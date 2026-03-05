import os
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate

DB_PATH = "db_faiss"
LLM_MODEL = "phi3"
EMBEDDING_MODEL = "nomic-embed-text"

def main():
    print("Memuat database...")
    if not os.path.exists(DB_PATH):
        print("Error: Database belum ada. Jalankan crawl.py dulu!")
        return

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
    llm = ChatOllama(model=LLM_MODEL)
    
    print("\nBOT LOKAL SIAP! (Ketik 'exit' untuk keluar)")
    print("------------------------------------------")
    
    while True:
        try:
            query = input("\nAnda: ")
            if query.lower() in ['exit', 'quit', 'keluar']: break
            
            # Proses
            docs = vectorstore.similarity_search(query, k=3)
            context = "\n\n".join([doc.page_content for doc in docs])
            
            prompt = f"Konteks:\n{context}\n\nPertanyaan: {query}\n\nJawaban:"
            response = llm.invoke(prompt)
            
            print(f"\nBot: {response.content}")
            
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
