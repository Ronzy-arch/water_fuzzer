# modules/leaked_files.py
import os
import logging
import aiohttp
from urllib.parse import urlparse, urlunparse, ParseResult
from typing import List, Dict, Any, Tuple
from modules.base import BaseModule
import config

logger = logging.getLogger("water_fuzzer.leaked_files")

class LeakedFilesModule(BaseModule):
    """
    Modul Sensitive File Disclosure V10.1 Asinkronus (AI-Driven Evidence Framework).
    Menggunakan fungsi isolasi perakit URL terpisah untuk menyisir root direktori aplikasi web
    secara non-blocking dan memvalidasi pola data sensitif yang terekspos publik.
    """

    def build_target_url(self, target_url: str, filename: str) -> str:
        """Merakit kembali komponen URL menuju root objek berkas target secara terisolasi."""
        try:
            parsed: ParseResult = urlparse(target_url)
            return urlunparse((parsed.scheme, parsed.netloc, filename, '', '', ''))
        except Exception as e:
            logger.error(f"Gagal memparsing URL untuk komponen file '{filename}': {str(e)}")
            return ""

    async def run_audit(self, session: aiohttp.ClientSession) -> bool:
        """Mengeksekusi penyisiran massal berkas konfigurasi secara asinkronus tanpa interupsi loop."""
        print("[*] Menjalankan Modul V10.1 Asinkronus: Sensitive File Disclosure...")
        headers: dict = self.auditor._get_random_headers()
        found_any_leak: bool = False
        target_wordlist: List[str] = config.TARGET_FILES_WORDLIST

        for f_name in target_wordlist:
            url_uji: str = self.build_target_url(self.auditor.target_url, f_name)
            if not url_uji:
                continue
                
            try:
                # allow_redirects=False wajib dikunci agar kebal jebakan false positive pengalihan login
                async with session.get(url_uji, headers=headers, timeout=self.auditor.timeout, allow_redirects=False, proxy=self.auditor._get_random_proxy()) as res:
                    body: str = await res.text()
                    status: int = res.status
                
                matched_indicators: List[str] = []
                module_specific: Dict[str, Any] = {
                    "vulnerability_proof_concept": "Sensitive Configuration Disclosure",
                    "exposed_file_path": url_uji,
                    "matched_data_patterns": [],
                    "is_critical_credential_leaked": False
                }

                # FIX: Mengunci kode proteksi HTTP WAF secara kaku dan valid (Anti-SyntaxError)
                if status in [403, 409, 429] or "waf" in body.lower() or "blocked" in body.lower():
                    print(f"[\033[1;31m!\033[0m] WAF mencegah pembacaan langsung '{f_name}'! Memicu Pipa Pemikiran AI...")
                    ai_bypass_suggestion = await self.auditor.ask_local_ai_to_bypass_waf(session, f_name, "WAF_BLOCK_DETECTED")
                    if ai_bypass_suggestion and ai_bypass_suggestion != f_name:
                        url_uji_ai = self.build_target_url(self.auditor.target_url, ai_bypass_suggestion)
                        async with session.get(url_uji_ai, headers=headers, timeout=self.auditor.timeout, allow_redirects=False, proxy=self.auditor._get_random_proxy()) as res_ai:
                            body = await res_ai.text()
                            status = res_ai.status
                            url_uji = url_uji_ai

                # EVALUASI INDIKATOR KEBOCORAN KREDENSIAL INTERNAL
                if status == 200 and len(body) > 0:
                    for signature in ["DB_PASSWORD", "repositoryformatversion", "AWS_SECRET", "SECRET_KEY"]:
                        if signature in body:
                            matched_indicators.append("anomalous_output")
                            matched_indicators.append("consistent_evaluation_proof")
                            module_specific["is_critical_credential_leaked"] = True
                            module_specific["matched_data_patterns"].append(f"Found internal key: {signature}")

                if status != self.auditor.baseline["status_code"]:
                    matched_indicators.append("response_diff")

                if matched_indicators:
                    self.auditor.evaluate_heuristic_evidence(
                        response_text=body, status_code=status, response_time=0.1,
                        sent_payload=f_name, indicators=matched_indicators, evidence_type="SENSITIVE_FILE_LEAK",
                        module_specific_proof=module_specific
                    )
                    found_any_leak = True
                    
            except Exception as e:
                logger.debug(f"Abaikan gangguan koneksi paralel Leaked Files: {str(e)}")
                
        return found_any_leak

    def verifikator(self, response, payload_terpakai, crypto_token) -> Tuple[str, str, str, str, list]:
        return "SECURE", "None", "None", "Lolos.", []
