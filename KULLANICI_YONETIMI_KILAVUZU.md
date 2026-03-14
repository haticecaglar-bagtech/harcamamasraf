# Kullanıcı Yönetimi Kılavuzu

Bu kılavuz, sistemde kullanıcı ekleme, rol atama ve bölge kodu tanımlama işlemlerini açıklar.

## Yöntem 1: Python Script ile (Önerilen)

### Adımlar:

1. **API sunucusunu başlatın:**
   ```bash
   python RestApi.py
   ```

2. **Başka bir terminalde kullanıcı yönetim scriptini çalıştırın:**
   ```bash
   python kullanici_yonetimi.py
   ```

3. **Menüden istediğiniz işlemi seçin:**
   - `1` - Yeni kullanıcı ekle
   - `2` - Kullanıcı rolü güncelle
   - `3` - Kullanıcıya bölge ekle
   - `4` - Kullanıcı bilgilerini görüntüle
   - `5` - Tüm kullanıcıları listele

### Örnek Kullanım:

#### Yeni Kullanıcı Ekleme:
```
1. Yeni Kullanıcı Ekle seçeneğini seçin
2. Kullanıcı adını girin: ahmet
3. Şifreyi girin: 123456
4. Rol atamak ister misiniz? (e/h): e
5. Rol seçiniz (1/2/3): 1
   (1=normal, 2=admin, 3=ust_duzey_yonetici)
6. Bölge kodu eklemek ister misiniz? (e/h): e
7. Bölge Kodu: 10
```

#### Kullanıcı Rolü Güncelleme:
```
1. Kullanıcı Rolü Güncelle seçeneğini seçin
2. Kullanıcı Adı: ahmet
3. Rol seçiniz (1/2/3): 2
   (Admin yapmak için)
```

#### Kullanıcıya Bölge Ekleme:
```
1. Kullanıcıya Bölge Ekle seçeneğini seçin
2. Kullanıcı Adı: ahmet
3. Bölge Kodu: 20
   (Kullanıcı artık 10 ve 20 bölgelerine erişebilir)
```

## Yöntem 2: API Endpoint'leri ile (Programatik)

### Kullanıcı Kayıt:
```bash
curl -X POST http://127.0.0.1:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "ahmet", "password": "123456"}'
```

### Rol Güncelleme:
```bash
curl -X PUT http://127.0.0.1:5000/api/users/ahmet/role \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'
```

### Bölge Ekleme:
```bash
curl -X POST http://127.0.0.1:5000/api/users/ahmet/bolge \
  -H "Content-Type: application/json" \
  -d '{"bolge_kodu": "10"}'
```

### Kullanıcı Bilgilerini Görüntüleme:
```bash
curl http://127.0.0.1:5000/api/users/ahmet
```

## Yöntem 3: SQL ile (Gelişmiş Kullanıcılar)

### Kullanıcı Ekleme:
```sql
INSERT INTO users (username, password_hash, role, default_bolge_kodu)
VALUES ('ahmet', '<password_hash>', 'normal', '10');
```

### Bölge Ekleme:
```sql
INSERT INTO user_bolgeler (user_id, bolge_kodu)
VALUES (1, '10');
```

**Not:** Password hash için Python'da:
```python
from werkzeug.security import generate_password_hash
password_hash = generate_password_hash('123456')
```

## Roller:

- **normal**: Normal kullanıcı - Sadece kendi bölgelerine erişebilir
- **admin**: Admin - Tüm bölgelere erişebilir, kod işlemleri yapabilir, düzenleme yapabilir
- **ust_duzey_yonetici**: Üst düzey yönetici - Tüm bölgeleri görüntüleyebilir, analiz yapabilir ama düzenleme yapamaz

## Bölge Kodları:

Mevcut bölge kodlarını görmek için:
```bash
curl http://127.0.0.1:5000/api/bolge_kodlari
```

Veya Python scriptinde "Kullanıcıya Bölge Ekle" seçeneğini seçtiğinizde otomatik olarak gösterilir.

## Örnek Senaryolar:

### Senaryo 1: Normal Kullanıcı Oluşturma
```
1. Kullanıcı ekle: ahmet / 123456
2. Rol: normal (varsayılan)
3. Bölge ekle: 10
4. Bölge ekle: 20
Sonuç: Ahmet sadece 10 ve 20 bölgelerine erişebilir
```

### Senaryo 2: Admin Oluşturma
```
1. Kullanıcı ekle: admin_user / admin123
2. Rol: admin
3. Bölge eklemeye gerek yok (admin tüm bölgelere erişebilir)
Sonuç: Admin tüm bölgelere erişebilir ve kod işlemleri yapabilir
```

### Senaryo 3: Üst Düzey Yönetici Oluşturma
```
1. Kullanıcı ekle: yonetici / yonet123
2. Rol: ust_duzey_yonetici
3. Bölge eklemeye gerek yok
Sonuç: Yönetici tüm bölgeleri görüntüleyebilir ama düzenleme yapamaz
```

## Sorun Giderme:

### "Kullanıcı bulunamadı" hatası:
- Kullanıcı adının doğru yazıldığından emin olun
- Önce kullanıcıyı ekleyin (`1. Yeni Kullanıcı Ekle`)

### "Geçersiz bölge kodu" hatası:
- Bölge kodunun veritabanında mevcut olduğundan emin olun
- Bölge kodlarını listelemek için: `curl http://127.0.0.1:5000/api/bolge_kodlari`

### "API sunucusuna bağlanılamadı" hatası:
- API sunucusunun çalıştığından emin olun: `python RestApi.py`
- Port 5000'in kullanılabilir olduğundan emin olun

