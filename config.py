# config.py
import os
from typing import List

# ARSITEKTUR STRUKTUR DIREKTORI REKORD V18 ENTERPRISE (TLS INTERCEPTOR)
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR: str = os.path.join(BASE_DIR, "reports", "json")
RAW_LOG_DIR: str = os.path.join(BASE_DIR, "reports", "raw_logs")
SERVER_LOG_DIR: str = os.path.join(BASE_DIR, "server_logs_capture")

# TIMEOUT & AMBANG BATAS JARINGAN ASINKRONUS MASAL V18
TIMEOUT: float = 15.0
MAX_CONCURRENT_TASKS: int = 50
TIME_DELAY_THRESHOLD: float = 5.0
OOB_GATEWAY: str = "http://waterfuzzer.local"

# INTERFACES API OLLAMA LOKAL (V18 POLYMORPHIC ENGINE)
OLLAMA_API_URL: str = "http://localhost:11434/api/generate"
OLLAMA_MODEL_NAME: str = "deepseek-coder:1.3b"

# KUNCI GHOST PROXIES LIMITER
TCP_POOL_LIMIT: int = 100
TCP_POOL_TTL: int = 300

# CONFIG POIN 1: PENYAMARAN SIDIK JARI BINER BROWSER (ANTI-GUI/BROWSERLESS)
# Opsi emulator: 'chrome', 'firefox', 'safari'
CURL_CFFI_BROWSER: str = "firefox" 
COOKIE_REFRESH_THRESHOLD_MINUTES: int = 20

USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Android 10; Mobile; rv:126.0) Gecko/126.0 Firefox/126.0"
]

TARGET_FILES_WORDLIST: List[str] = [
    ".env", ".env.bak", "wp-config.php.bak", "config.php.bak", ".git/config", "backup.sql"
]
