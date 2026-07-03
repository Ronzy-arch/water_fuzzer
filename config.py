# config.py - WATER FUZZER V2.0 STABLE RELEASE
# Updated version synchronization across all modules

import os
from typing import List

# ═══════════════════════════════════════════════════════════════════════════
# FRAMEWORK VERSION INFORMATION - V2.0 (All components synchronized)
# ═══════════════════════════════════════════════════════════════════════════
FRAMEWORK_VERSION = "2.0"
FRAMEWORK_RELEASE_DATE = "2024-Q3"
ENGINE_NAME = "WATER_FUZZER_V2.0_ENTERPRISE"
ASSESSMENT_ENGINE = "EVIDENCE_DRIVEN_AI_ENGINE_V2_0_CONCURRENT_STATEFUL"

# ═══════════════════════════════════════════════════════════════════════════
# DIRECTORY STRUCTURE - V2.0 ENTERPRISE (Enhanced for stateful operations)
# ═══════════════════════════════════════════════════════════════════════════
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR: str = os.path.join(BASE_DIR, "reports", "json")
RAW_LOG_DIR: str = os.path.join(BASE_DIR, "reports", "raw_logs")
SERVER_LOG_DIR: str = os.path.join(BASE_DIR, "server_logs_capture")
SHELL_SESSION_DIR: str = os.path.join(BASE_DIR, "shell_sessions")  # NEW: Track shell interactions

# ═══════════════════════════════════════════════════════════════════════════
# NETWORK & CONCURRENCY TUNING - V2.0 (Anti-stacking optimization)
# ═══════════════════════════════════════════════════════════════════════════
TIMEOUT: float = 15.0
MAX_CONCURRENT_TASKS: int = 1  # CRITICAL: Reduced to 1 to prevent concurrent interference
MAX_PARALLEL_MODULES: int = 1  # CRITICAL: Only 1 module at a time during fuzzing
MAX_SHELL_COMMANDS_QUEUE: int = 100  # Increased for extended sessions
SHELL_RESPONSE_TIMEOUT: float = 15.0  # Shell command timeout
TIME_DELAY_THRESHOLD: float = 5.0
OOB_GATEWAY: str = "http://waterfuzzer.local"

# ═══════════════════════════════════════════════════════════════════════════
# SHELL SESSION MANAGEMENT - V2.0 (Stateful interactive session control)
# ═══════════════════════════════════════════════════════════════════════════
SHELL_SESSION_LOCK_TIMEOUT: float = 60.0  # Increased from 30s to allow longer sessions
SHELL_IDLE_TIMEOUT: float = 600.0  # 10 minutes (increased from 5)
MAX_CONCURRENT_SHELLS: int = 1  # Enforce single shell globally
SHELL_PROMPT_TEMPLATE: str = "\033[1;32mwater-shell [{cwd}]> \033[0m"
SHELL_COLOR_CYAN: str = "\033[1;36m"
SHELL_COLOR_GREEN: str = "\033[1;32m"
SHELL_COLOR_RED: str = "\033[1;31m"
SHELL_COLOR_YELLOW: str = "\033[1;33m"
SHELL_COLOR_RESET: str = "\033[0m"

# ═══════════════════════════════════════════════════════════════════════════
# DATA ISOLATION & PARSING - V2.0 (Enhanced boundary token mechanisms)
# ═══════════════════════════════════════════════════════════════════════════
BOUNDARY_TOKEN_PREFIX: str = "===WATER_BOUNDARY_START"  # Unique boundary token
BOUNDARY_TOKEN_SUFFIX: str = "===WATER_BOUNDARY_END"    # Unique boundary token
COMMAND_WRAPPER_STRATEGY: str = "boundary_tokens"  # Use boundary tokens for output isolation
MAX_RESPONSE_PARSE_LENGTH: int = 50000  # Max bytes to parse from response
HTML_CLEANUP_ENABLED: bool = True  # Enable HTML/JS cleanup in responses
REGEX_BOUNDARY_PATTERN: str = r"===WATER_BOUNDARY_START_(.*?)===WATER_BOUNDARY_END"  # Regex for extraction

# ═══════════════════════════════════════════════════════════════════════════
# TASK CANCELLATION & INTERRUPTION - V2.0 (Critical for stateful operation)
# ═══════════════════════════════════════════════════════════════════════════
ENABLE_TASK_CANCELLATION: bool = True  # Enable async task cancellation
TASK_CANCELLATION_GRACE_PERIOD: float = 2.0  # Grace period before force-cancel
ENABLE_PIPELINE_INTERRUPTION: bool = True  # Stop remaining modules when shell opens

# ═══════════════════════════════════════════════════════════════════════════
# AI & WAF BYPASS - V2.0 (Ollama integration)
# ═══════════════════════════════════════════════════════════════════════════
OLLAMA_API_URL: str = "http://localhost:11434/api/generate"
OLLAMA_MODEL_NAME: str = "deepseek-coder:1.3b"
OLLAMA_INFERENCE_TIMEOUT: float = 10.0
ENABLE_AI_BYPASS: bool = True  # Enable AI-driven WAF bypass

# ═══════════════════════════════════════════════════════════════════════════
# CONNECTION POOLING - V2.0 (Reduced for stability)
# ═══════════════════════════════════════════════════════════════════════════
TCP_POOL_LIMIT: int = 20  # REDUCED from 50
TCP_POOL_TTL: int = 300
CONNECTOR_FORCE_CLOSE: bool = False
CONNECTOR_ENABLE_CLEANUP: bool = True

# ═══════════════════════════════════════════════════════════════════════════
# BROWSER FINGERPRINTING - V2.0 (TLS impersonation)
# ═══════════════════════════════════════════════════════════════════════════
CURL_CFFI_BROWSER: str = "firefox"
COOKIE_REFRESH_THRESHOLD_MINUTES: int = 20
COOKIE_CACHE_TTL: int = 300  # 5 minutes

USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Android 10; Mobile; rv:126.0) Gecko/126.0 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
]

# ═══════════════════════════════════════════════════════════════════════════
# PAYLOAD & WORDLIST - V2.0
# ═══════════════════════════════════════════════════════════════════════════
TARGET_FILES_WORDLIST: List[str] = [
    ".env", ".env.bak", "wp-config.php.bak", "config.php.bak", ".git/config", "backup.sql"
]

# ═══════════════════════════════════════════════════════════════════════════
# INPUT VALIDATION & DEFENSIVE HARDENING - V2.0 (Critical security layer)
# ═══════════════════════════════════════════════════════════════════════════
ENABLE_INPUT_WHITELIST: bool = True  # Enable strict input validation
SHELL_META_CHAR_WHITELIST: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_./~:?#[]@!$&'()*+,;="
SHELL_META_CHAR_BLACKLIST: str = ";|&$`<>\\'\""  # Dangerous shell metacharacters
MAX_COMMAND_LENGTH: int = 2048  # Prevent buffer overflow

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING & DEBUG - V2.0
# ═══════════════════════════════════════════════════════════════════════════
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
ENABLE_DEBUG_LOGGING: bool = False
