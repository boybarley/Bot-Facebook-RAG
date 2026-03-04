import os
import sys
import subprocess
import time

# Konfigurasi Path
PROJECT_DIR = "/opt/fb-rag-bot"
VENV_PYTHON = f"{PROJECT_DIR}/venv/bin/python"
SERVICE_NAME = "fb-rag-bot"

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def run_command(cmd, cwd=PROJECT_DIR):
    """Jalankan command shell"""
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {e}")
    except KeyboardInterrupt:
        print("\n[INFO] Proses dihentikan user.")

def check_service_status():
    result = subprocess.run(["systemctl", "is-active", SERVICE_NAME], capture_output=True, text=True)
    return result.stdout.strip() == "active"

def main():
    while True:
        clear_screen()
        status = "🟢 RUNNING" if check_service_status() else "🔴 STOPPED"
        
        print("=" * 50)
        print(f"   BOT MANAGER - Facebook RAG System")
        print(f"   Status Service: {status}")
        print("=" * 50)
        print("\n   [1] Start Bot   (Jalankan Service)")
        print("   [2] Stop Bot    (Hentikan Service)")
        print("   [3] Restart Bot (Restart Service)")
        print("   [4] View Logs   (Monitor aktivitas real-time)")
        print("   -------------------------------------------")
        print("   [5] Crawl Website (Update data dari Web)")
        print("   [6] Ingest PDF    (Tambah data dari PDF)")
        print("   -------------------------------------------")
        print("   [0] Exit")
        print("=" * 50)
        
        choice = input("\n   Pilih menu (0-6): ").strip()

        if choice == '1':
            print("\n[INFO] Memulai service...")
            run_command(f"systemctl start {SERVICE_NAME}")
            time.sleep(1)
        
        elif choice == '2':
            print("\n[INFO] Menghentikan service...")
            run_command(f"systemctl stop {SERVICE_NAME}")
            time.sleep(1)

        elif choice == '3':
            print("\n[INFO] Merestart service...")
            run_command(f"systemctl restart {SERVICE_NAME}")
            time.sleep(1)

        elif choice == '4':
            print("\n[INFO] Menampilkan logs (Tekan CTRL+C untuk kembali ke menu)...\n")
            time.sleep(1)
            # Menggunakan journalctl untuk melihat log
            run_command(f"journalctl -u {SERVICE_NAME} -f --no-pager -n 50")

        elif choice == '5':
            print("\n[INFO] Memulai Web Crawler...")
            print("[INFO] Pastikan Anda sudah mengedit URL di dalam crawl.py")
            # Cek dulu service, mesti dihentikan biar tidak konflik saat menulis DB
            if check_service_status():
                confirm = input("   [!] Bot sedang berjalan. Hentikan dulu untuk update DB? (y/n): ")
                if confirm.lower() == 'y':
                    run_command(f"systemctl stop {SERVICE_NAME}")
                else:
                    continue
            
            run_command(f"{VENV_PYTHON} {PROJECT_DIR}/crawl.py")
            input("\n[INFO] Selesai. Tekan Enter untuk kembali...")

        elif choice == '6':
            print("\n[INFO] Memulai Ingest PDF...")
            if check_service_status():
                confirm = input("   [!] Bot sedang berjalan. Hentikan dulu untuk update DB? (y/n): ")
                if confirm.lower() == 'y':
                    run_command(f"systemctl stop {SERVICE_NAME}")
                else:
                    continue
            
            run_command(f"{VENV_PYTHON} {PROJECT_DIR}/ingest_pdf.py")
            input("\n[INFO] Selesai. Tekan Enter untuk kembali...")

        elif choice == '0':
            print("\n[INFO] Sampai jumpa!")
            sys.exit(0)
        
        else:
            print("\n[ERROR] Pilihan tidak valid!")
            time.sleep(1)

if __name__ == "__main__":
    # Cek apakah script dijalankan sebagai root
    if os.geteuid() != 0:
        print("Mohon jalankan skrip ini sebagai root (sudo python manage.py)")
        sys.exit(1)
    
    # Cek apakah direktori proyek ada
    if not os.path.exists(PROJECT_DIR):
        print(f"Error: Direktori proyek {PROJECT_DIR} tidak ditemukan.")
        print("Pastikan Anda sudah menjalankan install.sh")
        sys.exit(1)
        
    main()
