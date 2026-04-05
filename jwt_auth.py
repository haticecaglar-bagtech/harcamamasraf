"""
JWT uretimi ve Flask before_request ile API koruma.
"""
import jwt
from datetime import datetime, timedelta, timezone
from flask import Flask, g, jsonify, request

from config import (
    get_jwt_auth_enabled,
    get_jwt_expiration_seconds,
    get_jwt_secret,
)


def issue_access_token(user_id, username, role):
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=get_jwt_expiration_seconds())
    payload = {
        "sub": str(user_id),
        "user_id": int(user_id),
        "username": username,
        "role": role or "normal",
        "iat": now,
        "exp": exp,
    }
    encoded = jwt.encode(payload, get_jwt_secret(), algorithm="HS256")
    if isinstance(encoded, bytes):
        return encoded.decode("utf-8")
    return encoded


def _json_401(message, error_code="invalid_token"):
    rid = getattr(g, "_log_request_id", None)
    body = {
        "success": False,
        "error": message,
        "message": message,
        "code": 401,
        "error_code": error_code,
    }
    if rid:
        body["request_id"] = rid
    return jsonify(body), 401


def register_jwt_middleware(app: Flask) -> None:
    @app.before_request
    def _jwt_require():
        if not get_jwt_auth_enabled():
            return None
        if request.method == "OPTIONS":
            return None
        path = request.path or ""
        if not path.startswith("/api"):
            return None
        if path == "/api/login" and request.method == "POST":
            return None
        if path == "/api/register" and request.method == "POST":
            return None

        auth = (request.headers.get("Authorization") or "").strip()
        if not auth.startswith("Bearer "):
            return _json_401(
                "Oturum anahtari gerekli. Once /api/login ile giris yapip "
                "Authorization: Bearer <token> basligini gonderin.",
                "missing_token",
            )

        token = auth[7:].strip()
        if not token:
            return _json_401("Bos oturum anahtari.", "missing_token")

        try:
            data = jwt.decode(
                token,
                get_jwt_secret(),
                algorithms=["HS256"],
                options={"require": ["exp", "sub"]},
            )
        except jwt.ExpiredSignatureError:
            return _json_401(
                "Oturum suresi doldu. Lutfen tekrar giris yapin.",
                "token_expired",
            )
        except jwt.InvalidTokenError:
            return _json_401(
                "Gecersiz oturum anahtari. Lutfen tekrar giris yapin.",
                "invalid_token",
            )

        g.jwt_user_id = data.get("user_id")
        g.jwt_username = data.get("username")
        g.jwt_role = data.get("role")
        g.jwt_payload = data
        return None
