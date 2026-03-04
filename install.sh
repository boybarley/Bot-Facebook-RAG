#!/bin/bash

# Definisikan direktori proyek
PROJECT_DIR="/opt/fb-rag-bot"
VENV_DIR="$PROJECT_DIR/venv"
USER="root" # Sesuaikan jika menggunakan user non-root

echo ">>> Memulai instalasi Bot Facebook RAG..."

# 1. Update sistem dan instal dependensi sistem
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git curl

# 2. Buat direktori proyek jika belum ada
sudo mkdir -p $PROJECT_DIR/data
cd $PROJECT_DIR

# 3. Buat Virtual Environment
echo ">>> Membuat Python Virtual Environment..."
python3 -m venv $VENV_DIR

# 4. Aktifkan environment dan instal library Python
source $VENV_DIR/bin/activate

# Buat requirements.txt
cat <<EOF > requirements.txt
flask
langchain
langchain-community
langchain-ollama
faiss-cpu
ollama
beautifulsoup4
lxml
pypdf
python-dotenv
requests
EOF

echo ">>> Menginstal library Python..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Buat file .env template
if [ ! -f .env ]; then
    echo ">>> Membuat file .env..."
    cat <<EOF > .env
PAGE_ACCESS_TOKEN="MASUKKAN_PAGE_ACCESS_TOKEN_ANDA_DI_SINI"
VERIFY_TOKEN="MASUKKAN_VERIFY_TOKEN_CUSTOM_ANDA_DI_SINI"
EOF
    echo ">>> PERHATIAN: Harap edit file .env dan isi token Anda."
fi

# 6. Konfigurasi Systemd Service
echo ">>> Mengkonfigurasi Systemd Service..."
cat <<EOF > /etc/systemd/system/fb-rag-bot.service
[Unit]
Description=Facebook Messenger RAG Bot Service
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl enable fb-rag-bot

echo ">>> Instalasi selesai!"
echo ">>> Langkah selanjutnya:"
echo "    1. Jalankan 'ollama pull llama3' dan 'ollama pull nomic-embed-text'"
echo "    2. Edit file .env"
echo "    3. Jalankan crawl.py dan ingest_pdf.py"
echo "    4. Start service: systemctl start fb-rag-bot"
