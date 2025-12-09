# -*- coding: utf-8 -*-
"""Legacy-Modul für CapHa-Client.

DEPRECATED: Dieses Modul ist veraltet und wird nur für Abwärtskompatibilität beibehalten.
Bitte verwende stattdessen `captchasolverr_client.py`.

Alle Klassen und Funktionen werden aus dem neuen Modul re-exportiert.
"""

from __future__ import annotations

# Re-export aus dem neuen Modul für Abwärtskompatibilität
from kuasarr.providers.captchasolverr_client import (
    CaptchaSolverrClient as CaphaClient,
    CaptchaSolverrError as CaphaClientError,
    create_captchasolverr_client as create_capha_client_from_state,
)

__all__ = ["CaphaClient", "CaphaClientError", "create_capha_client_from_state"]
