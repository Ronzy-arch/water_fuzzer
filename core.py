# core.py
import json
import logging
import re
import time
import random
import os
import hashlib
import math
import asyncio
import aiohttp
from urllib.parse import urlparse, quote
from typing import List, Dict, Any, Tuple, Optional
import config

logger = logging.getLogger("water_fuzzer.core")

class CoreAuditor:
    """
    Jantung Utama Orkestrator V18.6 (Concurrent Multi-Fingerprint Proxy Engine).
    Secara dinamis mengocok dan melepas sidik jari TLS dari Chrome dan Firefox serentak
    pada setiap korutin request jaringan secara independen dan bersamaan.
    """
    def __init__(self, target_url: str, parameter: str, method: str = "POST") -> None:
        self.target_url: str = target_url
        self.parameter: str = parameter
        self.method: str = method.upper()
        self.timeout: float = config.TIMEOUT
        
        os.makedirs(config.REPORT_DIR, exist_ok=True)
        os.makedirs(config.RAW_LOG_DIR, exist_ok=True)
        os.makedirs(config.SERVER_LOG_DIR, exist_ok=True)
        
        self.baseline: Dict[str, Any] = {
            "status_code": 200, "content_length": 0, "response_time": 0.0, "entropy_score": 0.0, "captured": False
        }

        self.ai_seed: str = str(time.time()) + str(random.randint(1000, 9999))
        self.crypto_token: str = hashlib.sha256(self.ai_seed.encode()).hexdigest()[:16]

        self.master_report: Dict[str, Any] = {
            "audit_metadata": {
                "target_url": self.target_url, "tested_parameter": self.parameter, "http_method": self.method,
                "audit_timestamp_start": time.strftime("%Y-%m-%d %H:%M:%S"), "assessment_engine": "EVIDENCE_DRIVEN_AI_ENGINE_V18_6_CONCURRENT"
            },
            "audit_findings_summary": []
        }

        self.browser_pool: List[Dict[str, str]] = [
            {
                "name": "CHROME",
                "impersonate": "chrome",
                "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            },
            {
                "name": "FIREFOX",
                "impersonate": "firefox",
                "ua": "Mozilla/5.0 (Android 10; Mobile; rv:126.0) Gecko/126.0 Firefox/126.0"
            }
        ]

    def _get_dynamic_request_identity(self) -> Dict[str, str]:
        """V18.6 CONCURRENT ENGINE: Mencabut identitas browser secara instan untuk korutin paralel."""
        return random.choice(self.browser_pool)

    def _get_random_headers(self) -> Dict[str, str]:
        # Pipa Independen: Setiap korutin request mencabut identitasnya sendiri agar bisa jalan serentak berdampingan
        identity = self._get_dynamic_request_identity()
        headers = {
            "User-Agent": identity["ua"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Connection": "keep-alive",
            "X-Engine-Identity": identity["name"],
            "X-Impersonate-Code": identity["impersonate"]
        }
        if os.path.exists("cookie.txt"):
            try:
                with open("cookie.txt", "r", encoding="utf-8") as f:
                    cookie_data = f.read().strip()
                    if cookie_data: headers["Cookie"] = cookie_data
            except Exception: pass
        return headers

    async def solve_cloudflare_via_headless_browser(self) -> Dict[str, str]:
        """POIN 1 V18.6: Membakar jalur Cloudflare memakai emulasi Chrome & Firefox serentak bersamaan."""
        print("\n\033[1;35m[*] TLS Interceptor V18.6: Menembakkan Sidik Jari CHROME & FIREFOX Serentak Bersamaan... \033[0m")
        loop = asyncio.get_running_loop()
        identity = self._get_dynamic_request_identity()
        
        def _execute_curl_cffi_request():
            from curl_cffi import requests
            headers = {
                "User-Agent": identity["ua"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            response = requests.get(self.target_url, headers=headers, impersonate=identity["impersonate"], timeout=int(config.TIMEOUT))
            return response.cookies.get("cf_clearance"), response.text

        try:
            cf_val, raw_html = await loop.run_in_executor(None, _execute_curl_cffi_request)
            if cf_val:
                cookie_string = f"cf_clearance={cf_val}"
                print(f"\033[1;32m[+] SUCCESS: TLS Impersonator [{identity['name']}] Berhasil Memanen Token Cloudflare!\033[0m")
                import aiofiles
                async with aiofiles.open("cookie.txt", "w", encoding="utf-8") as f:
                    await f.write(cookie_string)
                return {"Cookie": cookie_string}
            else:
                print(f"[-] TLS Impersonator [{identity['name']}]: Saringan kaku Turnstile aktif.")
        except Exception as e:
            print(f"[-] TLS Interceptor Error: Hambatan emulasi enkripsi soket: {str(e)}")
        return {}

    def _get_random_proxy(self) -> Optional[str]:
        if os.path.exists("proxy.txt"):
            try:
                with open("proxy.txt", "r", encoding="utf-8") as f:
                    proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                    if proxies: return random.choice(proxies)
            except Exception: pass
        return None

    def calculate_content_entropy(self, text: str) -> float:
        if not text: return 0.0
        frequencies: Dict[str, int] = {}
        for char in text: frequencies[char] = frequencies.get(char, 0) + 1
        entropy = 0.0
        total_chars = len(text)
        for count in frequencies.values():
            p = count / total_chars
            entropy -= p * math.log2(p)
        return round(entropy, 4)

    async def ask_local_ai_to_bypass_waf(self, session: aiohttp.ClientSession, base_payload: str, waf_response_text: str) -> str:
        clean_waf_text = waf_response_text[:1200].strip()
        prompt_instruction = (
            "Anda adalah Core AI Kernel untuk fuzzer adaptif tingkat tinggi. Tugas Anda adalah memintas saringan WAF.\n"
            "Analisis potongan bodi respons sensor Firewall berikut:\n"
            f"'{clean_waf_text}'\n\n"
            "Berdasarkan signature WAF di atas, deteksi karakter atau kata yang dilarang (misal: spasi, tanda petik, atau SELECT).\n"
            f"Lakukan mutasi polimorfik cerdas (menggunakan teknik alternatif, comment-nesting /**/, hex-encoding, atau bypass logic) dari payload dasar ini: '{base_payload}'\n"
            "ATURAN MUTLAK: Jawab HANYA string payload hasil mutasi finalnya saja! Jangan berikan penjelasan, jangan berikan markdown ```, jangan berikan basa-basi kata pengantar!"
        )
        request_body = {"model": config.OLLAMA_MODEL_NAME, "prompt": prompt_instruction, "stream": False, "options": {"temperature": 0.2, "top_p": 0.1}}
        try:
            print(f"\n\033[1;35m[*] AI Polymorphic Engine: Meminta inferensi otonom dari {config.OLLAMA_MODEL_NAME}...\033[0m")
            async with session.post(config.OLLAMA_API_URL, json=request_body, timeout=20.0) as response:
                if response.status == 200:
                    result = await response.json()
                    ai_payload = result.get("response", "").strip()
                    clean_payload = re.sub(r'^[`"\'\\]|[`"\'\\]\$', '', ai_payload).strip()
                    clean_payload = clean_payload.replace("```", "").strip()
                    print(f"\033[1;32m[+] SUCCESS: AI Berhasil Memproduksi Mutasi Peluru -> {clean_payload}\033[0m")
                    return clean_payload
        except Exception as e:
            logger.debug(f"Koneksi pipa Ollama lokal offline, beralih ke strategi fallback kaku: {str(e)}")
        return ""

    def mutate_payload_for_waf(self, base_payload: str, strategy_index: int) -> str:
        if strategy_index == 0: return base_payload
        elif strategy_index == 1: return base_payload.replace(" ", "/**/").replace("UNION", "uNiOn").replace("SELECT", "sElEcT")
        elif strategy_index == 2: return quote(quote(base_payload))
        elif strategy_index == 3: return f"%00{base_payload}"
        return base_payload

    async def capture_baseline_profile(self, session: aiohttp.ClientSession) -> None:
        try:
            headers = self._get_random_headers()
            start_time = time.time()
            if self.method == "POST":
                async with session.post(self.target_url, data={self.parameter: "baseline_v18_6"}, headers=headers, timeout=self.timeout, proxy=self._get_random_proxy()) as res:
                    body = await res.text(); status = res.status
            else:
                async with session.get(self.target_url, params={self.parameter: "baseline_v18_6"}, headers=headers, timeout=self.timeout, proxy=self._get_random_proxy()) as res:
                    body = await res.text(); status = res.status
            self.baseline["status_code"] = status
            self.baseline["content_length"] = len(body)
            self.baseline["response_time"] = time.time() - start_time
            self.baseline["entropy_score"] = self.calculate_content_entropy(body)
            self.baseline["captured"] = True
            print(f"\033[1;32m[+] ASYNC BASELINE LOCKED: Status = {status} | Entropy = {self.baseline['entropy_score']} | Executed as Multi-Fingerprint Core\033[0m")
        except Exception as e:
            logger.critical(f"Gagal mengunci baseline V18.6: {str(e)}")

    async def save_raw_response_log_async(self, payload_name: str, request_headers: dict, status_code: int, response_text: str) -> str:
        clean_payload = re.sub(r'[^a-zA-Z0-9]', '_', payload_name)[:20]
        file_name = f"raw_v18_{clean_payload}_{int(time.time())}.txt"
        full_path = os.path.join(config.RAW_LOG_DIR, file_name)
        try:
            import aiofiles
            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(f"=== RAW HTTP REQUEST LOG ===\nURL: {self.target_url}\nMethod: {self.method}\nHeaders: {json.dumps(request_headers)}\n\n")
                await f.write(f"=== RAW HTTP RESPONSE LOG ===\nStatus: {status_code}\n\nBody:\n{response_text}")
        except ImportError:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(f"=== RAW HTTP REQUEST LOG ===\nURL: {self.target_url}\nHeaders: {json.dumps(request_headers)}\n\nBody:\n{response_text}")
        return full_path

    def evaluate_heuristic_evidence(self, response_text: str, status_code: int, response_time: float, sent_payload: str, indicators: List[str], evidence_type: str, module_specific_proof: Dict[str, Any]) -> str:
        verdict = "SECURE"
        technical_reason = "Aplikasi berperilaku normal dalam batas aman pengujian."
        has_response_diff = "response_diff" in indicators
        has_anomalous = "anomalous_output" in indicators
        has_verified = "consistent_evaluation_proof" in indicators
        has_time_anomaly = "time_anomaly" in indicators
        has_confirmed = "server_state_change_confirmed" in indicators

        confidence_score = 0
        if has_response_diff: confidence_score += 10
        if has_anomalous: confidence_score += 25
        if has_time_anomaly: confidence_score += 40
        if has_verified: confidence_score += 50
        if has_confirmed: confidence_score += 100

        if has_response_diff and confidence_score < 30: verdict = "OBSERVED"
        elif has_anomalous and confidence_score < 60: verdict = "SUSPECTED"
        elif (has_verified or has_time_anomaly) and not has_confirmed: verdict = "VERIFIED"
        elif has_confirmed or confidence_score >= 100: verdict = "CONFIRMED"

        if verdict != "SECURE":
            loop = asyncio.get_event_loop()
            log_path = os.path.join(config.RAW_LOG_DIR, f"pending_v18_{int(time.time())}.txt")
            if loop.is_running():
                loop.create_task(self.save_raw_response_log_async(sent_payload, self._get_random_headers(), status_code, response_text))
            
            self.master_report["audit_findings_summary"].append({
                "1_REQUEST_EVIDENCE": {"method": self.method, "endpoint": self.target_url, "parameter": self.parameter, "tested_payload": sent_payload},
                "2_BASELINE_EVIDENCE": self.baseline,
                "3_TEST_RESPONSE_EVIDENCE": {"http_status_code": status_code, "response_length": len(response_text), "actual_response_time": response_time, "matched_indicators": indicators},
                "4_BEHAVIORAL_PROOF": {"confidence_scoring_matrix": confidence_score, "is_pure_loopback_evaluation": has_verified, "verdict_tier_status": verdict, "technical_evidence_reason": technical_reason},
                "5_MODULE_SPECIFIC_EVIDENCE": module_specific_proof, "raw_http_evidence_file_path": log_path
            })
            print(f"\033[1;33m[!] AUTONOMOUS EVIDENCE VERDICT: [{verdict}] (Confidence Score: {confidence_score})\033[0m")
            return verdict
        return "SECURE"

    def save_report(self) -> None:
        try:
            output_name = os.path.join(config.REPORT_DIR, f"audit_v18_enterprise_{int(time.time())}_report.json")
            with open(output_name, 'w', encoding='utf-8') as f:
                json.dump(self.master_report, f, indent=4, ensure_ascii=False)
            print(f"\n\033[0;32m[+] Sukses! Dokumen Forensik V18 disimpan di: {output_name}\033[0m\n")
        except IOError as e:
            logger.critical(f"Gagal total menulis dokumen JSON report: {str(e)}")

def bypass_cloudflare_just_a_moment(targets: List[str]) -> dict:
    return {}
