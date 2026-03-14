# Bölge Kodları Ekleme Kılavuzu

Bu kılavuz, görüntüdeki bölge kodlarını sisteminize ekleme sürecini açıklar.

## Eklenen Bölge Kodları

Aşağıdaki 25 bölge kodu sisteme eklenecek:

| Kod | Açıklama |
|-----|----------|
| 10 | ADY - DOĞU |
| 11 | ADY - BATI |
| 20 | MNS |
| 30 | MAR |
| 21 | MNS - FCV MAK. |
| 24 | MNS - N.RUSTICA |
| 35 | MAR - IZ |
| 25 | MNS - IZ |
| 12 | ADY DOĞU-JTI SCV |
| 13 | ADY BATI-JTI SCV |
| 22 | MNS-JTI SCV |
| 32 | MAR-JTI SCV |
| 14 | ADY DOĞU-SCV TOPPING |
| 15 | ADY BATI-SCV TOPPING |
| 26 | MNS-SCV TOPPING |
| 36 | MAR-SCV TOPPING |
| 16 | ADY DOĞU-PMI SCV |
| 17 | ADY BATI-PMI SCV |
| 23 | MNS-PMI SCV |
| 33 | MAR-PMI SCV |
| 18 | ADY BATI - N.RUSTICA |
| 37 | MAR-BASMA |
| 34 | MAR-N.RUSTICA |
| 38 | MAR-PRILEP |
| 39 | MAR-KATERINI |

## Ekleme Yöntemleri

### 1. Python Script ile Otomatik Ekleme

```bash
# API sunucusunu başlatın (eğer çalışmıyorsa)
python RestApi.py

# Başka bir terminalde bölge kodlarını ekleyin
python add_region_codes.py
```

### 2. SQL Script ile Manuel Ekleme

```bash
# SQLite veritabanına direkt ekleme
sqlite3 your_database.db < add_region_codes.sql
```

### 3. API Endpoint ile Manuel Ekleme

```python
from api_client import ApiClient

# API client oluştur
api_client = ApiClient()

# Tek bölge ekleme
response = api_client.add_bolge("10", "ADY - DOĞU")

# Toplu bölge ekleme
bolge_listesi = [
    {"kod": "10", "ad": "ADY - DOĞU"},
    {"kod": "11", "ad": "ADY - BATI"},
    # ... diğer bölgeler
]
response = api_client.bulk_add_bolge(bolge_listesi)
```

## Yapılan Değişiklikler

### 1. RestApi.py
- `@app.route('/api/add_bolge', methods=['POST'])` - Tek bölge ekleme endpoint'i
- `@app.route('/api/bulk_add_bolge', methods=['POST'])` - Toplu bölge ekleme endpoint'i

### 2. api_client.py
- `bulk_add_bolge(bolge_listesi)` - Toplu bölge ekleme fonksiyonu

### 3. Yeni Dosyalar
- `add_region_codes.sql` - SQL script
- `add_region_codes.py` - Python script
- `BOLGE_KODLARI_EKLEME_KILAVUZU.md` - Bu kılavuz

## Doğrulama

Bölge kodlarının başarıyla eklendiğini kontrol etmek için:

```python
from api_client import ApiClient

api_client = ApiClient()
bolge_kodlari = api_client.get_bolge_kodlari()
print(f"Toplam {len(bolge_kodlari)} bölge kodu mevcut")
```

## Hata Durumları

- **"Bu kod zaten mevcut"**: Aynı kod daha önce eklenmiş
- **"Database connection failed"**: Veritabanı bağlantı hatası
- **"API'den yanıt alınamadı"**: API sunucusu çalışmıyor

## Notlar

- Mevcut kodlar atlanır, sadece yeni kodlar eklenir
- Tüm işlemler transaction içinde yapılır
- Hata durumunda rollback yapılır
- API sunucusunun çalışır durumda olması gerekir
