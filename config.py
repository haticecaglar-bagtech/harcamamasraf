"""
Merkezi uygulama ayarlari. Ortam degiskenleri ile uzerine yazilabilir.

Ortam degiskenleri (ornek):
  API_ORIGIN veya API_BASE_URL  — Ornek: http://127.0.0.1:5000 (sonunda / yok)
  API_PREFIX                    — Varsayilan: /api
  DATABASE_URL — SQLAlchemy veritabani URLi (PostgreSQL: postgresql+psycopg2://user:sifre@host:5432/dbadi)
               Belirtilmezse SQLite kullanilir (asagidaki DATABASE_PATH / SQLITE_PATH).
  DATABASE_PATH veya SQLITE_PATH — SQLite dosya yolu (mutlak veya goreceli); DATABASE_URL yokken
  FLASK_HOST                    — Varsayilan: 0.0.0.0
  FLASK_PORT veya PORT          — Varsayilan: 5000 (bulut platformlari genelde PORT kullanir)

  migrate_data_to_sqlite.py icin (opsiyonel):
  SQLSERVER_SERVER, SQLSERVER_DATABASE, SQLSERVER_DRIVER

  Proje kokundeki .env dosyasi (git'e eklenmez) yuklenir.
  Sistemde tanimli ortam degiskenleri varsa onlar onceliklidir (load_dotenv override=False).

  Hassas / guvenlik:
  FLASK_SECRET_KEY veya SECRET_KEY — Flask oturum ve imzalar (uretimde zorunlu)
  FLASK_ENV=production — uretim modu; eksik secret key uygulamayi baslatmaz
  ADMIN_USERNAME — Ilk admin kullanici adi (varsayilan: admin)
  ADMIN_INITIAL_PASSWORD — Veritabaninda admin yokken tek seferlik olusturma sifresi

  Loglama (backend):
  LOG_DIR — Log klasoru (varsayilan: proje/logs)
  LOG_LEVEL — DEBUG, INFO, WARNING, ERROR (varsayilan: INFO)
  LOG_CONSOLE — 1/true: konsola da yaz; 0/false: kapat. Belirtilmezse uretimde kapali, gelistirmede acik.
  LOG_REQUEST_DETAIL — minimal | standard | full (varsayilan: full)
  LOG_SLOW_MS — Bu sureyi asan istekler WARNING ile loglanir; 0=kapat (varsayilan: 2000)
  LOG_REQUEST_BODY — 1/true: JSON/text govde onizlemesi (login/register haric); varsayilan kapali
  LOG_HUMAN_READABLE — 0/false: Turkce ozet satirini kapat (yalnizca TEKNIK blogu); varsayilan acik

  JWT (Flask SECRET_KEY ile karistirilmaz):
  JWT_SECRET_KEY — Zorunlu ayri imza anahtari (uretimde mutlaka .env)
  JWT_EXPIRATION_HOURS — Access token suresi (varsayilan 24)
  JWT_AUTH_ENABLED — 0: API JWT zorunlulugunu kapat (script/legacy); varsayilan 1
"""
import logging
import os

from dotenv import load_dotenv

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

_dev_flask_secret = None
_dev_jwt_secret = None


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
    """SQLite veritabani dosya yolu (DATABASE_URL kullanilmiyorken)."""
    custom = _env_str("DATABASE_PATH") or _env_str("SQLITE_PATH")
    if custom:
        return os.path.abspath(custom)
    return os.path.join(_PROJECT_ROOT, "harcama_masraf.db")


def get_database_url():
    """SQLAlchemy baglanti URLi. DATABASE_URL tanimliysa onu; aksi halde SQLite dosya URLi."""
    url = _env_str("DATABASE_URL")
    if url:
        return url.strip()
    path = os.path.abspath(get_database_path())
    return "sqlite:///" + path.replace("\\", "/")


def is_postgresql_database():
    u = get_database_url().lower()
    return u.startswith("postgresql") or u.startswith("postgres:")


def sanitize_database_url(url: str) -> str:
    """Log/cikti icin parola maskeleme (postgresql+psycopg2://user:pass@host/db)."""
    if not url or "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    if "@" not in rest:
        return url
    creds, hostpart = rest.rsplit("@", 1)
    if ":" not in creds:
        return url
    user = creds.split(":", 1)[0]
    return f"{scheme}://{user}:***@{hostpart}"


def get_flask_host():
    return _env_str("FLASK_HOST", "0.0.0.0")


def get_flask_port():
    return _env_int("PORT", _env_int("FLASK_PORT", 5000))


def get_health_check_url():
    return f"{get_api_origin()}/"


def is_production():
    env = (_env_str("FLASK_ENV", "") or "").lower()
    return env in ("production", "prod")


def get_flask_secret_key():
    """
    Flask app.secret_key. Uretimde FLASK_SECRET_KEY veya SECRET_KEY zorunludur.
    Gelistirmede tanimli degilse her calistirmada sabit kalmak uzere rastgele anahtar uretilir.
    """
    global _dev_flask_secret
    key = _env_str("FLASK_SECRET_KEY") or _env_str("SECRET_KEY")
    if key:
        return key
    if is_production():
        raise RuntimeError(
            "Uretim ortaminda FLASK_SECRET_KEY veya SECRET_KEY tanimlanmalidir (.env veya ortam)."
        )
    if _dev_flask_secret is None:
        import secrets

        _dev_flask_secret = secrets.token_hex(32)
        print(
            "UYARI: FLASK_SECRET_KEY tanimli degil; gelistirme icin gecici anahtar kullaniliyor. "
            ".env dosyasina guclu bir FLASK_SECRET_KEY eklemeniz onerilir."
        )
    return _dev_flask_secret


def get_admin_username():
    return _env_str("ADMIN_USERNAME", "admin")


def get_admin_initial_password():
    """Ilk admin olusturma sifresi; yoksa RestApi __main__ rastgele uretir (yalnizca gelistirme)."""
    return _env_str("ADMIN_INITIAL_PASSWORD")


def get_log_dir():
    custom = _env_str("LOG_DIR")
    if custom:
        return os.path.abspath(custom)
    return os.path.join(_PROJECT_ROOT, "logs")


def get_log_level():
    name = (_env_str("LOG_LEVEL", "INFO") or "INFO").upper()
    return getattr(logging, name, logging.INFO)


def get_log_to_console():
    v = _env_str("LOG_CONSOLE")
    if v is not None:
        return v.lower() in ("1", "true", "yes", "on")
    return not is_production()


def get_log_request_detail():
    """minimal | standard | full — istek satirina eklenecek alanlar."""
    v = (_env_str("LOG_REQUEST_DETAIL", "full") or "full").lower().strip()
    if v in ("0", "minimal", "min", "basic"):
        return "minimal"
    if v in ("1", "standard", "std", "normal"):
        return "standard"
    return "full"


def get_log_slow_request_ms():
    """0: yavas istek uyarisini kapat."""
    return _env_int("LOG_SLOW_MS", 2000)


def get_log_request_body_preview():
    """Login/register yollarinda asla; digerlerinde kisa govde onizlemesi."""
    v = _env_str("LOG_REQUEST_BODY")
    if v is not None:
        return v.lower() in ("1", "true", "yes", "on")
    return False


def get_log_human_readable():
    """Kullaniciya yonelik Turkce ozet + yazilimci icin TEKNIK blogu."""
    v = _env_str("LOG_HUMAN_READABLE")
    if v is not None:
        return v.lower() not in ("0", "false", "no", "off")
    return True


def get_jwt_secret():
    """
    JWT imzasi icin Flask secret'tan BAGIMSIZ anahtar.
    Uretimde JWT_SECRET_KEY zorunludur; gelistirmede yoksa yalnizca JWT icin uretilen gecici anahtar kullanilir.
    """
    global _dev_jwt_secret
    s = _env_str("JWT_SECRET_KEY")
    if s:
        return s
    if is_production():
        raise RuntimeError(
            "Uretim ortaminda JWT_SECRET_KEY tanimlanmalidir (.env). "
            "Flask SECRET_KEY ile ayni olmamali; ayri guclu bir deger kullanin."
        )
    if _dev_jwt_secret is None:
        import secrets

        _dev_jwt_secret = secrets.token_hex(32)
        print(
            "UYARI: JWT_SECRET_KEY tanimli degil; gelistirme icin yalnizca JWT'ye ozel "
            "gecici anahtar kullaniliyor. Uretimde .env icine ayri JWT_SECRET_KEY ekleyin."
        )
    return _dev_jwt_secret


def get_jwt_expiration_seconds():
    hours = _env_int("JWT_EXPIRATION_HOURS", 24)
    return max(300, hours * 3600)


def get_jwt_auth_enabled():
    v = _env_str("JWT_AUTH_ENABLED")
    if v is not None:
        return v.lower() not in ("0", "false", "no", "off")
    return True
