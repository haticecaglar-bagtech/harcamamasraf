# Veri Migration Kılavuzu

## SQL Server'dan SQLite'a Veri Aktarımı

Bu kılavuz, mevcut SQL Server veritabanındaki tüm verileri SQLite'a aktarmanız için hazırlanmıştır.

## Adımlar

### 1. SQL Server Bağlantısını Kontrol Edin

`migrate_data_to_sqlite.py` dosyasındaki SQL Server bağlantı bilgilerini kontrol edin:

```python
SERVER_NAME = r'DESKTOP-GVRQ3CP'
DATABASE_NAME = r'harcama_masraf_db'
DRIVER_NAME = r'ODBC Driver 11 for SQL Server'
```

Eğer farklıysa, dosyayı düzenleyin.

### 2. Migration Script'ini Çalıştırın

Terminal/Command Prompt'ta:

```bash
python migrate_data_to_sqlite.py
```

### 3. Migration İşlemi

Script şunları yapacak:

1. ✅ SQLite tablolarını oluşturacak
2. ✅ Kullanıcıları aktaracak
3. ✅ Kullanıcı-bölge ilişkilerini aktaracak
4. ✅ Bölge kodlarını aktaracak
5. ✅ Kaynak tiplerini aktaracak
6. ✅ Stages'leri aktaracak
7. ✅ Operasyonları aktaracak
8. ✅ Stage-operasyon kombinasyonlarını aktaracak
9. ✅ Birim ücretlerini aktaracak
10. ✅ Harcama taleplerini aktaracak
11. ✅ Masrafları aktaracak

### 4. Sonuç

Migration tamamlandıktan sonra:
- `harcama_masraf.db` dosyası oluşturulacak
- Tüm veriler SQLite'a aktarılacak
- Uygulama artık SQLite kullanacak

## Önemli Notlar

⚠️ **Yedek Alın**: Migration öncesi SQL Server veritabanınızın yedeğini alın!

⚠️ **Hata Durumu**: Eğer bir tablo bulunamazsa, o tablo atlanacak ve devam edecek.

⚠️ **Büyük Veriler**: Harcama ve masraf tabloları büyükse, migration biraz zaman alabilir.

## Sorun Giderme

### SQL Server Bağlantı Hatası

Eğer SQL Server'a bağlanamıyorsanız:
1. SQL Server'ın çalıştığından emin olun
2. Bağlantı bilgilerini kontrol edin
3. ODBC Driver'ın yüklü olduğundan emin olun

### Tablo Bulunamadı Hatası

Eğer bir tablo bulunamazsa:
- O tablo SQL Server'da yok demektir
- Script devam edecek, sadece o tablo atlanacak

### Veri Tipi Uyumsuzluğu

Eğer veri tipi uyumsuzluğu varsa:
- Script hata mesajı verecek
- İlgili satır atlanacak ve devam edecek

## Migration Sonrası

Migration tamamlandıktan sonra:
1. Uygulamayı yeniden başlatın
2. Verilerin doğru aktarıldığını kontrol edin
3. Gerekirse `migrate_data_to_sqlite.py` dosyasını tekrar çalıştırabilirsiniz (INSERT OR REPLACE kullanıldığı için güvenli)

