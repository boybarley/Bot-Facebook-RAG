import os
import threading
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
# Import khusus struktur baru
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate

# Konfigurasi
load_dotenv()
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
DB_PATH = "db_faiss"
LLM_MODEL = "phi3"
EMBEDDING_MODEL = "nomic-embed-text"

app = Flask(__name__)

# System Prompt
prompt_template = """
Anda adalah asisten cerdas. Jawab pertanyaan berdasarkan konteks berikut.
Konteks:
{context}

Pertanyaan: {question}

Jawaban (Jika ada link di konteks, sertakan di jawaban):
"""

# Inisialisasi AI Components
print("Memuat AI Model dan Database...")
vectorstore = None
llm = None
PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

try:
    if os.path.exists(DB_PATH):
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        vectorstore = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
        llm = ChatOllama(model=LLM_MODEL)
        print(">>> AI siap digunakan.")
    else:
        print(">>> Database tidak ditemukan. Jalankan crawl/ingest dulu.")
except Exception as e:
    print(f">>> Error memuat AI: {e}")

def get_url_from_sources(source_docs):
    urls = set()
    for doc in source_docs:
        source = doc.metadata.get('source')
        if source and source.startswith("http"):
            urls.add(source)
    return list(urls)

def send_message(recipient_id, text):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    data = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    try:
        requests.post(url, json=data, headers=headers)
    except Exception as e:
        print(f"Error kirim pesan: {e}")

def process_message_thread(sender_id, message_text):
    if not vectorstore or not llm:
        print("RESPON: Maaf, sistem AI belum siap (Database kosong).")
        send_message(sender_id, "Maaf, sistem AI belum siap.")
        return

    try:
        # 1. Cari dokumen relevan
        docs = vectorstore.similarity_search(message_text, k=3)
        
        # 2. Ambil URL
        urls = get_url_from_sources(docs)
        
        # 3. Gabungkan konteks
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        # 4. Format Prompt
        final_prompt = PROMPT.format(context=context_text, question=message_text)
        
        # 5. Panggil LLM
        response = llm.invoke(final_prompt)
        answer = response.content
        
        # 6. Tambah link referensi
        if urls:
            answer += "\n\nReferensi:\n" + "\n".join(urls)

        # Tampilkan di LOG (untuk debugging)
        print(f"\n" + "="*40)
        print(f"PESAN MASUK: {message_text}")
        print(f"JAWABAN AI: {answer}")
        print("="*40 + "\n")

        # Kirim ke Facebook
        send_message(sender_id, answer)
        
    except Exception as e:
        print(f"Error AI Thread: {e}")

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if data.get("object") == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                sender_id = messaging_event["sender"]["id"]
                if "message" in messaging_event and "text" in messaging_event["message"]:
                    message_text = messaging_event["message"]["text"]
                    thread = threading.Thread(target=process_message_thread, args=(sender_id, message_text))
                    thread.start()
                    return "OK", 200
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
