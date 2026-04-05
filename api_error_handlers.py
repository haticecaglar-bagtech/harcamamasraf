"""
Flask API icin global hata yonetimi: JSON yanitlar, Turkce kullanici mesajlari.
"""
from werkzeug.exceptions import HTTPException
from flask import Flask, g, jsonify, request

from config import is_production


def _request_id():
    return getattr(g, "_log_request_id", None)


def _wants_api_json_response():
    if request.path.startswith("/api"):
        return True
    accept = (request.headers.get("Accept") or "").lower()
    if "application/json" in accept:
        return True
    if request.is_json:
        return True
    return False


def _friendly_http_message(exc: HTTPException) -> str:
    code = exc.code
    desc = (exc.description or "").strip()

    by_code = {
        400: "Geçersiz istek. Gönderdiğiniz veriyi kontrol edin.",
        401: "Bu işlem için giriş yapmanız gerekiyor.",
        403: "Bu işlem için yetkiniz yok.",
        404: "İstenen adres bulunamadı.",
        405: "Bu HTTP yöntemi bu adres için kullanılamaz.",
        408: "İstek zaman aşımına uğradı.",
        409: "İstek verisi mevcut kayıtla çakışıyor.",
        410: "Bu kayıt artık kullanılamıyor.",
        413: "Gönderilen veri çok büyük.",
        415: "Desteklenmeyen veri türü.",
        422: "Gönderilen veri doğrulanamadı.",
        429: "Çok fazla istek gönderildi. Lütfen bir süre sonra tekrar deneyin.",
        500: "Sunucuda bir hata oluştu.",
        502: "Sunucu geçici olarak ulaşılamıyor.",
        503: "Hizmet geçici olarak kullanılamıyor.",
    }
    if code in by_code:
        base = by_code[code]
        if code == 400 and desc and len(desc) < 200 and "browser" not in desc.lower():
            return "%s (%s)" % (base, desc)
        return base
    if desc and len(desc) < 300:
        return desc
    return exc.name or "Bir hata oluştu"


def _payload_500_public():
    return (
        "Beklenmeyen bir sunucu hatası oluştu. "
        "Lütfen daha sonra tekrar deneyin. Sorun devam ederse destek ekibine "
        "aşağıdaki İstek numarası (request_id) ile başvurun."
    )


def register_global_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        if not _wants_api_json_response():
            return exc.get_response()

        msg = _friendly_http_message(exc)
        body = {
            "success": False,
            "error": msg,
            "message": msg,
            "code": exc.code,
        }
        rid = _request_id()
        if rid:
            body["request_id"] = rid
        return jsonify(body), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(exc: Exception):
        if isinstance(exc, HTTPException):
            return handle_http_exception(exc)

        msg = (
            _payload_500_public()
            if is_production()
            else "Sunucu hatası (geliştirme): %s" % type(exc).__name__
        )
        body = {
            "success": False,
            "error": msg,
            "message": msg,
            "code": 500,
        }
        rid = _request_id()
        if rid:
            body["request_id"] = rid
        if not is_production():
            body["debug_type"] = type(exc).__name__
            body["debug_detail"] = str(exc)

        return jsonify(body), 500
