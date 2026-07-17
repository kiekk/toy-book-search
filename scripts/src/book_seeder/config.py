import os
from pathlib import Path

from dotenv import load_dotenv

_SCRIPTS_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_SCRIPTS_ROOT / ".env")

ALADIN_TTB_KEY: str = os.getenv("ALADIN_TTB_KEY", "").strip()
KAKAO_REST_API_KEY: str = os.getenv("KAKAO_REST_API_KEY", "").strip()
