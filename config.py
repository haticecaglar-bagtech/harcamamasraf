"""
Merkezi uygulama ayarlari. Ortam degiskenleri ile uzerine yazilabilir.

Ortam degiskenleri (ornek):
  API_ORIGIN veya API_BASE_URL  — Ornek: http://127.0.0.1:5000 (sonunda / yok)
  API_PREFIX                    — Varsayilan: /api
  DATABASE_PATH veya SQLITE_PATH — SQLite dosya yolu (mutlak veya goreceli)
  FLASK_HOST                    — Varsayilan: 0.0.0.0
  FLASK_PORT veya PORT          — Varsayilan: 5000 (bulut platformlari genelde PORT kullanir)

  migrate_data_to_sqlite.py icin (opsiyonel):
  SQLSERVER_SERVER, SQLSERVER_DATABASE, SQLSERVER_DRIVER

  Proje kokundeki .env dosyasi (git'e eklenmez) yuklenir.
  Sistemde tanimli ortam degiskenleri varsa onlar onceliklidir (load_dotenv override=False).
"""
import os

from dotenv import load_dotenv

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))


def _env_str(name, default=None):
    v = os.environ.get(name)
    if v is not None and str(v).strip() != "":
        return str(v).strip()
    return default


def _env_int(name, default):
    v = os.environ.get(name)
    if v is None or str(v).strip() == "":
        return default
    try:
        return int(v)
    except ValueError:
        return default


def get_api_origin():
    """HTTP kok adresi (yol yok, sonunda / yok). Ornek: http://127.0.0.1:5000"""
    origin = _env_str("API_ORIGIN") or _env_str("API_BASE_URL") or "http://127.0.0.1:5000"
    return origin.rstrip("/")


def get_api_prefix():
    """API yol oneki. Ornek: /api"""
    p = _env_str("API_PREFIX", "/api")
    if not p.startswith("/"):
        p = "/" + p
    return p.rstrip("/") or "/api"


def get_api_root():
    """REST API taban URL (ApiClient.base_url ile ayni). Ornek: http://127.0.0.1:5000/api"""
    origin = get_api_origin()
    prefix = get_api_prefix().lstrip("/")
    return f"{origin}/{prefix}" if prefix else origin


def api_url(path):
    """path: 'login' veya '/harcama_talep' — tek URL uretir."""
    path = path.lstrip("/")
    return f"{get_api_root()}/{path}"


def get_database_path():
    """SQLite veritabani dosya yolu."""
    custom = _env_str("DATABASE_PATH") or _env_str("SQLITE_PATH")
    if custom:
        return os.path.abspath(custom)
    return os.path.join(_PROJECT_ROOT, "harcama_masraf.db")


def get_flask_host():
    return _env_str("FLASK_HOST", "0.0.0.0")


def get_flask_port():
    return _env_int("PORT", _env_int("FLASK_PORT", 5000))


def get_health_check_url():
    return f"{get_api_origin()}/"
