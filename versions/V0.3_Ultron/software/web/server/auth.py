"""Authentication for the Ultron V0.3 web control system.

Roles:
  - 'user'           : granted by the 4-digit user PIN (user control panel).
  - 'admin'          : granted by the admin dashboard password (read-only
                       admin view; the demo-style data collection dashboard).
  - 'admin_control'  : granted ONLY by the 10-character admin override
                       password. This is the single capability that lets the
                       admin operate the robot / see live camera+sensors.
                       It must never be granted by the regular admin login.

Admin password: 10 characters, hashed (PBKDF2-HMAC-SHA256) — never stored
plaintext. The user PIN is 4 digits, verified against a hash, and ALSO kept
in the settings store (server-side only) so the admin can view/change it —
this is a deliberate, documented trade-off for the pilot control gate.

Login attempts are rate-limited per IP to blunt brute force.
"""

import base64
import hashlib
import hmac
import os
import secrets
import threading
import time

PIN_RANGE = (0, 9999)
ADMIN_PASSWORD_LEN = 10
TOKEN_TTL_S = 8 * 3600
_ITERATIONS = 200_000


class AuthError(Exception):
    pass


def _salt():
    return os.urandom(16)


def hash_secret(secret: str, salt: bytes):
    return hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"),
                               salt, _ITERATIONS).hex()


def verify_secret(secret: str, salt: bytes, expected_hex: str):
    return hmac.compare_digest(hash_secret(secret, salt), expected_hex)


def pin_ok(pin: str) -> bool:
    return (isinstance(pin, str) and len(pin) == 4 and pin.isdigit())


def admin_password_ok(pw: str) -> bool:
    return isinstance(pw, str) and len(pw) == ADMIN_PASSWORD_LEN


# ---- token helpers (HMAC-signed, no external deps) -------------------------
class Token:
    def __init__(self, secret: bytes):
        self.secret = secret

    def issue(self, role: str, identity: str) -> str:
        payload = base64.urlsafe_b64encode(
            f"{role}:{identity}:{int(time.time()) + TOKEN_TTL_S}".encode())
        sig = hmac.new(self.secret, payload, hashlib.sha256).digest()
        return payload.decode() + "." + base64.urlsafe_b64encode(sig).decode()

    def verify(self, token: str):
        try:
            payload, sig = token.split(".")
            expected = hmac.new(self.secret, payload.encode(),
                                hashlib.sha256).digest()
            if not hmac.compare_digest(
                    base64.urlsafe_b64decode(sig), expected):
                return None
            role, identity, exp = base64.urlsafe_b64decode(
                payload.encode()).decode().split(":")
            if int(exp) < time.time():
                return None
            return {"role": role, "identity": identity}
        except Exception:
            return None


class LoginRateLimiter:
    """Simple in-memory per-IP rate limiter for login endpoints."""

    def __init__(self, max_attempts=5, window_s=60, lockout_s=60):
        self.max_attempts = max_attempts
        self.window_s = window_s
        self.lockout_s = lockout_s
        self._hits = {}        # ip -> [timestamps]
        self._lock = threading.Lock()

    def allow(self, ip: str) -> bool:
        now = time.time()
        with self._lock:
            stamps = [t for t in self._hits.get(ip, [])
                      if now - t < self.window_s]
            if len(stamps) >= self.max_attempts:
                # lockout: require silence for lockout_s
                last = max(stamps)
                return (now - last) > self.lockout_s
            self._hits[ip] = stamps
            return True

    def hit(self, ip: str):
        now = time.time()
        with self._lock:
            self._hits.setdefault(ip, []).append(now)


def new_admin_password() -> str:
    """Generate a 10-char admin password (human-readable, no ambiguous)."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(ADMIN_PASSWORD_LEN))


def new_pin() -> str:
    return f"{secrets.randbelow(PIN_RANGE[1] + 1):04d}"
