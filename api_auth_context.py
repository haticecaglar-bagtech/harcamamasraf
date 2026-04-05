"""
Oturum JWT'sini paylasir: ApiClient ve dogrudan requests cagrilari ayni Bearer token'i kullanir.
"""
import threading

_lock = threading.Lock()
_bearer_token = None


def set_bearer_token(token):
    global _bearer_token
    with _lock:
        _bearer_token = (token or "").strip() or None


def clear_bearer_token():
    set_bearer_token(None)


def get_bearer_token():
    with _lock:
        return _bearer_token


def get_auth_headers():
    t = get_bearer_token()
    if t:
        return {"Authorization": "Bearer %s" % t}
    return {}


def merge_auth_headers(extra=None):
    out = dict(extra) if extra else {}
    out.update(get_auth_headers())
    return out
