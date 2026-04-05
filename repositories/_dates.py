from datetime import date, datetime


def parse_date(val):
    if val is None:
        raise ValueError("tarih gerekli")
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if " " in s:
        s = s.split(" ")[0]
    return date.fromisoformat(s)


def format_tarih_for_json(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, date):
        return val.isoformat()
    return str(val)
