# Ücretsiz Bulut Deployment Kılavuzu

## SQLite Veritabanı (Ücretsiz ve Global)

Uygulama artık SQLite kullanıyor. SQLite dosyası (`harcama_masraf.db`) uygulama klasöründe otomatik oluşturulacak.

## Ücretsiz Bulut Deployment Seçenekleri

### 1. Railway (Önerilen - Ücretsiz Tier)
- Website: https://railway.app
- Ücretsiz: $5 kredi/ay
- Deployment:
  ```bash
  # Railway CLI ile
  railway login
  railway init
  railway up
  ```

### 2. Render (Ücretsiz Tier)
- Website: https://render.com
- Ücretsiz: 750 saat/ay
- Deployment:
  1. GitHub'a push edin
  2. Render'da yeni Web Service oluşturun
  3. Build Command: `pip install -r requirements.txt`
  4. Start Command: `python RestApi.py`

### 3. PythonAnywhere (Ücretsiz Tier)
- Website: https://www.pythonanywhere.com
- Ücretsiz: Sınırlı kaynak
- Deployment:
  1. Hesap oluşturun
  2. Files sekmesinde dosyaları yükleyin
  3. Web sekmesinde Flask app oluşturun

### 4. Heroku (Ücretsiz Tier Kaldırıldı - Alternatifler)
- Artık ücretsiz tier yok, alternatifler kullanın

## Veritabanı Seçenekleri

### SQLite (Mevcut - Ücretsiz)
- ✅ Tamamen ücretsiz
- ✅ Kurulum gerektirmez
- ✅ Dosya tabanlı
- ⚠️ Tek kullanıcılı (concurrent write sınırlaması)

### Supabase (PostgreSQL - Ücretsiz Tier)
- Website: https://supabase.com
- Ücretsiz: 500MB veritabanı, 2GB bandwidth
- PostgreSQL tabanlı
- Global erişim

### ElephantSQL (PostgreSQL - Ücretsiz Tier)
- Website: https://www.elephantsql.com
- Ücretsiz: 20MB veritabanı
- PostgreSQL tabanlı

## API Endpoint'leri

API şu adreste çalışacak:
- Local: http://localhost:5000
- Production: [Deployment URL'iniz]

## Önemli Notlar

1. **SQLite Geçişi**: Tüm SQL Server sorguları SQLite'a çevrildi
2. **Veritabanı Dosyası**: `harcama_masraf.db` otomatik oluşturulacak
3. **Migration**: İlk çalıştırmada otomatik migration yapılacak
4. **Backup**: SQLite dosyasını düzenli yedekleyin

## Gerekli Dosyalar

- `requirements.txt` - Python bağımlılıkları
- `Procfile` - Railway/Render için
- `runtime.txt` - Python versiyonu
- `RestApi.py` - Flask API

## Deployment Adımları

1. GitHub'a push edin
2. Railway/Render'da yeni proje oluşturun
3. GitHub repo'yu bağlayın
4. Otomatik deploy başlayacak
5. API URL'ini alın ve uygulamada kullanın

