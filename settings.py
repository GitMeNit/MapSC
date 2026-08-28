"""Load API keys and other secrets from .env."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

COMTRADE_API_KEY = os.getenv("COMTRADE_API_KEY", "")
TRADE_GOV_API_KEY = os.getenv("TRADE_GOV_API_KEY", "")
USGS_API_KEY = os.getenv("USGS_API_KEY", "")
SEC_EDGAR_USER_AGENT = os.getenv("SEC_EDGAR_USER_AGENT", "")
