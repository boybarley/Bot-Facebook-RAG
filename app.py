import os
import threading
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Konfigurasi
load_dotenv()
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
DB_PATH = "db_faiss"
LLM_MODEL = "phi3"
EMBEDDING_MODEL = "nomic-embed-text"

app = Flask(__name__)

# System Prompt Kustom
prompt_template = """
Anda adalah asisten cerdas yang berbasis data website dan PDF. Berikan jawaban yang akurat.
Gunakan konteks berikut untuk menjawab pertanyaan.

Konteks:
{context}

Pertanyaan: {question}

Jawaban (Jika informasi berasal dari website dan ada linknya, sertakan link URL di akhir jawaban. Jika tidak ada di database, arahkan pengguna untuk menghubungi admin secara manual):
"""

# Inisialisasi AI (Load sekali saat startup)
print("Memuat AI Model dan Database...")
try:
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
    
    llm = ChatOllama(model=LLM_MODEL)
    
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}), # Ambil 3 konteks teratas
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True # Penting untuk mengambil metadata URL
    )
    print("AI siap digunakan.")
except Exception as e:
    print(f"Error memuat AI: {e}")
    chain = None

def get_url_from_sources(source_docs):
    """Ekstrak URL unik dari metadata dokumen sumber."""
    urls = set()
    for doc in source_docs:
        source = doc.metadata.get('source')
        # Cek apakah source adalah URL (bukan nama file PDF)
        if source and source.startswith("http"):
            urls.add(source)
    return list(urls)

def send_message(recipient_id, text):
    """Kirim pesan balasan ke Facebook API."""
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    try:
        requests.post(url, json=data, headers=headers)
    except Exception as e:
        print(f"Error kirim pesan: {e}")

def process_message_thread(sender_id, message_text):
    """Proses AI di thread terpisah."""
    if not chain:
        send_message(sender_id, "Maaf, sistem AI sedang tidak siap.")
        return

    try:
        # Query ke RAG
        result = chain.invoke({"query": message_text})
        answer = result.get("result", "Maaf saya tidak mengerti.")
        
        # Logika Link Rekomendasi
        source_docs = result.get("source_documents", [])
        urls = get_url_from_sources(source_docs)
        
        if urls:
            # Tambahkan link referensi ke jawaban
            links_str = "\n\nReferensi:\n" + "\n".join(urls)
            final_response = answer + links_str
        else:
            final_response = answer

        send_message(sender_id, final_response)
        
    except Exception as e:
        print(f"Error AI: {e}")
        send_message(sender_id, "Terjadi kesalahan internal saat memproses pertanyaan Anda.")

# --- Routes ---

@app.route("/webhook", methods=["GET"])
def verify():
    """Verifikasi webhook oleh Facebook."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    """Menerima pesan masuk."""
    data = request.json
    
    if data.get("object") == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                sender_id = messaging_event["sender"]["id"]
                
                # Cek apakah ada pesan teks
                if "message" in messaging_event and "text" in messaging_event["message"]:
                    message_text = messaging_event["message"]["text"]
                    
                    # Jalankan proses AI di background thread
                    thread = threading.Thread(target=process_message_thread, args=(sender_id, message_text))
                    thread.start()
                    
                    # Langsung kirim 200 OK ke Facebook agar tidak timeout
                    return "OK", 200
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
