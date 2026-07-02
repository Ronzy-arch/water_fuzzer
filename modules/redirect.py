# modules/redirect.py
import os
import logging
import time
import asyncio
import aiohttp
from typing import List, Dict, Any, Tuple
from modules.base import BaseModule
import config

logger = logging.getLogger("water_fuzzer.redirect")

class OpenRedirectionModule(BaseModule):
    """
    Modul Open Redirection V10.1 Asinkronus (AI-Driven Evidence Framework).
    Menguji kemampuan manipulasi tajuk navigasi secara non-blocking, serta memicu
    inferensi LLM Ollama Lokal jika mendeteksi blokiran WAF permukaan.
    """

    def load_payloads(self) -> List[str]:
        """Memuat kamus amunisi khusus Open Redirection dari berkas eksternal atau fallback."""
        payload_file: str = os.path.join(config.BASE_DIR, "payloads", "redirect.txt")
        payloads: List[str] = []
        if os.path.exists(payload_file):
            try:
                with open(payload_file, "r", encoding="utf-8") as f:
                    payloads = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            except IOError as e:
                logger.error(f"Gagal membaca berkas payloads Open Redirection: {str(e)}")
        return payloads if payloads else ["https://google.com", "//google.com"]

    async def execute_and_evaluate(self, session: aiohttp.ClientSession, payload: str, base_payload: str, headers: dict) -> Tuple[bool, bool]:
        """Metode utilitas internal untuk mengirim paket data dan mengevaluasi indikator biner respons Redirect."""
        try:
            start_time: float = time.time()
            if self.auditor.method == "POST":
                async with session.post(self.auditor.target_url, data={self.auditor.parameter: payload}, headers=headers, timeout=self.auditor.timeout, allow_redirects=False, proxy=self.auditor._get_random_proxy()) as res:
                    body: str = await res.text()
                    status: int = res.status
                    res_headers = res.headers
            else:
                async with session.get(self.auditor.target_url, params={self.auditor.parameter: payload}, headers=headers, timeout=self.auditor.timeout, allow_redirects=False, proxy=self.auditor._get_random_proxy()) as res:
                    body: str = await res.text()
                    status: int = res.status
                    res_headers = res.headers
                        
            latency: float = time.time() - start_time
            
            # SENSOR DETEKSI BLOKIRAN WAF PERMUKAAN (DIKUNCI KAKU KODE 403, 409, 429)
            if status in [403, 409, 429] or "waf" in body.lower() or "blocked" in body.lower():
                return False, True

            matched_indicators: List[str] = []
            location_header: str = res_headers.get("Location", "")
            module_specific: Dict[str, Any] = {
                "vulnerability_proof_concept": "HTTP External Location Control",
                "http_redirect_status_code": status,
                "captured_location_header_value": location_header,
                "is_external_domain_validated": False
            }

            # EVALUASI INDIKATOR OPEN REDIRECTION (301, 302, 303, 307, 308)
            if status in [301, 302, 303, 307, 308] and location_header:
                if "google.com" in location_header or base_payload in location_header:
                    matched_indicators.append("anomalous_output")
                    matched_indicators.append("consistent_evaluation_proof")
                    module_specific["is_external_domain_validated"] = True

            if status != self.auditor.baseline["status_code"]:
                matched_indicators.append("response_diff")

            if matched_indicators:
                self.auditor.evaluate_heuristic_evidence(
                    response_text=body, status_code=status, response_time=latency,
                    sent_payload=payload, indicators=matched_indicators, evidence_type="OPEN_REDIRECTION",
                    module_specific_proof=module_specific
                )
                return True, False
                        
        except Exception as e:
            logger.debug(f"Abaikan gangguan koneksi paralel Redirect: {str(e)}")
                    
        return False, False

    async def run_audit(self, session: aiohttp.ClientSession) -> bool:
        """Menyapu kamus amunisi Redirect secara asinkronus didukung Dynamic AI Mutator."""
        print("[*] Menjalankan Modul V10.1: Open Redirection (AI-Driven)...")
        headers: dict = self.auditor._get_random_headers()
        payloads: List[str] = self.load_payloads()
        found_any_vuln: bool = False

        for base_payload in payloads:
            for strategy in range(4):
                payload = self.auditor.mutate_payload_for_waf(base_payload, strategy)
                success, trigger_ai = await self.execute_and_evaluate(session, payload, base_payload, headers)
                
                if success:
                    found_any_vuln = True
                    break
                    
                if trigger_ai:
                    print(f"[\033[1;31m!\033[0m] Peringatan: Sensor WAF Terdeteksi! Memicu Pipa Pemikiran AI Lokal...")
                    ai_mutated_payload = await self.auditor.ask_local_ai_to_bypass_waf(session, base_payload, "WAF_BLOCK_DETECTED")
                    if ai_mutated_payload:
                        success_ai, _ = await self.execute_and_evaluate(session, ai_mutated_payload, base_payload, headers)
                        if success_ai:
                            found_any_vuln = True
                            break
            if found_any_vuln:
                break

        return found_any_vuln

    def verifikator(self, response, payload_terpakai, crypto_token) -> Tuple[str, str, str, str, list]:
        return "SECURE", "None", "None", "Lolos.", []
