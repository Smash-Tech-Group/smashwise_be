"""
In-memory OTP store with per-purpose (signup/login) namespacing.

Each entry is keyed by (purpose, email) and stores:
  - otp:    the 6-digit code
  - expiry: a datetime after which the code is invalid

OTPs are invalidated immediately after successful verification or expiry.
"""

from datetime import datetime, timedelta
from threading import Lock
import random

_store: dict[tuple[str, str], dict] = {}
_lock = Lock()

OTP_TTL_SECONDS = 300  # 5 minutes


def _make_key(purpose: str, email: str) -> tuple[str, str]:
    return (purpose.lower(), email.lower())


def generate_otp(purpose: str, email: str) -> str:
    """Generate a new 6-digit OTP, store it, and return the code."""
    code = f"{random.randint(0, 999999):06d}"
    key = _make_key(purpose, email)
    expiry = datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS)
    with _lock:
        _store[key] = {"otp": code, "expiry": expiry}
    return code


def verify_otp(purpose: str, email: str, code: str) -> bool:
    """
    Verify the given code for (purpose, email).
    Returns True on success; False if not found, expired, or wrong code.
    Invalidates the OTP on success AND on expiry.
    """
    key = _make_key(purpose, email)
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return False
        if datetime.utcnow() > entry["expiry"]:
            del _store[key]  # remove expired entry
            return False
        if entry["otp"] != code:
            return False
        del _store[key]  # consumed successfully
        return True
