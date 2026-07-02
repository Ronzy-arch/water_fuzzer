# cf_generator.py
import sys
import os
import re
import asyncio
import aiofiles

async def generate_cloudflare_clearance_async():
    """Async version to avoid blocking I/O in async contexts."""
    print("\n" + "="*80)
    print("   🌊 WATER FUZZER: CLOUDFLARE TURNSTILE DYNAMIC AUTOMATED GENERATOR 🌊")
    print("="*80)
    
    target_file = "target.txt"
    config_path = "config.py"
    
    # VALIDASI KEBERADAAN BERKAS DAFTAR TARGET
    if not os.path.exists(target_file):
        print(f"[-] Kesalahan: Berkas input '{target_file}' tidak ditemukan!")
        print("[*] Silakan buat file 'target.txt' dan isi dengan URL target Anda.")
        sys.exit(1)
        
    try:
        import cloudscraper
    except ImportError:
        print("[-] Kesalahan: Pustaka 'cloudscraper' belum terpasang di Termux!")
        print("[*] Jalankan perintah ini terlebih dahulu: pip install cloudscraper")
        sys.exit(1)

    # MEMBACA TARGET PERTAMA DARI FILE TARGET.TXT SECARA DINAMIS (async)
    try:
        async with aiofiles.open(target_file, "r", encoding="utf-8") as f:
            content = await f.read()
            targets = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith("#")]
    except Exception as e:
        print(f"[-] Error reading target file: {e}")
        sys.exit(1)
        
    if not targets:
        print("[-] Kesalahan: File 'target.txt' kosong! Masukkan URL target terlebih dahulu.")
        sys.exit(1)
        
    # Mengunci URL pertama sebagai basis pengondisian kuki clearance session
    target_url = targets[0]
    print(f"[+] Deteksi Target Aktif dari target.txt -> {target_url}")

    try:
        print(f"[*] Menghubungi gerbang Cloudflare Turnstile secara dinamis...")
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'android',
                'desktop': False
            }
        )
        
        # Mengeksekusi rendering JavaScript Cloudflare di memori RAM Termux
        response = scraper.get(target_url, timeout=15)
        cookies = scraper.cookies.get_dict()
        
        if "cf_clearance" in cookies:
            token_clearance = cookies["cf_clearance"]
            bm_token = cookies.get("__cf_bm", "")
            
            cookie_string = f"cf_clearance={token_clearance}"
            if bm_token:
                cookie_string += f"; __cf_bm={bm_token}"
                
            print("\n\033[1;32m[+] SUCCESS: Sandi JavaScript Cloudflare Berhasil Dipecahkan!\033[0m")
            print(f"[+] Token Clearance Terkunci: {token_clearance[:20]}...")
            
            # MEMANIPULASI DAN MENYUNTIKKAN DATA COOKIE SECARA OTOMATIS KE CONFIG.PY (async)
            if os.path.exists(config_path):
                try:
                    async with aiofiles.open(config_path, "r", encoding="utf-8") as f:
                        file_content = await f.read()
                    
                    if "USER_AGENTS" in file_content:
                        file_content = re.sub(r'USER_AGENTS\s*=.*', '', file_content, flags=re.DOTALL)
                    
                    # Membangun ulang file config.py dengan membawa kuki clearance terbaru secara dinamis
                    new_config = (
                        f'# config.py otomatis diperbarui secara dinamis oleh cf_generator.py\n'
                        f'import os\n'
                        f'from typing import List\n\n'
                        f'BASE_DIR = os.path.dirname(os.path.abspath(__file__))\n'
                        f'REPORT_DIR = os.path.join(BASE_DIR, "reports", "json")\n'
                        f'RAW_LOG_DIR = os.path.join(BASE_DIR, "reports", "raw_logs")\n'
                        f'SERVER_LOG_DIR = os.path.join(BASE_DIR, "server_logs_capture")\n\n'
                        f'TIMEOUT = 15.0\n'
                        f'MAX_CONCURRENT_TASKS = 50\n'
                        f'TIME_DELAY_THRESHOLD = 5.0\n'
                        f'OOB_GATEWAY = "http://waterfuzzer.local"\n\n'
                        f'OLLAMA_API_URL = "http://localhost:11434/api/generate"\n'
                        f'OLLAMA_MODEL_NAME = "llama3"\n\n'
                        f'# TOKEN SAKRAL BYPASS CLOUDFLARE TURNSTILE (DINAMIS)\n'
                        f'CLOUDFLARE_COOKIE = "{cookie_string}"\n\n'
                        f'USER_AGENTS = [\n'
                        f'    "{scraper.headers.get("User-Agent")}"\n'
                        f']\n\n'
                        f'TARGET_FILES_WORDLIST = [".env", ".env.bak", "wp-config.php.bak", "config.php.bak", ".git/config", "backup.sql"]\n'
                    )
                    
                    async with aiofiles.open(config_path, "w", encoding="utf-8") as f:
                        await f.write(new_config)
                        
                    print("\033[1;36m[+] Sinkronisasi Berhasil: File 'config.py' otomatis dipersenjatai kuki target baru!\033[0m\n")
                except Exception as e:
                    print(f"[-] Error updating config.py: {e}")
            else:
                print("[-] Kesalahan: File 'config.py' tidak ditemukan.")
        else:
            print("\n\033[1;31m[-] GAGAL: Cloudflare Turnstile menolak emulasi skrip.\033[0m")
            print("[*] Solusi Manual: Salin Cookie cf_clearance dari Google Chrome asli Anda ke config.py.")
            
    except Exception as e:
        print(f"\n[-] Kegagalan Interogasi Scraper Dinamis: {str(e)}")

def generate_cloudflare_clearance():
    """Sync wrapper for async function (backward compatible)."""
    try:
        asyncio.run(generate_cloudflare_clearance_async())
    except Exception as e:
        print(f"[-] Error in async execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_cloudflare_clearance()
