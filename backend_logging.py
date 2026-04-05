"""
Flask backend merkezi loglama.

- Herkes (destek / yönetim): Türkçe ÖZET — ne yapıldı, HTTP sonucunun anlamı, süre, IP, istek no.
- Geliştirici: TEKNİK blok — rid, method, path, status, süre, ua, sorgu parametreleri, vb.

Hassas yollar: /api/login, /api/register için gövde okunmaz ve loglanmaz.
"""
import logging
import os
import re
import time
import uuid
from logging.handlers import RotatingFileHandler

from flask import Flask, g, has_request_context, request
from werkzeug.exceptions import HTTPException

from config import (
    get_log_dir,
    get_log_human_readable,
    get_log_level,
    get_log_request_body_preview,
    get_log_request_detail,
    get_log_slow_request_ms,
    get_log_to_console,
)

REQUEST_LOGGER_NAME = "harcamamasraf.request"
ERROR_LOGGER_NAME = "harcamamasraf.error"

_MAX_BYTES = 10 * 1024 * 1024
_BACKUP_COUNT = 5

_MAX_BODY_PREVIEW_BYTES = 2048
_MAX_BODY_CAPTURE_TOTAL = 65536

_SENSITIVE_PATH_MARKERS = ("/api/login", "/api/register")

# Uzun prefix once (daha ozel yollar ustte)
_PATH_HINTS = (
    ("/api/clear_all_expenses", "Tüm masraf kayıtlarını silme"),
    ("/api/clear_harcama_talep", "Harcama taleplerini toplu silme"),
    ("/api/clear_expenses/", "Belirli kullanıcının masraflarını silme"),
    ("/api/get_operations_by_stage/", "Safhaya göre operasyon listesi"),
    ("/api/update_expense/", "Masraf kaydı güncelleme"),
    ("/api/delete_expense/", "Masraf kaydı silme"),
    ("/api/delete_operasyon/", "Operasyon silme"),
    ("/api/delete_kaynak_tipi/", "Kaynak tipi silme"),
    ("/api/delete_stage/", "Safha silme"),
    ("/api/delete_birim/", "Birim silme"),
    ("/api/delete_bolge/", "Bölge silme"),
    ("/api/harcama_talep/", "Tek harcama talebi (detay veya güncelleme/silme)"),
    ("/api/login", "Kullanıcı girişi"),
    ("/api/register", "Yeni kullanıcı kaydı"),
    ("/api/bolge_kodlari", "Bölge kodları"),
    ("/api/kaynak_tipleri", "Kaynak tipleri"),
    ("/api/stages", "Safhalar (stage)"),
    ("/api/operasyonlar", "Operasyonlar"),
    ("/api/stage_operasyonlar", "Safha–operasyon eşlemesi"),
    ("/api/birim_ucretler", "Birim ücretler"),
    ("/api/all_data", "Toplu veri (all_data)"),
    ("/api/add_kaynak_tipi", "Kaynak tipi ekleme"),
    ("/api/add_stage", "Safha ekleme"),
    ("/api/add_operasyon", "Operasyon ekleme"),
    ("/api/add_stage_operasyon", "Safha–operasyon bağlama"),
    ("/api/add_birim", "Birim ekleme"),
    ("/api/update_bolge", "Bölge güncelleme"),
    ("/api/update_kaynak_tipi", "Kaynak tipi güncelleme"),
    ("/api/update_stage", "Safha güncelleme"),
    ("/api/update_operasyon", "Operasyon güncelleme"),
    ("/api/update_birim", "Birim güncelleme"),
    ("/api/save_expense", "Masraf kaydetme"),
    ("/api/get_expenses", "Masraf listesi"),
    ("/api/get_user_id", "Kullanıcı ID sorgusu"),
    ("/api/add_bolge", "Bölge ekleme"),
    ("/api/bulk_add_bolge", "Toplu bölge ekleme"),
    ("/api/harcama_talep", "Harcama talepleri (liste veya yeni kayıt)"),
    ("/api/users", "Kullanıcı listesi veya kullanıcı işlemleri"),
)


def get_request_logger():
    return logging.getLogger(REQUEST_LOGGER_NAME)


def get_error_logger():
    return logging.getLogger(ERROR_LOGGER_NAME)


def _path_is_sensitive(path):
    pl = (path or "").lower()
    return any(m in pl for m in _SENSITIVE_PATH_MARKERS)


def _client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip() or "-"
    return request.remote_addr or "-"


def _header_trunc(name, max_len=200):
    v = request.headers.get(name)
    if not v:
        return "-"
    v = str(v).replace("\r", " ").replace("\n", " ")
    return (v[:max_len] + "...") if len(v) > max_len else v


def _human_http_status_tr(code):
    if code is None:
        return "Bilinmeyen yanıt"
    if code == 200:
        return "Başarılı (200 OK)"
    if code == 201:
        return "Oluşturuldu (201)"
    if code == 204:
        return "İçerik yok / silindi (204)"
    if code == 304:
        return "Değişmedi / önbellek (304)"
    if 200 <= code < 300:
        return "Başarılı (%s)" % code
    if 300 <= code < 400:
        return "Yönlendirme (%s)" % code
    if code == 400:
        return "Geçersiz istek (400)"
    if code == 401:
        return "Giriş gerekli / yetkisiz (401)"
    if code == 403:
        return "Erişim reddedildi (403)"
    if code == 404:
        return "Adres bulunamadı (404)"
    if code == 409:
        return "Çakışma (409)"
    if code == 422:
        return "Veri doğrulanamadı (422)"
    if 400 <= code < 500:
        return "İstemci tarafı hata (%s)" % code
    if code == 500:
        return "Sunucu hatası (500)"
    if 500 <= code < 600:
        return "Sunucu tarafı hata (%s)" % code
    return "HTTP %s" % code


def _method_action_tr(method):
    return {
        "GET": "sorgulandı",
        "POST": "gönderildi",
        "PUT": "güncellendi",
        "PATCH": "kısmen güncellendi",
        "DELETE": "silindi",
        "OPTIONS": "seçenekler soruldu",
        "HEAD": "başlık istendi",
    }.get(method, "işlendi")


def _hint_users_subpath(path, method):
    p = path.rstrip("/")
    if p == "/api/users":
        return "Tüm kullanıcıların listesi" if method == "GET" else "Kullanıcı API"
    if not path.startswith("/api/users/"):
        return None
    if path.endswith("/role"):
        return "Kullanıcı rolünü güncelleme"
    if re.search(r"/api/users/[^/]+/bolge/[^/]+$", path) and method == "DELETE":
        return "Kullanıcıdan bölge kaldırma"
    if re.search(r"/api/users/[^/]+/bolge$", path.rstrip("/")):
        return "Kullanıcıya bölge atama"
    if re.match(r"^/api/users/[^/]+$", path.rstrip("/")):
        return "Tek kullanıcı bilgisi"
    return "Kullanıcı yönetimi"


def _what_was_requested_tr(method, path):
    u = _hint_users_subpath(path, method)
    if u:
        return u
    for prefix, label in _PATH_HINTS:
        if path == prefix or path.startswith(prefix + "/"):
            return label
    if path in ("/", ""):
        return "Sunucu sağlık kontrolü (ana sayfa)"
    return "Bilinmeyen API adresi"


def _human_summary_sentence(method, path, status_code, duration_ms, ip, rid):
    """Destek ve yönetim için tek satır Türkçe özet."""
    ne = _what_was_requested_tr(method, path)
    eylem = _method_action_tr(method)
    durum = _human_http_status_tr(status_code)
    return (
        "Ne: %s | İşlem: %s %s | Sonuç: %s | Süre: %s ms | İstemci IP: %s | İstek no: %s"
        % (ne, method, eylem, durum, duration_ms, ip, rid)
    )


def _maybe_capture_body_preview():
    g._log_body_preview = ""
    if not get_log_request_body_preview():
        return
    if _path_is_sensitive(request.path):
        return
    if request.method not in ("POST", "PUT", "PATCH"):
        return
    ct = (request.content_type or "").lower()
    if "multipart/form-data" in ct:
        g._log_body_preview = "<multipart_skipped>"
        return
    if not (
        "application/json" in ct
        or "text/" in ct
        or ct.endswith("+json")
    ):
        return
    cl = request.content_length
    if cl is None:
        g._log_body_preview = "<no_content_length_skipped>"
        return
    if cl <= 0:
        return
    if cl > _MAX_BODY_CAPTURE_TOTAL:
        g._log_body_preview = "<skipped_large len=%s>" % cl
        return
    try:
        raw = request.get_data(cache=True, as_text=True)
        if raw:
            one_line = raw.replace("\r", " ").replace("\n", " ").strip()
            g._log_body_preview = one_line[:_MAX_BODY_PREVIEW_BYTES]
    except Exception:
        g._log_body_preview = "<body_read_error>"


def _build_technical_parts(response, duration_ms):
    detail = get_log_request_detail()
    parts = [
        "rid=%s" % getattr(g, "_log_request_id", "-"),
        "method=%s" % request.method,
        "path=%s" % request.path,
        "status=%s" % response.status_code,
        "duration_ms=%s" % duration_ms,
        "ip=%s" % _client_ip(),
    ]
    if request.query_string:
        q = request.query_string.decode("utf-8", errors="replace")[:800]
        parts.append("query=%s" % q)
    if detail != "minimal":
        parts.append("ua=%s" % _header_trunc("User-Agent", 200))
        parts.append("ct_in=%s" % _header_trunc("Content-Type", 100))
        parts.append(
            "cl_in=%s"
            % (
                request.content_length
                if request.content_length is not None
                else "-"
            )
        )
        parts.append("x_request_id=%s" % _header_trunc("X-Request-ID", 80))
    if detail == "full":
        parts.append("referer=%s" % _header_trunc("Referer", 200))
        parts.append("accept=%s" % _header_trunc("Accept", 120))
        parts.append("mime_out=%s" % (response.content_type or "-"))
        try:
            rcl = response.content_length
        except Exception:
            rcl = None
        parts.append("cl_out=%s" % (rcl if rcl is not None else "-"))
        parts.append("cache_control=%s" % _header_trunc("Cache-Control", 80))
    preview = getattr(g, "_log_body_preview", "") or ""
    if preview:
        parts.append("body_preview=%s" % preview)
    return parts


def _format_access_line(response, duration_ms):
    rid = getattr(g, "_log_request_id", "-")
    ip = _client_ip()
    human = _human_summary_sentence(
        request.method, request.path, response.status_code, duration_ms, ip, rid
    )
    technical = " | ".join(_build_technical_parts(response, duration_ms))
    if get_log_human_readable():
        return "ÖZET (herkes için) >> %s || TEKNİK (geliştirici) >> %s" % (
            human,
            technical,
        )
    return technical


def _on_request_exception(sender, exception, **extra):
    if isinstance(exception, HTTPException):
        code = exception.code
        if code is not None and code < 500:
            return
    log = get_error_logger()
    rid = getattr(g, "_log_request_id", "-") if has_request_context() else "-"
    if has_request_context():
        detail = get_log_request_detail()
        ip = _client_ip()
        ne = _what_was_requested_tr(request.method, request.path)
        ozet = (
            "ÖZET: Sunucuda beklenmeyen hata | İşlem: %s | Ne: %s | İstek no: %s | IP: %s"
            % (request.method, ne, rid, ip)
        )
        teknik = ["TEKNİK:", "method=%s" % request.method, "path=%s" % request.path]
        if detail != "minimal":
            teknik.append("ip=%s" % ip)
            teknik.append("ua=%s" % _header_trunc("User-Agent", 120))
        if detail == "full" and request.query_string:
            q = request.query_string.decode("utf-8", errors="replace")[:400]
            teknik.append("query=%s" % q)
        teknik.append("istisna_tipi=%s" % type(exception).__name__)
        msg = "%s | %s | Aşağıda Python traceback (geliştirici için)." % (
            ozet,
            " ".join(teknik),
        )
        log.exception(msg)
    else:
        log.exception(
            "ÖZET: Bağlam dışı hata | TEKNİK: rid=%s | istisna_tipi=%s | Aşağıda traceback.",
            rid,
            type(exception).__name__,
        )


def configure_backend_logging(app: Flask) -> None:
    log_dir = get_log_dir()
    os.makedirs(log_dir, exist_ok=True)

    level = get_log_level()

    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    req_log = get_request_logger()
    req_log.handlers.clear()
    req_log.setLevel(logging.DEBUG)
    req_log.propagate = False
    req_path = os.path.join(log_dir, "backend_request.log")
    req_handler = RotatingFileHandler(
        req_path, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8"
    )
    req_handler.setLevel(logging.DEBUG)
    req_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    req_log.addHandler(req_handler)

    err_path = os.path.join(log_dir, "backend_error.log")
    err_handler = RotatingFileHandler(
        err_path, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8"
    )
    err_handler.setLevel(logging.ERROR)
    err_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s | %(message)s"
        )
    )

    app.logger.handlers.clear()
    app.logger.setLevel(level)
    app.logger.addHandler(err_handler)

    err_log = get_error_logger()
    err_log.handlers.clear()
    err_log.setLevel(logging.ERROR)
    err_log.propagate = True
    err_log.parent = app.logger

    if get_log_to_console():
        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        app.logger.addHandler(console)

    @app.before_request
    def _request_context_start():
        g._log_request_id = uuid.uuid4().hex[:12]
        g._log_request_started = time.perf_counter()
        _maybe_capture_body_preview()

    @app.after_request
    def _request_access_log(response):
        try:
            start = getattr(g, "_log_request_started", None)
            duration_ms = (
                int((time.perf_counter() - start) * 1000) if start is not None else -1
            )
            line = _format_access_line(response, duration_ms)
            slow_ms = get_log_slow_request_ms()
            if slow_ms > 0 and duration_ms >= slow_ms:
                if get_log_human_readable():
                    line = (
                        "DİKKAT (yavaş istek, %s ms — eşik %s ms) >> %s"
                        % (duration_ms, slow_ms, line)
                    )
                else:
                    line = "YAVAS duration_ms=%s threshold_ms=%s | %s" % (
                        duration_ms,
                        slow_ms,
                        line,
                    )
                get_request_logger().warning(line)
            else:
                get_request_logger().info(line)
        except Exception:
            get_error_logger().exception("İstek access log yazımı başarısız")
        return response

    try:
        from flask.signals import got_request_exception
    except ImportError:
        from flask import got_request_exception

    got_request_exception.connect(_on_request_exception, app)

    app.logger.info(
        "Backend loglama açıldı | Klasör: %s | Detay: %s | Yavaş eşik (ms): %s | Türkçe özet: %s",
        log_dir,
        get_log_request_detail(),
        get_log_slow_request_ms(),
        "açık" if get_log_human_readable() else "kapalı",
    )
