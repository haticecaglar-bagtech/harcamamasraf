# Gelistirme Ortami Kurulumu

Bu proje, tum gelistiricilerde ayni Python ve bagimlilik surumleriyle calismasi icin standartlastirilmistir.

## 1) Python surumu

Proje Python `3.8.10` ile calisir.

- Surum sabitleme dosyasi: `.python-version`
- Kurulu surumu dogrulama:

```powershell
python --version
```

## 2) Virtual environment olusturma

Proje klasorunde su komutlari calistirin:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## 3) Bagimliliklari yukleme

`requirements.txt` dosyasindaki sabit surumleri yukleyin:

```powershell
pip install -r requirements.txt
```

## 4) Ortami dogrulama

Kurulu paketleri dogrulayin:

```powershell
pip freeze
```

> Not: `venv/` ve `.venv/` klasorleri `.gitignore` icindedir; depoya eklenmez.

## 5) Ortam dosyasi (.env)

Uygulama ayarlari icin proje kokunde `.env` kullanabilirsiniz (ornek: `.env.example`).

```powershell
copy .env.example .env
```

`config.py` yuklendiginde `.env` otomatik okunur. Gercek sifre veya ozel yollar burada tutulmamali ise yalnizca yerel makinede `.env` olusturun; dosya `.gitignore` ile repoya eklenmez.

Onerilen degiskenler (hassas):

- `FLASK_SECRET_KEY` veya `SECRET_KEY` — Flask icin; uretimde `FLASK_ENV=production` iken zorunludur.
- `ADMIN_INITIAL_PASSWORD` — Bos veritabaninda ilk admin sifresi; uretimde tanimlanmazsa admin otomatik olusturulmaz.
- `DATABASE_PATH` — SQLite dosya yolu (paylasilan sunucuda hassas olabilir).
