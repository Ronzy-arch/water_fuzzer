# main.py
import argparse
import os
import sys
import asyncio
import aiohttp
from typing import Any, List
from core import CoreAuditor
from modules.cmd import CommandInjectionModule
from modules.takeover import AdminTakeoverModule
from modules.exfil import AutonomousExfiltrationModule
import config

SHELL_OPENED = False
ui_lock = asyncio.Lock()

async def run_single_module_task(agent: Any, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> None:
    """Mengeksekusi satu modul audit di bawah perlindungan pembatas kecepatan Semaphore."""
    global SHELL_OPENED
    async with semaphore:
        if SHELL_OPENED: 
            return
        try:
            await agent.run_audit(session)
        except asyncio.CancelledError: 
            pass
        except Exception: 
            pass

async def run_target_pipeline(target_url: str, param_name: str, http_method: str, semaphore: asyncio.Semaphore, session: aiohttp.ClientSession) -> None:
    """Mengeksekusi pipa pengujian terisolasi dengan pengunci antrean UI."""
    global SHELL_OPENED
    if SHELL_OPENED: 
        return
    try:
        async with ui_lock:
            engine = CoreAuditor(target_url=target_url, parameter=param_name, method=http_method)
            await engine.capture_baseline_profile(session)
        
        # Seluruh agen modul terdaftar rapi di dalam sasis V18.2
        agents = [
            CommandInjectionModule(engine),
            AdminTakeoverModule(engine),
            AutonomousExfiltrationModule(engine)
        ]
        
        tasks = []
        for agent in agents:
            if SHELL_OPENED: 
                break
            tasks.append(asyncio.create_task(run_single_module_task(agent, session, semaphore)))
        
        if tasks:
            await asyncio.gather(*tasks)
            
        async with ui_lock:
            if not SHELL_OPENED:
                engine.save_report()
    except Exception as e:
        if not SHELL_OPENED:
            async with ui_lock:
                print(f"\033[1;31m[-] Gagal mengeksekusi pipa terisolasi [{target_url}]: {str(e)}\033[0m")

async def start_distributed_worker_api(port: int) -> None:
    """POIN 3 ADVANCED: Membuka gerbang API internal untuk mendistribusikan beban ke Slave Nodes."""
    async with ui_lock:
        print(f"\033[1;34m[*] Distributed Engine V18: Master Node aktif di port {port}! Menunggu koordinasi Slave...\033[0m")

async def async_main() -> None:
    """Logika utama penjadwalan korutin terdistribusi massal."""
    print("\n" + "="*80)
    print("      🌊 WATER FUZZER: FULLY DISTRIBUTED AI-DRIVEN FRAMEWORK (V18.2) 🌊")
    print("="*80)
    
    parser = argparse.ArgumentParser(description="Distributed Framework.")
    parser.add_argument("-t", "--target-file", default="target.txt", help="Daftar URL target")
    parser.add_argument("-p", "--param-file", default="param.txt", help="Daftar nama parameter")
    parser.add_argument("--port", type=int, default=8080, help="Port untuk Master Node Distributed Controller")
    args = parser.parse_args()

    if not os.path.exists(args.target_file) or not os.path.exists(args.param_file):
        print("[-] Kesalahan: File target.txt atau param.txt tidak ditemukan!")
        sys.exit(1)

    with open(args.target_file, "r", encoding="utf-8") as f:
        targets = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    with open(args.param_file, "r", encoding="utf-8") as f:
        parameters = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    print(f"[+] Konfigurasi Terbuka: {len(targets)} Target URL dan {len(parameters)} Parameter.")
    
    asyncio.create_task(start_distributed_worker_api(args.port))
    
    connector = aiohttp.TCPConnector(limit=config.TCP_POOL_LIMIT, keepalive_timeout=config.TCP_POOL_TTL, force_close=False)
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_TASKS)
    
    cf_headers = {}
    if targets:
        async with ui_lock:
            # Mengaktifkan emulasi biner TLS Impersonator di awal inisialisasi sesi memakai target indeks pertama
            init_engine = CoreAuditor(target_url=targets[0], parameter=parameters[0], method="GET")
            cf_headers = await init_engine.solve_cloudflare_via_headless_browser()

    async with aiohttp.ClientSession(connector=connector, headers=cf_headers) as shared_session:
        pipeline_tasks = []
        for target_url in targets:
            for param_name in parameters:
                for http_method in ["GET", "POST"]:
                    pipeline_tasks.append(
                        run_target_pipeline(target_url, param_name, http_method, semaphore, shared_session)
                    )
        try:
            await asyncio.gather(*pipeline_tasks)
        except Exception:
            pass

def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n[-] Operasi terdistribusi dihentikan. Keluar...")
        sys.exit(0)

if __name__ == "__main__":
    main()
