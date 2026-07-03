# main_tui.py - Water Fuzzer TUI Enterprise Orchestrator
import argparse
import os
import sys
import time
import asyncio
import aiohttp
from typing import Any, List, Dict
import config
from core import CoreAuditor

# Import seluruh 11 agen modul Enterprise komplit
from modules.cmd import CommandInjectionModule
from modules.sql import SqlInjectionModule
from modules.xss import CrossSiteScriptingModule
from modules.ssti import ServerSideTemplateInjectionModule
from modules.ssrf import ServerSideRequestForgeryModule
from modules.path import PathTraversalModule
from modules.exfil import ExfiltrationModule
from modules.leaked_file import LeakedFilesModule
from modules.redirect import OpenRedirectModule
from modules.takeover import SubdomainTakeoverModule

SHELL_OPENED = False

# Kamus State Global Pemantau 11 Modul Utama secara Real-Time
MODULES_STATE: Dict[str, Dict[str, Any]] = {
    "CMD":  {"name": "OS Command Inj.", "progress": 0, "status": "WAIT"},
    "SQL":  {"name": "SQL Injection   ", "progress": 0, "status": "WAIT"},
    "XSS":  {"name": "Cross-Site Scr. ", "progress": 0, "status": "WAIT"},
    "SSTI": {"name": "Template Inj.   ", "progress": 0, "status": "WAIT"},
    "SSRF": {"name": "Request Forgery ", "progress": 0, "status": "WAIT"},
    "PATH": {"name": "Path Traversal  ", "progress": 0, "status": "WAIT"},
    "EXFL": {"name": "Data Exposure   ", "progress": 0, "status": "WAIT"},
    "LEAK": {"name": "Leaked Files    ", "progress": 0, "status": "WAIT"},
    "RDIR": {"name": "Open Redirect   ", "progress": 0, "status": "WAIT"},
    "TOVR": {"name": "Domain Takeover ", "progress": 0, "status": "WAIT"}
}

TUI_LOGS: List[str] = ["[CORE] Inisialisasi arsitektur TUI Master Monitor..."]

def render_tui_display(target_url: str, identity: str) -> None:
    """Merender ulang seluruh elemen visual grafis TUI tepat di koordinat atas terminal."""
    sys.stdout.write("\033[H") # Kembalikan kursor ke pojok kiri atas
    
    cyan = "\033[1;36m"; hijau = "\033[1;32m"; kuning = "\033[1;33m"; normal = "\033[0m"
    
    print(f"{cyan}┌────────────────────────────────────────────────────────────────────────┐{normal}")
    print(f"{cyan}│ 🌊 WATER FUZZER ENTERPRISE CONCURRENT CORE v18.2 - MASTER MONITOR 🌊  │{normal}")
    print(f"{cyan}├────────────────────────────────────────────────────────────────────────┤{normal}")
    print(f"│ TARGET : {target_url:<62} │")
    print(f"│ ENGINE : TLS IMPERSONATOR IMPR -> [{hijau}{identity:<15}{normal}]              │")
    print(f"{cyan}├────────────────────────────────────────────────────────────────────────┤{normal}")
    print(f"│                       PASUKAN STATUS AGENT MODUL                       │")
    print(f"{cyan}├────────────────────────────────────────────────────────────────────────┤{normal}")
    
    for mod_id, info in MODULES_STATE.items():
        prog = info["progress"]
        status = info["status"]
        bar_count = int(prog / 5)
        bar_visual = "█" * bar_count + "░" * (20 - bar_count)
        
        status_color = kuning if status == "RUN " else (hijau if status == "DONE" else normal)
        print(f"│ ├─ [{mod_id}] {info['name']} ➜ [{bar_visual}] {prog:>3}%  [{status_color}{status}{normal}] │")
        
    print(f"{cyan}├────────────────────────────────────────────────────────────────────────┤{normal}")
    print(f"│                       MATRIKS ANOMALI MATRIX LOG                       │")
    print(f"{cyan}├────────────────────────────────────────────────────────────────────────┤{normal}")
    
    for log in TUI_LOGS[-3:]:
        print(f"│ {log:<70} │")
    for _ in range(3 - len(TUI_LOGS[-3:])):
        print(f"│ {'':<70} │")
        
    print(f"{cyan}├────────────────────────────────────────────────────────────────────────┤{normal}")
    print(f"│ 💾 LAPORAN: Rekaman bukti otomatis dikunci aman ke reports/json/       │")
    print(f"{cyan}└────────────────────────────────────────────────────────────────────────┘{normal}")
    sys.stdout.flush()

async def run_single_module_task(agent: Any, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, mod_id: str) -> None:
    global SHELL_OPENED
    async with semaphore:
        if SHELL_OPENED: return
        try:
            MODULES_STATE[mod_id]["status"] = "RUN "
            MODULES_STATE[mod_id]["progress"] = 25
            
            # Simulasi pergerakan progres taktis asinkronus
            await asyncio.sleep(0.2)
            MODULES_STATE[mod_id]["progress"] = 60
            
            await agent.run_audit(session)
            
            MODULES_STATE[mod_id]["progress"] = 100
            MODULES_STATE[mod_id]["status"] = "DONE"
        except Exception as e:
            MODULES_STATE[mod_id]["status"] = "ERR "
            TUI_LOGS.append(f"[{time.strftime('%H:%M:%S')}] ➜ [{mod_id}] Gagal: {str(e)[:30]}")

async def run_target_pipeline(target_url: str, param_name: str, http_method: str, semaphore: asyncio.Semaphore, session: aiohttp.ClientSession) -> None:
    global SHELL_OPENED
    if SHELL_OPENED: return
    try:
        engine = CoreAuditor(target_url=target_url, parameter=param_name, method=http_method)
        
        # Ambil sampel identitas browser penyamar dari core pool
        browser_identity = engine._get_random_headers().get("X-Engine-Identity", "CHROME_120")
        
        TUI_LOGS.append(f"[{time.strftime('%H:%M:%S')}] ➜ [CORE] Mengunci baseline profile target...")
        await engine.capture_baseline_profile(session)
        
        # Pipa peremajaan loop penampil visual TUI (10 kali per detik)
        async def tui_refresher_loop():
            # Mengosongkan total layar terminal (\033[2J) di awal pemicuan
            sys.stdout.write("\033[2J")
            sys.stdout.flush()
            while not SHELL_OPENED and not all(info["status"] in ["DONE", "ERR ", "WAIT"] for info in MODULES_STATE.values()):
                render_tui_display(target_url, browser_identity)
                await asyncio.sleep(0.1)
            render_tui_display(target_url, browser_identity)

        # Mendaftarkan seluruh agensi modul V18 Enterprise ke peta tugas
        agents_mapping = {
            "CMD": CommandInjectionModule(engine),
            "SQL": SqlInjectionModule(engine),
            "XSS": CrossSiteScriptingModule(engine),
            "SSTI": ServerSideTemplateInjectionModule(engine),
            "SSRF": ServerSideRequestForgeryModule(engine),
            "PATH": PathTraversalModule(engine),
            "EXFL": ExfiltrationModule(engine),
            "LEAK": LeakedFilesModule(engine),
            "RDIR": OpenRedirectModule(engine),
            "TOVR": SubdomainTakeoverModule(engine)
        }
        
        # Memicu loop penampil visual dasbor di background secara independen
        refresher_task = asyncio.create_task(tui_refresher_loop())
        
        tasks = [
            asyncio.create_task(run_single_module_task(agent_obj, session, semaphore, m_id))
            for m_id, agent_obj in agents_mapping.items()
        ]
        
        if tasks: await asyncio.gather(*tasks)
        if not SHELL_OPENED: engine.save_report()
        
        await refresher_task
    except Exception as e:
        if not SHELL_OPENED: TUI_LOGS.append(f"[-] Pipeline Error: {str(e)}")

async def async_main() -> None:
    parser = argparse.ArgumentParser(description="V18.2 TUI Framework.")
    parser.add_argument("-t", "--target-file", default="target.txt")
    parser.add_argument("-p", "--param-file", default="param.txt")
    args = parser.parse_args()

    if not os.path.exists(args.target_file) or not os.path.exists(args.param_file):
        print("[-] Kesalahan: File target.txt atau param.txt tidak ditemukan!")
        sys.exit(1)

    with open(args.target_file, "r", encoding="utf-8") as f:
        targets = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    with open(args.param_file, "r", encoding="utf-8") as f:
        parameters = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    connector = aiohttp.TCPConnector(limit=config.TCP_POOL_LIMIT, keepalive_timeout=config.TCP_POOL_TTL)
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_TASKS)

    async with aiohttp.ClientSession(connector=connector) as shared_session:
        pipeline_tasks = []
        for target_url in targets:
            for param_name in parameters:
                for http_method in ["GET", "POST"]:
                    pipeline_tasks.append(run_target_pipeline(target_url, param_name, http_method, semaphore, shared_session))
        try: await asyncio.gather(*pipeline_tasks)
        except Exception: pass

def main() -> None:
    try: asyncio.run(async_main())
    except KeyboardInterrupt:
        sys.stdout.write("\n\033[0m[-] Monitor TUI dihentikan paksa. Keluar...\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
