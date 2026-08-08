#!/usr/bin/env python3
"""Unit tests for auth (PIN, admin password, tokens, rate limiter).

Run: pytest -q tests/test_auth.py   (from software/web)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import auth  # noqa: E402


def test_pin_ok():
    assert auth.pin_ok("1234")
    assert not auth.pin_ok("123")
    assert not auth.pin_ok("abcd")
    assert not auth.pin_ok("12345")
    assert not auth.pin_ok(1234)


def test_admin_password_ok():
    assert auth.admin_password_ok("AbCdEfGhIj")
    assert not auth.admin_password_ok("short")


def test_hash_verify_roundtrip():
    salt = auth._salt()
    h = auth.hash_secret("Secret1-2-3", salt)
    assert auth.verify_secret("Secret1-2-3", salt, h)
    assert not auth.verify_secret("Secret1-2-4", salt, h)


def test_new_pin_is_4_digits():
    for _ in range(50):
        p = auth.new_pin()
        assert len(p) == 4 and p.isdigit()


def test_new_admin_password_length():
    for _ in range(50):
        assert len(auth.new_admin_password()) == auth.ADMIN_PASSWORD_LEN


def test_token_issue_verify():
    t = auth.Token(os.urandom(32))
    tok = t.issue("user", "test")
    payload = t.verify(tok)
    assert payload["role"] == "user"
    assert payload["identity"] == "test"


def test_token_rejects_tamper_and_garbage():
    t = auth.Token(os.urandom(32))
    tok = t.issue("admin", "x")
    assert t.verify(tok + "x") is None
    assert t.verify("garbage") is None
    other = auth.Token(os.urandom(32))
    assert other.verify(tok) is None


def test_token_expiry():
    secret = os.urandom(32)
    t = auth.Token(secret)
    # force a short TTL by issuing then rewriting module constant is invasive;
    # instead verify a token with an already-expired timestamp decodes to None.
    import base64
    import hashlib
    import hmac as _hmac
    import time
    payload = base64.urlsafe_b64encode(b"user:me:1")  # exp = 1 (past)
    sig = _hmac.new(secret, payload, hashlib.sha256).digest()
    expired = payload.decode() + "." + base64.urlsafe_b64encode(sig).decode()
    assert t.verify(expired) is None


def test_rate_limiter():
    rl = auth.LoginRateLimiter(max_attempts=3, window_s=60, lockout_s=1)
    ip = "10.0.0.1"
    assert rl.allow(ip)
    rl.hit(ip)
    rl.hit(ip)
    rl.hit(ip)
    assert not rl.allow(ip)          # locked after 3 hits
    import time
    time.sleep(1.1)
    assert rl.allow(ip)              # lockout window passed


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
