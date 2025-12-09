# Refactoring-Plan: captcha_handler.py modularisieren

> **Ziel:** Die monolithische `captcha_handler.py` (2383 Zeilen, ~30 Klassen) in eine saubere Python-Paketstruktur aufteilen.
> 
> **Status:** ✅ Abgeschlossen  
> **Geschätzter Aufwand:** 5-6 Arbeitstage  
> **Voraussetzung:** API-Anpassung (CaptchaSolverr v1) ist ✅ abgeschlossen
> **Abgeschlossen:** 2025-12-03

---

## Inhaltsverzeichnis

1. [Ausgangslage](#1-ausgangslage)
2. [Zielstruktur](#2-zielstruktur)
3. [Detaillierte Klassenverteilung](#3-detaillierte-klassenverteilung)
4. [Import-Hierarchie](#4-import-hierarchie)
5. [Phasenplan](#5-phasenplan)
6. [Code-Snippets für jedes Modul](#6-code-snippets-für-jedes-modul)
7. [Testplan](#7-testplan)
8. [Risiken & Mitigationen](#8-risiken--mitigationen)
9. [Checkliste](#9-checkliste)

---

## 1. Ausgangslage

### Aktuelle Datei: `captcha_helper/captcha_handler.py`

| Bereich | Zeilen | Klassen/Funktionen |
|---------|--------|-------------------|
| Imports | 1-69 | 25+ externe Imports |
| Enums | 72-89 | `CaptchaType`, `ServiceType`, `ProcessingResult` |
| Dataclasses | 92-164 | `CaptchaConfig`, `DecryptionRequest`, `DecryptionResult`, `AsyncJobState` |
| Pydantic Models | 131-202 | `DecryptionResponse`, `SolveRequest`, `SolveResponse`, `ResultResponse`, `CallbackPayload` |
| Exceptions | 204-207, 556-563 | `CaptchaException`, `ServiceNotSupportedException`, `DecryptionFailedException` |
| Job Store | 209-316 | `AsyncJobStore` (SQLite-basiert) |
| Job Registry | 319-553 | `AsyncJobRegistry` (Thread-safe, async workers) |
| Logging | 567-628 | `DashboardAccessFilter`, `UvicornFormatter`, `setup_logging()` |
| Utilities | 632-839 | `SecurityUtils`, `NetworkUtils`, `is_cloudflare_challenge()` |
| ABC Solvers | 842-868 | `CaptchaSolver`, `LinkDecryptor` |
| Solver Impl. | 871-998 | `DeathByCaptchaSolver`, `CutCaptchaV2Solver`, `RecaptchaV2Solver` |
| Decryptor Impl. | 1000-1618 | `CNLDecryptor`, `DLCDecryptor`, `FileCryptDecryptor`, `NoxDecryptor` |
| Processing Engine | 1621-1792 | `CaptchaProcessingEngine` |
| FastAPI App | 1794-2383 | `app`, Routes, `create_app()`, `main` |

---

## 2. Zielstruktur

```
captcha_helper/
├── __init__.py                    # Package exports & Version
├── app.py                         # FastAPI App, Lifespan, create_app()
├── routes/
│   ├── __init__.py
│   ├── v1.py                      # /v1/solve, /v1/status, /v1/result
│   ├── legacy.py                  # /solve, /status, /decrypt (Kompatibilität)
│   └── dashboard.py               # /dashboard, /cancel
├── models/
│   ├── __init__.py                # Re-exports
│   ├── enums.py                   # CaptchaType, ServiceType, ProcessingResult, JobStatus
│   ├── dataclasses.py             # CaptchaConfig, DecryptionRequest, DecryptionResult, AsyncJobState
│   └── schemas.py                 # Pydantic: SolveRequest, SolveResponse, etc.
├── exceptions.py                  # CaptchaException, ServiceNotSupportedException, DecryptionFailedException
├── logging_config.py              # DashboardAccessFilter, UvicornFormatter, setup_logging()
├── utils/
│   ├── __init__.py
│   ├── security.py                # SecurityUtils
│   └── network.py                 # NetworkUtils, is_cloudflare_challenge()
├── solvers/
│   ├── __init__.py                # Re-exports
│   ├── base.py                    # CaptchaSolver (ABC)
│   ├── deathbycaptcha.py          # DeathByCaptchaSolver
│   ├── cutcaptcha.py              # CutCaptchaV2Solver
│   └── recaptcha.py               # RecaptchaV2Solver
├── decryptors/
│   ├── __init__.py                # Re-exports
│   ├── base.py                    # LinkDecryptor (ABC)
│   ├── cnl.py                     # CNLDecryptor
│   ├── dlc.py                     # DLCDecryptor
│   ├── filecrypt.py               # FileCryptDecryptor (~400 Zeilen)
│   └── nox.py                     # NoxDecryptor (~140 Zeilen)
├── jobs/
│   ├── __init__.py                # Re-exports
│   ├── store.py                   # AsyncJobStore
│   └── registry.py                # AsyncJobRegistry
├── engine.py                      # CaptchaProcessingEngine
├── main.py                        # CLI Entry Point
├── captcha_handler.py             # FACADE: Re-exports für Abwärtskompatibilität
└── (bestehende Dateien bleiben)
    ├── capha_config.py
    ├── simple_monitoring.py
    ├── metrics_logger.py
    ├── request_tracker.py
    ├── dashboard.html
    ├── version.py
    └── captchas/
```

---

## 3. Detaillierte Klassenverteilung

### 3.1 `models/enums.py` (~30 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 72-148
from enum import Enum

class CaptchaType(Enum):
    CUTCAPTCHA_V2 = "cutcaptcha_v2"
    RECAPTCHA_V2 = "recaptcha_v2"
    CIRCLE_CAPTCHA = "circle_captcha"
    NO_CAPTCHA = "no_captcha"

class ServiceType(Enum):
    FILECRYPT = "filecrypt"
    NOX = "nox"
    UNKNOWN = "unknown"

class ProcessingResult(str, Enum):
    SUCCESS = "success"
    RETRY = "retry"
    FAILED = "failed"
    SKIPPED = "skipped"

class JobStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    QUEUED = "queued"
    PROCESSING = "processing"
    FINISHED = "finished"
    FAILED = "failed"
```

### 3.2 `models/dataclasses.py` (~80 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 92-164
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .enums import JobStatus

@dataclass
class CaptchaConfig:
    deathbycaptcha_token: str
    nox_user: str = ""
    nox_pass: str = ""
    flaresolverr_url: Optional[str] = None
    user_agent: str = "Mozilla/5.0 ..."
    request_timeout: int = 60
    retry_backoff: int = 5
    max_retries: int = 5

@dataclass
class DecryptionRequest:
    url: str
    mirror: Optional[str] = None
    title: str = ""
    password: str = ""
    package_id: str = ""
    
    def get_primary_url(self) -> str:
        return self.url

@dataclass
class DecryptionResult:
    success: bool
    urls: List[str] = field(default_factory=list)
    replace_url: Optional[str] = None
    mirror: Optional[str] = None
    session: Optional[str] = None
    error: Optional[str] = None
    processing_time: float = 0.0

@dataclass
class AsyncJobState:
    job_id: str
    captcha_type: str
    payload: Dict[str, Any]
    callback_url: Optional[str] = None
    timeout_seconds: int = 180
    status: JobStatus = JobStatus.QUEUED
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    duration_ms: Optional[int] = None
    callback_delivered: bool = False
```

### 3.3 `models/schemas.py` (~70 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 131-202, 1819-1835
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import AnyHttpUrl, BaseModel, Field

from .enums import JobStatus

class DecryptionResponse(BaseModel):
    status: int
    urls: List[str] = []
    replace_url: Optional[str] = None
    mirror: Optional[str] = None
    session: Optional[str] = None
    error: Optional[str] = None

class SolveRequest(BaseModel):
    captcha_type: str
    payload: Dict[str, Any]
    mode: Literal["sync", "async"] = "sync"
    callback_url: Optional[AnyHttpUrl] = None
    job_id: Optional[str] = Field(default=None, pattern=r"^[A-Za-z0-9_-]{4,64}$")
    timeout_seconds: int = Field(180, ge=10, le=3600)

class SolveResponse(BaseModel):
    status: Literal["finished", "queued", "error"]
    job_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    callback_delivered: bool = False
    created_at: datetime
    updated_at: datetime
    duration_ms: Optional[int] = None

class CallbackPayload(BaseModel):
    job_id: str
    status: Literal["finished", "failed"]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    version: str

class DecryptionRequestModel(BaseModel):
    payload: str
```

### 3.4 `exceptions.py` (~20 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 204-207, 556-563

class CaptchaException(Exception):
    """Base exception for captcha processing"""
    pass

class ServiceNotSupportedException(CaptchaException):
    """Raised when service is not supported"""
    pass

class DecryptionFailedException(CaptchaException):
    """Raised when decryption fails"""
    pass
```

### 3.5 `logging_config.py` (~70 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 567-628
import logging
import os

class DashboardAccessFilter(logging.Filter):
    FILTER_PATTERNS = ("GET /status", "GET /dashboard")
    
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(pattern in message for pattern in self.FILTER_PATTERNS)

class UvicornFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        return f"[CaptchaSolverr] {self.formatTime(record, '%Y-%m-%d %H:%M:%S')} [INFO] {msg}"

def configure_uvicorn_logging() -> None:
    access_logger = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, DashboardAccessFilter) for f in access_logger.filters):
        access_logger.addFilter(DashboardAccessFilter())
    for handler in access_logger.handlers:
        handler.setFormatter(UvicornFormatter())
    error_logger = logging.getLogger("uvicorn.error")
    for handler in error_logger.handlers:
        handler.setFormatter(UvicornFormatter())

def setup_logging() -> logging.Logger:
    logger = logging.getLogger("CaptchaSolverr")
    log_level_str = os.getenv("LOG_LEVEL") or os.getenv("CAPHA_LOG_LEVEL", "INFO")
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            '[CaptchaSolverr] %(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.propagate = False
    return logger
```

### 3.6 `utils/security.py` (~50 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 632-670
import base64

class SecurityUtils:
    @staticmethod
    def encode_base64_custom(data: str) -> str:
        return base64.b64encode(data.encode("utf-8")).decode().replace("/", "-")
    
    @staticmethod
    def decode_base64_custom(data: str) -> str:
        data = data.replace("-", "/")
        return base64.b64decode(data).decode()
    
    @staticmethod
    def mask_sensitive_data(value: str) -> str:
        if not isinstance(value, str):
            return ""
        if len(value) > 20:
            return f"{value[0]}*<<<LENGTH:{len(value):03d}>>>*{value[-1]}"
        elif len(value) <= 2:
            return value
        else:
            return value[0] + "*" * (len(value) - 2) + value[-1]
    
    @staticmethod
    def normalize_url(url: str) -> str:
        return (
            url.replace("https://", "")
            .replace("www.", "")
            .replace("filecrypt.cc", "")
            .replace("filecrypt.to", "")
            .replace("filecrypt.co", "")
            .split("?")[0]
        )
```

### 3.7 `utils/network.py` (~170 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 672-839
import os
import requests
from bs4 import BeautifulSoup
from typing import Optional

from ..models.dataclasses import CaptchaConfig
from ..logging_config import setup_logging

logger = setup_logging()

def is_cloudflare_challenge(html: str) -> bool:
    # ... (Zeilen 672-697)
    pass

class NetworkUtils:
    @staticmethod
    async def fetch_with_retry(url: str, config: CaptchaConfig, ...) -> Optional[str]:
        # ... (Zeilen 700-839)
        pass
    
    @staticmethod
    def _initialize_flaresolverr(config: CaptchaConfig) -> None:
        # ... (Zeilen 800-839)
        pass
```

### 3.8 `solvers/base.py` (~30 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 842-868
from abc import ABC, abstractmethod
from typing import Optional

from ..models.enums import CaptchaType
from ..models.dataclasses import CaptchaConfig

class CaptchaSolver(ABC):
    @abstractmethod
    async def solve(self, config: CaptchaConfig, url: str) -> Optional[str]:
        pass
    
    @abstractmethod
    def get_captcha_type(self) -> CaptchaType:
        pass
```

### 3.9 `solvers/deathbycaptcha.py` (~100 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 871-970
import asyncio
import json
import re
import requests
from typing import Any, Dict, Optional

from ..models.enums import CaptchaType
from ..models.dataclasses import CaptchaConfig
from ..exceptions import CaptchaException, DecryptionFailedException
from ..logging_config import setup_logging
from .base import CaptchaSolver

try:
    from captchas import deathbycaptcha
except ImportError:
    from captcha_helper.captchas import deathbycaptcha

logger = setup_logging()

class DeathByCaptchaSolver(CaptchaSolver):
    def __init__(self, captcha_type: CaptchaType):
        self.captcha_type = captcha_type
    
    def get_captcha_type(self) -> CaptchaType:
        return self.captcha_type
    
    async def solve(self, config: CaptchaConfig, url: str) -> Optional[str]:
        # ... (Zeilen 880-931)
        pass
    
    def _create_payload(self, url: str, config: CaptchaConfig) -> Dict[str, Any]:
        # ... (Zeilen 933-950)
        pass
    
    def _get_captcha_type_id(self) -> int:
        return 19 if self.captcha_type == CaptchaType.CUTCAPTCHA_V2 else 4
    
    def _transform_nox_url(self, url: str) -> str:
        # ... (Zeilen 956-959)
        pass
    
    def _get_misery_key(self, api_key: str) -> str:
        # ... (Zeilen 961-969)
        pass
```

### 3.10 `solvers/cutcaptcha.py` & `solvers/recaptcha.py` (je ~20 Zeilen)

```python
# cutcaptcha.py - Zeilen 972-984
from ..models.enums import CaptchaType
from ..models.dataclasses import CaptchaConfig
from .base import CaptchaSolver
from .deathbycaptcha import DeathByCaptchaSolver

class CutCaptchaV2Solver(CaptchaSolver):
    API_KEY = "SAs61IAI"
    
    def __init__(self) -> None:
        self._dbc_solver = DeathByCaptchaSolver(CaptchaType.CUTCAPTCHA_V2)
    
    def get_captcha_type(self) -> CaptchaType:
        return CaptchaType.CUTCAPTCHA_V2
    
    async def solve(self, config: CaptchaConfig, url: str):
        return await self._dbc_solver.solve(config, url)
```

### 3.11 `decryptors/base.py` (~20 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 856-868
from abc import ABC, abstractmethod

from ..models.enums import ServiceType
from ..models.dataclasses import DecryptionRequest, DecryptionResult, CaptchaConfig

class LinkDecryptor(ABC):
    @abstractmethod
    async def decrypt_links(self, request: DecryptionRequest, token: str, config: CaptchaConfig) -> DecryptionResult:
        pass
    
    @abstractmethod
    def get_service_type(self) -> ServiceType:
        pass
```

### 3.12 `decryptors/cnl.py` (~50 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 1000-1038
import base64
from typing import List

import dukpy
from Cryptodome.Cipher import AES

from ..exceptions import DecryptionFailedException

class CNLDecryptor:
    @staticmethod
    def evaluate_javascript(js_function: str) -> str:
        js_code = f"{js_function}\nf();"
        return dukpy.evaljs(js_code).strip()
    
    @staticmethod
    def aes_decrypt_data(encrypted_data: str, key_hex: str) -> str:
        # ... (Zeilen 1013-1026)
        pass
    
    @staticmethod
    def decrypt_cnl_data(crypted_data: List[str]) -> List[str]:
        # ... (Zeilen 1029-1038)
        pass
```

### 3.13 `decryptors/dlc.py` (~50 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 1040-1087
import base64
import xml.etree.ElementTree as ET
from typing import Optional

from Cryptodome.Cipher import AES

from ..logging_config import setup_logging

logger = setup_logging()

class DLCDecryptor:
    DLC_KEY = b"cb99b5cbc24db398"
    DLC_IV = b"9837f5c9a3a5b8f2"
    
    @staticmethod
    def decrypt_dlc_content(encrypted_content: str) -> Optional[str]:
        # ... (Zeilen 1050-1087)
        pass
```

### 3.14 `decryptors/filecrypt.py` (~400 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 1089-1477
# GRÖSSTE KLASSE - sorgfältig extrahieren!

import asyncio
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, urljoin, parse_qs

import aiohttp
import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from ..models.enums import ServiceType, CaptchaType
from ..models.dataclasses import DecryptionRequest, DecryptionResult, CaptchaConfig
from ..exceptions import DecryptionFailedException
from ..logging_config import setup_logging
from ..utils.network import is_cloudflare_challenge
from .base import LinkDecryptor
from .cnl import CNLDecryptor
from .dlc import DLCDecryptor

logger = setup_logging()

class FileCryptDecryptor(LinkDecryptor):
    def get_service_type(self) -> ServiceType:
        return ServiceType.FILECRYPT
    
    async def decrypt_links(self, request: DecryptionRequest, token: str, config: CaptchaConfig) -> DecryptionResult:
        # ... (Zeilen 1095-1477)
        pass
    
    # Alle privaten Methoden:
    # _get_session_cookies()
    # _fetch_page()
    # _extract_cnl_data()
    # _extract_dlc_links()
    # _extract_web_links()
    # _process_mirror()
    # etc.
```

### 3.15 `decryptors/nox.py` (~140 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 1479-1618
import asyncio
from typing import Any, Dict, Optional

import requests

from ..models.enums import ServiceType
from ..models.dataclasses import DecryptionRequest, DecryptionResult, CaptchaConfig
from ..logging_config import setup_logging
from .base import LinkDecryptor

logger = setup_logging()

class NoxDecryptor(LinkDecryptor):
    def __init__(self) -> None:
        self._session: Optional[requests.Session] = None
        self._session_valid = False
    
    def get_service_type(self) -> ServiceType:
        return ServiceType.NOX
    
    async def decrypt_links(self, request: DecryptionRequest, token: str, config: CaptchaConfig) -> DecryptionResult:
        # ... (Zeilen 1490-1600)
        pass
    
    async def _ensure_session(self, config: CaptchaConfig) -> requests.Session:
        # ... (Zeilen 1580-1603)
        pass
    
    def _login(self, session: requests.Session, config: CaptchaConfig) -> Dict[str, Any]:
        # ... (Zeilen 1605-1618)
        pass
```

### 3.16 `jobs/store.py` (~120 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 209-316
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..models.dataclasses import AsyncJobState
from ..models.enums import JobStatus

try:
    from capha_config import DEFAULT_DB_PATH
except ImportError:
    from captcha_helper.capha_config import DEFAULT_DB_PATH

class AsyncJobStore:
    TABLE_NAME = "async_jobs"
    
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_table()
    
    def _ensure_table(self) -> None:
        # ... (Zeilen 220-240)
        pass
    
    def upsert(self, job: AsyncJobState) -> None:
        # ... (Zeilen 242-278)
        pass
    
    def delete(self, job_id: str) -> None:
        # ... (Zeilen 280-286)
        pass
    
    def load_jobs(self) -> List[AsyncJobState]:
        # ... (Zeilen 288-316)
        pass
```

### 3.17 `jobs/registry.py` (~230 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 319-553
import asyncio
import secrets
from datetime import datetime
from typing import Any, Dict, Optional

from ..models.dataclasses import AsyncJobState
from ..models.enums import JobStatus
from ..logging_config import setup_logging
from .store import AsyncJobStore

logger = setup_logging()

# Globale Variablen
job_store: Optional[AsyncJobStore] = None
_async_job_queue: Optional[asyncio.Queue] = None
_async_workers: list = []
async_worker_target: int = 3
_async_runtime_ready: bool = False

def _generate_job_id() -> str:
    return secrets.token_urlsafe(12)

class AsyncJobRegistry:
    def __init__(self, store: AsyncJobStore) -> None:
        self._store = store
        self._jobs: Dict[str, AsyncJobState] = {}
        self._lock = asyncio.Lock()
        self._load_persisted_jobs()
    
    # ... alle Methoden (Zeilen 330-553)
    
    async def create_job(...) -> AsyncJobState:
        pass
    
    async def get_job(job_id: str) -> Optional[AsyncJobState]:
        pass
    
    async def update_job(...) -> Optional[AsyncJobState]:
        pass
    
    # etc.

# Globale Registry-Instanz
job_registry: Optional[AsyncJobRegistry] = None

async def enqueue_async_job(job_id: str) -> None:
    # ... (Zeilen 480-490)
    pass

async def start_async_job_workers(target_count: int) -> None:
    # ... (Zeilen 500-530)
    pass

async def _resume_pending_jobs() -> None:
    # ... (Zeilen 540-553)
    pass

async def _ensure_async_runtime_ready() -> None:
    # ... (Zeilen 545-553)
    pass
```

### 3.18 `engine.py` (~180 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 1621-1792
import asyncio
from typing import Any, Dict, Optional, Tuple

from .models.enums import CaptchaType, ServiceType, ProcessingResult
from .models.dataclasses import CaptchaConfig, DecryptionRequest, DecryptionResult
from .models.schemas import DecryptionResponse
from .exceptions import DecryptionFailedException
from .logging_config import setup_logging
from .solvers import CutCaptchaV2Solver, RecaptchaV2Solver
from .decryptors import FileCryptDecryptor, NoxDecryptor

try:
    from captchas.circlecaptcha import CircleCaptchaSolver
except ImportError:
    from captcha_helper.captchas.circlecaptcha import CircleCaptchaSolver

logger = setup_logging()

class CaptchaProcessingEngine:
    def __init__(self, config: CaptchaConfig):
        self.config = config
        self.processing_lock = asyncio.Lock()
        
        self.solvers = {
            CaptchaType.CUTCAPTCHA_V2: CutCaptchaV2Solver(),
            CaptchaType.RECAPTCHA_V2: RecaptchaV2Solver(),
            CaptchaType.CIRCLE_CAPTCHA: CircleCaptchaSolver()
        }
        
        self.decryptors = {
            ServiceType.FILECRYPT: FileCryptDecryptor(),
            ServiceType.NOX: NoxDecryptor()
        }
    
    def _detect_service_type(self, url: str) -> ServiceType:
        # ... (Zeilen 1641-1649)
        pass
    
    def _detect_captcha_type(self, url: str) -> CaptchaType:
        # ... (Zeilen 1651-1659)
        pass
    
    async def process_decryption_request(self, request: DecryptionRequest) -> DecryptionResult:
        # ... (Zeilen 1661-1701)
        pass
    
    async def process_external_payload(self, raw_payload: Dict[str, Any], job_id: Optional[str] = None) -> Tuple[ProcessingResult, Optional[DecryptionResponse]]:
        # ... (Zeilen 1703-1792)
        pass
```

### 3.19 `routes/v1.py` (~100 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 1851-1892, 2095-2190
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from ..models.schemas import SolveRequest, SolveResponse, ResultResponse
from ..models.enums import JobStatus
from ..jobs.registry import job_registry
from ..logging_config import setup_logging

logger = setup_logging()
router = APIRouter(prefix="/v1", tags=["v1"])

@router.get("/status")
async def v1_status():
    # ... (Zeilen 1853-1874)
    pass

@router.post("/solve", response_model=SolveResponse)
async def v1_solve(request_body: SolveRequest, background_tasks: BackgroundTasks, request: Request):
    # ... (Zeilen 1877-1885)
    pass

@router.get("/result/{job_id}", response_model=ResultResponse)
async def v1_result(job_id: str):
    # ... (Zeilen 1888-1891)
    pass

@router.post("/callback/{job_id}")
async def generic_callback(job_id: str, request: Request):
    # ... (Zeilen 2095-2190)
    pass
```

### 3.20 `routes/legacy.py` (~200 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 1896-2093, 2204-2303
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from ..models.schemas import SolveRequest, SolveResponse, ResultResponse, CallbackPayload, DecryptionResponse
from ..logging_config import setup_logging

logger = setup_logging()
router = APIRouter(tags=["legacy"])

@router.post("/solve", response_model=SolveResponse)
async def solve_request_endpoint(...):
    # ... (Zeilen 1896-1958)
    pass

@router.get("/result/{job_id}", response_model=ResultResponse)
async def get_job_result(job_id: str):
    # ... (Zeilen 1961-1966)
    pass

@router.post("/callback", response_model=ResultResponse)
async def job_callback(payload: CallbackPayload, background_tasks: BackgroundTasks):
    # ... (Zeilen 1969-2001)
    pass

@router.get("/status")
async def get_status():
    # ... (Zeilen 2004-2092)
    pass

@router.post("/decrypt/{payload}", response_model=DecryptionResponse)
async def decrypt_payload(payload: str, background_tasks: BackgroundTasks):
    # ... (Zeilen 2214-2303)
    pass
```

### 3.21 `routes/dashboard.py` (~30 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 2193-2211
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard"])

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    try:
        dashboard_path = Path(__file__).parent.parent / "dashboard.html"
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard nicht gefunden</h1>", status_code=404)

@router.delete("/cancel/{request_id}")
async def cancel_request(request_id: str):
    # ... (Zeilen 2204-2211)
    pass
```

### 3.22 `app.py` (~100 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 1794-1817, 2306-2322
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

from .models.dataclasses import CaptchaConfig
from .engine import CaptchaProcessingEngine
from .jobs.registry import _ensure_async_runtime_ready
from .logging_config import setup_logging
from .routes import v1, legacy, dashboard
from .utils.network import _initialize_flaresolverr

try:
    from version import CAPTCHA_HANDLER_VERSION
except ImportError:
    from captcha_helper.version import CAPTCHA_HANDLER_VERSION

try:
    from metrics_logger import metrics_logger
except ImportError:
    from captcha_helper.metrics_logger import metrics_logger

logger = setup_logging()

# Global state
engine: Optional[CaptchaProcessingEngine] = None
processing_semaphore: Optional[asyncio.Semaphore] = None
max_concurrent_requests = 3
active_requests_count = 0
requests_lock: Optional[asyncio.Lock] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    await _ensure_async_runtime_ready()
    await metrics_logger.start()
    logger.info("Metrics logger started")
    yield
    await metrics_logger.stop()
    logger.info("Metrics logger stopped")

def create_app(config: CaptchaConfig) -> FastAPI:
    global engine, processing_semaphore, requests_lock
    
    _initialize_flaresolverr(config)
    
    engine = CaptchaProcessingEngine(config)
    processing_semaphore = asyncio.Semaphore(max_concurrent_requests)
    requests_lock = asyncio.Lock()
    
    app = FastAPI(title="CaptchaSolverr", version=CAPTCHA_HANDLER_VERSION, lifespan=lifespan)
    
    # Include routers
    app.include_router(v1.router)
    app.include_router(legacy.router)
    app.include_router(dashboard.router)
    
    @app.get("/")
    async def root():
        return {
            "service": "CaptchaSolverr",
            "version": CAPTCHA_HANDLER_VERSION,
            "status": "running",
            "docs": "/docs",
            "api_version": "v1"
        }
    
    return app

# Default app instance
app = FastAPI(title="CaptchaSolverr", version=CAPTCHA_HANDLER_VERSION, lifespan=lifespan)
```

### 3.23 `main.py` (~60 Zeilen)

```python
# Zu extrahieren aus captcha_handler.py Zeilen 2327-2383
import argparse
import asyncio
import os

import uvicorn

from .models.dataclasses import CaptchaConfig
from .app import create_app, app, max_concurrent_requests
from .utils.security import SecurityUtils
from .logging_config import setup_logging

try:
    from version import CAPTCHA_HANDLER_VERSION
except ImportError:
    from captcha_helper.version import CAPTCHA_HANDLER_VERSION

try:
    from request_tracker import request_tracker
except ImportError:
    from captcha_helper.request_tracker import request_tracker

logger = setup_logging()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deathbycaptcha_token", help="DeathByCaptcha Authentication Token")
    parser.add_argument("--nox_user", help="NX username")
    parser.add_argument("--nox_pass", help="NX password")
    parser.add_argument("--port", type=int, default=9700, help="Server port")
    parser.add_argument("--max_concurrent", type=int, default=3, help="Maximum concurrent requests")
    parser.add_argument("--flaresolverr_url", help="Optional FlareSolverr endpoint")
    parser.add_argument("--retry_backoff", type=int, default=5, help="Retry backoff in seconds")
    args = parser.parse_args()
    
    config = CaptchaConfig(
        deathbycaptcha_token=args.deathbycaptcha_token or "",
        nox_user=args.nox_user or "",
        nox_pass=args.nox_pass or "",
        flaresolverr_url=args.flaresolverr_url or os.getenv("FLARESOLVERR_URL"),
        retry_backoff=args.retry_backoff,
    )
    
    global max_concurrent_requests
    max_concurrent_requests = args.max_concurrent
    
    # Print startup banner
    # ... (Zeilen 2352-2364)
    
    create_app(config)
    
    async def start_tracker():
        await request_tracker.start_monitoring()
    
    asyncio.run(start_tracker())
    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()
```

### 3.24 `captcha_handler.py` (FACADE - ~50 Zeilen)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FACADE MODULE - Für Abwärtskompatibilität.

Dieses Modul re-exportiert alle öffentlichen Klassen und Funktionen
aus den neuen Submodulen, damit bestehender Code weiterhin funktioniert.

DEPRECATED: Importiere direkt aus den Submodulen:
    from captcha_helper.models import CaptchaType, CaptchaConfig
    from captcha_helper.engine import CaptchaProcessingEngine
    from captcha_helper.app import create_app, app
"""

# Models
from captcha_helper.models.enums import CaptchaType, ServiceType, ProcessingResult, JobStatus
from captcha_helper.models.dataclasses import CaptchaConfig, DecryptionRequest, DecryptionResult, AsyncJobState
from captcha_helper.models.schemas import (
    SolveRequest, SolveResponse, ResultResponse, CallbackPayload,
    DecryptionResponse, StatusResponse, DecryptionRequestModel
)

# Exceptions
from captcha_helper.exceptions import CaptchaException, ServiceNotSupportedException, DecryptionFailedException

# Logging
from captcha_helper.logging_config import setup_logging, configure_uvicorn_logging, DashboardAccessFilter, UvicornFormatter

# Utils
from captcha_helper.utils.security import SecurityUtils
from captcha_helper.utils.network import NetworkUtils, is_cloudflare_challenge

# Solvers
from captcha_helper.solvers.base import CaptchaSolver
from captcha_helper.solvers.deathbycaptcha import DeathByCaptchaSolver
from captcha_helper.solvers.cutcaptcha import CutCaptchaV2Solver
from captcha_helper.solvers.recaptcha import RecaptchaV2Solver

# Decryptors
from captcha_helper.decryptors.base import LinkDecryptor
from captcha_helper.decryptors.cnl import CNLDecryptor
from captcha_helper.decryptors.dlc import DLCDecryptor
from captcha_helper.decryptors.filecrypt import FileCryptDecryptor
from captcha_helper.decryptors.nox import NoxDecryptor

# Jobs
from captcha_helper.jobs.store import AsyncJobStore
from captcha_helper.jobs.registry import AsyncJobRegistry, job_registry, enqueue_async_job

# Engine
from captcha_helper.engine import CaptchaProcessingEngine

# App
from captcha_helper.app import create_app, app, lifespan

# Version
try:
    from version import CAPTCHA_HANDLER_VERSION
except ImportError:
    from captcha_helper.version import CAPTCHA_HANDLER_VERSION

logger = setup_logging()

__all__ = [
    # Enums
    "CaptchaType", "ServiceType", "ProcessingResult", "JobStatus",
    # Dataclasses
    "CaptchaConfig", "DecryptionRequest", "DecryptionResult", "AsyncJobState",
    # Schemas
    "SolveRequest", "SolveResponse", "ResultResponse", "CallbackPayload",
    "DecryptionResponse", "StatusResponse", "DecryptionRequestModel",
    # Exceptions
    "CaptchaException", "ServiceNotSupportedException", "DecryptionFailedException",
    # Logging
    "setup_logging", "configure_uvicorn_logging", "DashboardAccessFilter", "UvicornFormatter", "logger",
    # Utils
    "SecurityUtils", "NetworkUtils", "is_cloudflare_challenge",
    # Solvers
    "CaptchaSolver", "DeathByCaptchaSolver", "CutCaptchaV2Solver", "RecaptchaV2Solver",
    # Decryptors
    "LinkDecryptor", "CNLDecryptor", "DLCDecryptor", "FileCryptDecryptor", "NoxDecryptor",
    # Jobs
    "AsyncJobStore", "AsyncJobRegistry", "job_registry", "enqueue_async_job",
    # Engine
    "CaptchaProcessingEngine",
    # App
    "create_app", "app", "lifespan",
    # Version
    "CAPTCHA_HANDLER_VERSION",
]
```

---

## 4. Import-Hierarchie

Um zirkuläre Imports zu vermeiden, muss diese Hierarchie eingehalten werden:

```
Level 0 (keine Abhängigkeiten):
├── models/enums.py
├── exceptions.py
└── version.py

Level 1 (nur Level 0):
├── models/dataclasses.py  → enums
├── models/schemas.py      → enums
└── logging_config.py      → (keine)

Level 2 (Level 0-1):
├── utils/security.py      → (keine)
├── utils/network.py       → logging_config, models
├── jobs/store.py          → models
└── solvers/base.py        → models

Level 3 (Level 0-2):
├── solvers/deathbycaptcha.py → base, models, exceptions, logging
├── solvers/cutcaptcha.py     → base, deathbycaptcha
├── solvers/recaptcha.py      → base, deathbycaptcha
├── decryptors/base.py        → models
├── decryptors/cnl.py         → exceptions
├── decryptors/dlc.py         → logging
└── jobs/registry.py          → store, models, logging

Level 4 (Level 0-3):
├── decryptors/filecrypt.py → base, cnl, dlc, models, logging, utils
├── decryptors/nox.py       → base, models, logging
└── engine.py               → models, solvers, decryptors, logging

Level 5 (Level 0-4):
├── routes/v1.py      → models, jobs, logging
├── routes/legacy.py  → models, jobs, engine, logging
├── routes/dashboard.py → (keine)
└── app.py            → engine, jobs, routes, logging, utils

Level 6 (Level 0-5):
├── main.py           → app, models, utils, logging
└── captcha_handler.py (FACADE) → alles
```

### TYPE_CHECKING für Forward References

Bei Bedarf `TYPE_CHECKING` verwenden:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine import CaptchaProcessingEngine
```

---

## 5. Phasenplan

### Phase 1 – Vorbereitung (0.5 Tage) ✅
- [x] Git-Branch erstellen: `feature/refactor-captcha-handler`
- [x] Verzeichnisstruktur anlegen (leere `__init__.py` Dateien)
- [x] Backup der aktuellen `captcha_handler.py`

### Phase 2 – Models & Exceptions (0.5 Tage) ✅
- [x] `models/enums.py` erstellen
- [x] `models/dataclasses.py` erstellen
- [x] `models/schemas.py` erstellen
- [x] `models/__init__.py` mit Re-Exports
- [x] `exceptions.py` erstellen
- [x] **Test:** Imports aus neuen Modulen prüfen

### Phase 3 – Logging & Utils (0.5 Tage) ✅
- [x] `logging_config.py` erstellen
- [x] `utils/security.py` erstellen
- [x] `utils/network.py` erstellen
- [x] `utils/__init__.py` mit Re-Exports
- [x] **Test:** Logger funktioniert

### Phase 4 – Solvers (0.5 Tage) ✅
- [x] `solvers/base.py` erstellen
- [x] `solvers/deathbycaptcha.py` erstellen
- [x] `solvers/cutcaptcha.py` erstellen
- [x] `solvers/recaptcha.py` erstellen
- [x] `solvers/__init__.py` mit Re-Exports
- [x] **Test:** DeathByCaptcha-Solver initialisierbar

### Phase 5 – Decryptors (1 Tag) ✅
- [x] `decryptors/base.py` erstellen
- [x] `decryptors/cnl.py` erstellen
- [x] `decryptors/dlc.py` erstellen
- [x] `decryptors/filecrypt.py` erstellen (GRÖSSTE DATEI!)
- [x] `decryptors/nox.py` erstellen
- [x] `decryptors/__init__.py` mit Re-Exports
- [x] **Test:** FileCryptDecryptor initialisierbar

### Phase 6 – Jobs (0.5 Tage) ✅
- [x] `jobs/store.py` erstellen
- [x] `jobs/registry.py` erstellen
- [x] `jobs/__init__.py` mit Re-Exports
- [x] **Test:** Job-Store SQLite funktioniert

### Phase 7 – Engine (0.5 Tage) ✅
- [x] `engine.py` erstellen
- [x] **Test:** Engine initialisierbar mit Config

### Phase 8 – Routes & App (1 Tag) ✅
- [x] `routes/v1.py` erstellen
- [x] `routes/legacy.py` erstellen
- [x] `routes/dashboard.py` erstellen
- [x] `routes/__init__.py` mit Re-Exports
- [x] `app.py` erstellen
- [x] `main.py` erstellen
- [x] **Test:** FastAPI App startet

### Phase 9 – Integration (1 Tag) ✅
- [x] `captcha_handler.py` als FACADE umschreiben
- [x] Alle Imports in Docker-Entrypoint prüfen
- [x] `__init__.py` im Root-Package aktualisieren
- [x] **Test:** Docker-Build erfolgreich
- [x] **Test:** Alle API-Endpoints funktionieren

### Phase 10 – Cleanup & Dokumentation (0.5 Tage) ✅
- [x] Alte `captcha_handler.py` archivieren
- [x] README.md aktualisieren
- [x] Docstrings vervollständigen
- [ ] PR erstellen und Review

---

## 6. Code-Snippets für jedes Modul

> Die vollständigen Code-Snippets sind in Abschnitt 3 dokumentiert.

---

## 7. Testplan

### Unit Tests (pro Modul)

```bash
# Nach jeder Phase ausführen:
cd captcha_helper
python -c "from models import CaptchaType, CaptchaConfig; print('Models OK')"
python -c "from exceptions import CaptchaException; print('Exceptions OK')"
python -c "from logging_config import setup_logging; print('Logging OK')"
python -c "from utils import SecurityUtils; print('Utils OK')"
python -c "from solvers import CutCaptchaV2Solver; print('Solvers OK')"
python -c "from decryptors import FileCryptDecryptor; print('Decryptors OK')"
python -c "from jobs import AsyncJobStore; print('Jobs OK')"
python -c "from engine import CaptchaProcessingEngine; print('Engine OK')"
python -c "from app import create_app; print('App OK')"
```

### Integration Tests

```bash
# Docker-Build testen
cd captcha_helper
docker build -f docker/Dockerfile.dev -t weedo078/capha:refactor-test .

# Container starten
docker run -d --name capha-test -p 9700:9700 \
  -e DEATHBYCAPTCHA_TOKEN=test \
  weedo078/capha:refactor-test

# API-Endpoints testen
curl http://localhost:9700/v1/status
curl http://localhost:9700/status
curl http://localhost:9700/

# Cleanup
docker stop capha-test && docker rm capha-test
```

### Regressionstests

- [ ] `/v1/solve` (async mode)
- [ ] `/v1/solve` (sync mode)
- [ ] `/v1/result/{job_id}`
- [ ] `/v1/status`
- [ ] `/solve` (legacy)
- [ ] `/status` (legacy)
- [ ] `/decrypt/{payload}` (legacy)
- [ ] `/dashboard`
- [ ] `/cancel/{request_id}`

---

## 8. Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Zirkuläre Imports | Mittel | Hoch | Import-Hierarchie strikt einhalten, TYPE_CHECKING nutzen |
| Broken Docker-Build | Mittel | Hoch | Nach jeder Phase Docker-Build testen |
| Fehlende Imports | Hoch | Mittel | Alle `__init__.py` mit vollständigen Re-Exports |
| Kompatibilitätsbruch | Niedrig | Hoch | FACADE-Modul behält alle alten Imports |
| Performance-Regression | Niedrig | Mittel | Keine Logik-Änderungen, nur Strukturierung |

---

## 9. Checkliste

### Vor dem Start
- [ ] Git-Branch erstellt
- [ ] Backup der aktuellen Dateien
- [ ] Verzeichnisstruktur angelegt

### Während der Umsetzung
- [ ] Nach jeder Phase: Import-Test
- [ ] Nach jeder Phase: Docker-Build-Test
- [ ] Keine Logik-Änderungen (nur Verschiebungen)

### Nach Abschluss
- [ ] Alle API-Endpoints funktionieren
- [ ] Docker-Build erfolgreich
- [ ] Keine Deprecation-Warnings
- [ ] README aktualisiert
- [ ] PR erstellt

---

## Anhang: Dateigrößen-Schätzung

| Modul | Zeilen | Dateien |
|-------|--------|---------|
| `models/` | ~180 | 4 |
| `exceptions.py` | ~20 | 1 |
| `logging_config.py` | ~70 | 1 |
| `utils/` | ~220 | 3 |
| `solvers/` | ~200 | 5 |
| `decryptors/` | ~660 | 6 |
| `jobs/` | ~350 | 3 |
| `engine.py` | ~180 | 1 |
| `routes/` | ~330 | 4 |
| `app.py` | ~100 | 1 |
| `main.py` | ~60 | 1 |
| `captcha_handler.py` (FACADE) | ~80 | 1 |
| **Gesamt** | ~2450 | 31 |

---

*Erstellt: 2025-12-03*  
*Letzte Aktualisierung: 2025-12-03*
