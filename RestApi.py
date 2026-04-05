import os
from config import (
    get_admin_initial_password,
    get_admin_username,
    get_database_path,
    get_flask_host,
    get_flask_port,
    get_flask_secret_key,
    is_production,
)
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import sqlite3
from datetime import datetime

from api_error_handlers import register_global_error_handlers
from backend_logging import configure_backend_logging, get_error_logger

app = Flask(__name__)
app.secret_key = get_flask_secret_key()
CORS(app)  # Enable CORS for all routes
configure_backend_logging(app)
register_global_error_handlers(app)

# --- SQLite Veritabanı Ayarları (Ücretsiz ve Global) ---
# Veritabanı yolu: config.py + ortam degiskeni (DATABASE_PATH / SQLITE_PATH)
DATABASE_PATH = get_database_path()

def get_db_connection():
    """SQLite veritabanı bağlantısı oluşturur."""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Sözlük benzeri erişim için
        return conn
    except Exception as e:
        get_error_logger().error("Veritabani baglanti hatasi: %s", e, exc_info=True)
        return None

def migrate_db():
    """SQLite veritabanı yapısını oluşturur ve günceller"""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        # users tablosunu oluştur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'normal',
                default_bolge_kodu TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # user_bolgeler tablosunu oluştur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_bolgeler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                bolge_kodu TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, bolge_kodu)
            )
        """)
        
        # harcama_talep tablosunu oluştur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS harcama_talep (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                no INTEGER,
                tarih DATE NOT NULL,
                bolge_kodu TEXT,
                kaynak_tipi_kodu TEXT,
                stage_kodu TEXT,
                stage_operasyon_kodu TEXT,
                safha TEXT,
                harcama_kalemi TEXT,
                birim TEXT,
                miktar REAL,
                birim_ucret REAL,
                toplam REAL,
                aciklama TEXT,
                is_manuel INTEGER DEFAULT 0,
                user_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # harcama_talep_manuel_degisiklikler tablosunu oluştur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS harcama_talep_manuel_degisiklikler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                harcama_talep_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                alan_adi TEXT NOT NULL,
                eski_deger TEXT,
                yeni_deger TEXT,
                degisiklik_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (harcama_talep_id) REFERENCES harcama_talep(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # masraf tablosunu oluştur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS masraf (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih DATE NOT NULL,
                bolge_kodu TEXT,
                kaynak_tipi_kodu TEXT,
                stage_kodu TEXT,
                stage_operasyon_kodu TEXT,
                no INTEGER,
                kimden_alindi TEXT,
                aciklama TEXT,
                tutar REAL,
                user_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # bolge_kodlari tablosunu oluştur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bolge_kodlari (
                kod TEXT PRIMARY KEY,
                ad TEXT NOT NULL
            )
        """)
        
        # expenses tablosunu oluştur (masraf için)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tarih DATE NOT NULL,
                bolge_kodu TEXT,
                kaynak_tipi TEXT,
                stage TEXT,
                stage_operasyon TEXT,
                no_su TEXT,
                kimden_alindigi TEXT,
                aciklama TEXT,
                tutar REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # kaynak_tipleri tablosunu oluştur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kaynak_tipleri (
                kod TEXT PRIMARY KEY,
                ad TEXT NOT NULL
            )
        """)
        
        # stages tablosunu oluştur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stages (
                kod TEXT PRIMARY KEY,
                ad TEXT NOT NULL
            )
        """)
        
        # operasyonlar tablosunu oluştur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operasyonlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage_kod TEXT NOT NULL,
                operasyon_kod TEXT NOT NULL,
                operasyon_ad TEXT NOT NULL,
                FOREIGN KEY (stage_kod) REFERENCES stages(kod),
                UNIQUE (stage_kod, operasyon_kod)
            )
        """)
        
        # stage_operasyonlar tablosunu oluştur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stage_operasyonlar (
                kod TEXT PRIMARY KEY,
                ad TEXT NOT NULL
            )
        """)
        
        # birim_ucretler tablosunu oluştur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS birim_ucretler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                birim TEXT,
                ucret REAL
            )
        """)
        
        # Bölge kodlarını ekle (yoksa)
        bolge_kodlari = [
            ('10', 'ADY - DOĞU'),
            ('11', 'ADY - BATI'),
            ('20', 'MAN'),
            ('30', 'MAR'),
            ('21', 'MAN - FCV MAK.'),
            ('24', 'MAN - N.RUSTICA'),
            ('35', 'MAR - IZ'),
            ('25', 'MAN - IZ'),
            ('12', 'ADY DOĞU-JTI SCV'),
            ('13', 'ADY BATI-JTI SCV'),
            ('22', 'MAN-JTI SCV'),
            ('32', 'MAR-JTI SCV'),
            ('14', 'ADY DOĞU-SCV TOPPING'),
            ('15', 'ADY BATI-SCV TOPPING'),
            ('26', 'MAN-SCV TOPPING'),
            ('36', 'MAR-SCV TOPPING'),
            ('16', 'ADY DOĞU-PMI SCV'),
            ('17', 'ADY BATI-PMI SCV'),
            ('23', 'MAN-PMI SCV'),
            ('33', 'MAR-PMI SCV'),
            ('18', 'ADY BATI - N.RUSTICA'),
            ('37', 'MAR-BASMA'),
            ('34', 'MAR-N.RUSTICA'),
            ('38', 'MAR-PRILEP'),
            ('39', 'MAR-KATERINI')
        ]
        
        for kod, ad in bolge_kodlari:
            cursor.execute("""
                INSERT OR IGNORE INTO bolge_kodlari (kod, ad) VALUES (?, ?)
            """, (kod, ad))
        
        # Kaynak tipleri başlangıç verileri
        kaynak_tipleri = [
            ('01', 'İşçilik'),
            ('02', 'Malzeme'),
            ('03', 'Hizmet'),
            ('04', 'Enerji'),
            ('05', 'Kiralama')
        ]
        for kod, ad in kaynak_tipleri:
            cursor.execute("""
                INSERT OR IGNORE INTO kaynak_tipleri (kod, ad) VALUES (?, ?)
            """, (kod, ad))
        
        # Stages başlangıç verileri
        stages = [
            ('01', 'Fidelik'),
            ('02', 'Tarla Hazırlığı'),
            ('03', 'Gübre Atma'),
            ('04', 'Dikim'),
            ('05', 'İlaç Uygulama'),
            ('06', 'Sulama'),
            ('07', 'Çapalama'),
            ('08', 'Kırım'),
            ('09', 'Kurutma'),
            ('10', 'Kutulama'),
            ('11', 'Diğer is-işçilik'),
            ('12', 'Nakliye'),
            ('13', 'Supervisor'),
            ('14', 'Kültürel İşlemler'),
            ('15', 'TESTRRR')
        ]
        for kod, ad in stages:
            cursor.execute("""
                INSERT OR IGNORE INTO stages (kod, ad) VALUES (?, ?)
            """, (kod, ad))
        
        # Operasyonlar başlangıç verileri
        operasyonlar = [
            (164, '01', '01', 'Fide Yastığı Hazırlama'),
            (165, '01', '02', 'Tohum Atma'),
            (166, '01', '03', 'Sulama'),
            (167, '01', '04', 'Fide Çekimi'),
            (168, '01', '05', 'Gübre Uygulama'),
            (169, '01', '06', 'Ot Temizleme'),
            (170, '01', '07', 'Sera Havalandırma - Kapatma'),
            (171, '01', '08', 'İlaçlama'),
            (172, '01', '09', 'Fide Kırpma'),
            (173, '01', '97', 'Malzeme İndirme Yükleme'),
            (174, '01', '98', 'Malzeme Nakliye'),
            (175, '01', '99', 'Ekipman Bakım Tamirat'),
            (176, '02', '01', 'Tarla Kirası'),
            (177, '02', '02', 'Çiflik Ve Depo Kirası'),
            (178, '02', '03', 'Soil Analysis'),
            (179, '02', '04', 'Güz Sürüm'),
            (180, '02', '05', 'Bahar Sürümü'),
            (181, '02', '06', 'Dal Parçalama'),
            (182, '02', '07', 'Bahar Sürümü 2'),
            (183, '02', '08', 'Bahar Sürümü 3'),
            (184, '02', '97', 'Malzeme İndirme Yükleme'),
            (185, '02', '98', 'Malzeme Nakliye'),
            (186, '02', '99', 'Ekipman Bakım Tamirat'),
            (187, '03', '01', 'Gübre Uygulama'),
            (188, '03', '02', 'Gübre Uygulama Destek'),
            (189, '03', '97', 'Malzeme İndirme Yükleme'),
            (190, '03', '98', 'Malzeme Nakliye'),
            (191, '03', '99', 'Ekipman Bakım Tamirat'),
            (192, '04', '01', 'Dikim'),
            (193, '04', '02', 'Dikim Destek'),
            (194, '04', '03', 'Aşılama'),
            (195, '04', '97', 'Malzeme İndirme Yükleme'),
            (196, '04', '98', 'Malzeme Nakliye'),
            (197, '04', '99', 'Ekipman Bakım Tamirat'),
            (198, '05', '01', 'Herbicide Round-up'),
            (199, '05', '02', 'Herbicide Dual 960'),
            (200, '05', '03', 'Fungucide'),
            (201, '05', '04', 'Insecticide'),
            (202, '05', '05', 'Tarot'),
            (203, '05', '06', 'Herbicide Round-up destek'),
            (204, '05', '07', 'Herbicide Dual 960 destek'),
            (205, '05', '08', 'Fungucide destek'),
            (206, '05', '09', 'Insecticide destek'),
            (207, '05', '97', 'Malzeme İndirme Yükleme'),
            (208, '05', '98', 'Malzeme Nakliye'),
            (209, '05', '99', 'Ekipman Bakım Tamirat'),
            (210, '06', '01', 'Sulama Kurulumu'),
            (211, '06', '02', 'Sulama'),
            (212, '06', '03', 'Sulama Tamir'),
            (213, '06', '97', 'Malzeme İndirme Yükleme'),
            (214, '06', '98', 'Malzeme Nakliye'),
            (215, '06', '99', 'Ekipman Bakım Tamirat'),
            (216, '07', '01', 'Elle Çapalama'),
            (217, '07', '02', 'Mekanik Çapalama'),
            (218, '07', '97', 'Malzeme İndirme Yükleme'),
            (219, '07', '98', 'Malzeme Nakliye'),
            (220, '07', '99', 'Ekipman Bakım Tamirat'),
            (221, '08', '01', 'Kırım'),
            (222, '08', '02', 'Kırım Destek'),
            (223, '08', '03', 'Kırımdan Dikiş Mak. Taşıma'),
            (224, '08', '97', 'Malzeme İndirme Yükleme'),
            (225, '08', '98', 'Malzeme Nakliye'),
            (226, '08', '99', 'Ekipman Bakım Tamirat'),
            (227, '09', '01', 'Dikiş Mak.'),
            (228, '09', '02', 'Dikiş Mak. Destek'),
            (229, '09', '03', 'Dikiş Mak.Dan Seraya Taşıma'),
            (230, '09', '04', 'Sera Kurutma Kontrol'),
            (231, '09', '05', 'İstifleme'),
            (232, '09', '06', 'Sera Kurulumu'),
            (233, '09', '07', 'Seralarda Ot Temizliği'),
            (234, '09', '08', 'Yaprak Kesme'),
            (235, '09', '09', 'Fırın Bakım Ve Kontrol İşçiliği'),
            (236, '09', '10', 'Fırına Taşıma Ve Yerleştirme İşçiliği'),
            (237, '09', '11', 'Raks Doldurma İşçiliği'),
            (238, '09', '12', 'Seraya Taşıma Ve Serme İşçiliği'),
            (239, '09', '13', 'Yaprak Düzenleme İşçiliği'),
            (240, '09', '97', 'Malzeme İndirme Yükleme'),
            (241, '09', '98', 'Malzeme Nakliye'),
            (242, '09', '99', 'Ekipman Bakım Tamirat'),
            (243, '10', '01', 'Kutulama'),
            (244, '10', '02', 'Tavlama'),
            (245, '10', '97', 'Malzeme İndirme Yükleme'),
            (246, '10', '98', 'Malzeme Nakliye'),
            (247, '10', '99', 'Ekipman Bakım Tamirat'),
            (248, '11', '01', 'Çevre Düzenleme'),
            (249, '11', '02', 'Kahya / Aile'),
            (250, '11', '03', 'Diğer'),
            (251, '11', '04', 'Dayıbaşı'),
            (252, '11', '05', 'Bakım'),
            (253, '11', '06', 'Tespit-Tesellüm'),
            (254, '11', '07', 'Kasko , Sigorta Poliçeleri'),
            (255, '11', '08', 'Müşteri Temsil Ağırlama'),
            (256, '11', '09', 'Ekipman Bakım Tamirat'),
            (257, '11', '97', 'Malzeme İndirme Yükleme'),
            (258, '11', '98', 'Malzeme Nakliye'),
            (259, '11', '99', 'Traktör , Römork Bakım Tamirat'),
            (260, '12', '98', 'Gayrimamul'),
            (261, '13', '01', 'Supervisor'),
            (262, '14', '01', 'Sürgün Kontrol'),
            (263, '14', '02', 'Tepe Kırımı'),
            (268, '01', '15', 'TEST'),
            (269, '07', '55', 'gxfhgdfhf'),
        ]
        for op_id, stage_kod, op_kod, op_ad in operasyonlar:
            cursor.execute("""
                INSERT OR IGNORE INTO operasyonlar (id, stage_kod, operasyon_kod, operasyon_ad)
                VALUES (?, ?, ?, ?)
            """, (op_id, stage_kod, op_kod, op_ad))
        
        # Stage-operasyon kombinasyonları başlangıç verileri (init_db ile aynı format)
        stage_operasyonlar = [
            ('0101', 'Fidelik_Fide Yastığı Hazırlama'),
            ('0102', 'Fidelik_Tohum Atma'),
            ('0103', 'Fidelik_Fidelik Sulama'),
            ('0104', 'Fidelik_Fide Çekimi'),
            ('0105', 'Fidelik_Gübre Uygulama'),
            ('0106', 'Fidelik_Ot Temizleme'),
            ('0107', 'Fidelik_Sera Havalandırma - Kapatma'),
            ('0108', 'Fidelik_İlaçlama'),
            ('0109', 'Fidelik_Fide Kırpma'),
            ('0115', 'Fidelik TEST'),
            ('0197', 'Fidelik_Malzeme İndirme Yükleme'),
            ('0198', 'Fidelik_Malzeme Nakliye'),
            ('0199', 'Fidelik_Ekipman Bakım Tamirat'),
            ('0201', 'Tarla Hazırlığı_Tarla Kirası'),
            ('0202', 'Tarla Hazırlığı_Çiflik Ve Depo Kirası'),
            ('0203', 'Tarla Hazırlığı_Soil Analysis'),
            ('0204', 'Tarla Hazırlığı_Güz Sürüm'),
            ('0205', 'Tarla Hazırlığı_Bahar Sürümü'),
            ('0206', 'Tarla Hazırlığı_Dal Parçalama'),
            ('0207', 'Tarla Hazırlığı_Bahar Sürümü 2'),
            ('0208', 'Tarla Hazırlığı_Bahar Sürümü 3'),
            ('0297', 'Tarla Hazırlığı_Malzeme İndirme Yükleme'),
            ('0298', 'Tarla Hazırlığı_Malzeme Nakliye'),
            ('0299', 'Tarla Hazırlığı_Ekipman Bakım Tamirat'),
            ('0301', 'Gübreleme_Gübre Uygulama'),
            ('0302', 'Gübreleme_Gübre Uygulama Destek'),
            ('0397', 'Gübreleme_Malzeme İndirme Yükleme'),
            ('0398', 'Gübreleme_Malzeme Nakliye'),
            ('0399', 'Gübreleme_Ekipman Bakım Tamirat'),
            ('0401', 'Dikim_Dikim'),
            ('0402', 'Dikim_Dikim Destek'),
            ('0403', 'Dikim_Aşılama'),
            ('0497', 'Dikim_Malzeme İndirme Yükleme'),
            ('0498', 'Dikim_Malzeme Nakliye'),
            ('0499', 'Dikim_Ekipman Bakım Tamirat'),
            ('0501', 'İlaçlama_Herbicide Round-up'),
            ('0502', 'İlaçlama_Herbicide Dual 960'),
            ('0503', 'İlaçlama_Fungucide'),
            ('0504', 'İlaçlama_Insecticide'),
            ('0505', 'İlaçlama_Tarot'),
            ('0506', 'İlaçlama_Herbicide Round-up destek'),
            ('0507', 'İlaçlama_Herbicide Dual 960 destek'),
            ('0508', 'İlaçlama_Fungucide destek'),
            ('0509', 'İlaçlama_Insecticide destek'),
            ('0597', 'İlaçlama_Malzeme İndirme Yükleme'),
            ('0598', 'İlaçlama_Malzeme Nakliye'),
            ('0599', 'İlaçlama_Ekipman Bakım Tamirat'),
            ('0601', 'Sulama_Sulama Kurulumu'),
            ('0602', 'Sulama_Sulama'),
            ('0603', 'Sulama_Sulama Tamir'),
            ('0697', 'Sulama_Malzeme İndirme Yükleme'),
            ('0698', 'Sulama_Malzeme Nakliye'),
            ('0699', 'Sulama_Ekipman Bakım Tamirat'),
            ('0701', 'Çapalama_Elle Çapalama'),
            ('0702', 'Çapalama_Mekanik Çapalama'),
            ('0755', 'Çapalama gxfhgdfhf'),
            ('0797', 'Çapalama_Malzeme İndirme Yükleme'),
            ('0798', 'Çapalama_Malzeme Nakliye'),
            ('0799', 'Çapalama_Ekipman Bakım Tamirat'),
            ('0801', 'Kırım_Kırım'),
            ('0802', 'Kırım_Kırım Destek'),
            ('0803', 'Kırım_Kırımdan Dikiş Mak. Taşıma'),
            ('0897', 'Kırım_Malzeme İndirme Yükleme'),
            ('0898', 'Kırım_Malzeme Nakliye'),
            ('0899', 'Kırım_Ekipman Bakım Tamirat'),
            ('0901', 'Kurutma_Dikiş Mak.'),
            ('0902', 'Kurutma_Dikiş Mak. Destek'),
            ('0903', 'Kurutma_Dikiş Mak.Dan Seraya Taşıma'),
            ('0904', 'Kurutma_Sera Kurutma Kontrol'),
            ('0905', 'Kurutma_İstifleme'),
            ('0906', 'Kurutma_Sera Kurulumu'),
            ('0907', 'Kurutma_Seralarda Ot Temizliği'),
            ('0908', 'Kurutma_Yaprak Kesme'),
            ('0909', 'Kurutma_Fırın Bakım Ve Kontrol İşçiliği'),
            ('0910', 'Kurutma_Fırına Taşıma Ve Yerleştirme İşçiliği'),
            ('0911', 'Kurutma_Raks Doldurma İşçiliği'),
            ('0912', 'Kurutma_Seraya Taşıma Ve Serme İşçiliği'),
            ('0913', 'Kurutma_Yaprak Düzenleme İşçiliği'),
            ('0997', 'Kurutma_Malzeme İndirme Yükleme'),
            ('0998', 'Kurutma_Malzeme Nakliye'),
            ('0999', 'Kurutma_Ekipman Bakım Tamirat'),
            ('1001', 'Kutulama_Kutulama'),
            ('1002', 'Kutulama_Tavlama'),
            ('1097', 'Kutulama_Malzeme İndirme Yükleme'),
            ('1098', 'Kutulama_Malzeme Nakliye'),
            ('1099', 'Kutulama_Ekipman Bakım Tamirat'),
            ('1101', 'Diğer_Çevre Düzenleme'),
            ('1102', 'Diğer_Kahya / Aile'),
            ('1103', 'Diğer_Diğer'),
            ('1104', 'Diğer_Dayıbaşı'),
            ('1105', 'Diğer_Bakım'),
            ('1106', 'Diğer_Tespit-Tesellüm'),
            ('1107', 'Diğer_Kasko , Sigorta Poliçeleri'),
            ('1108', 'Diğer_Müşteri Temsil Ağırlama'),
            ('1109', 'Diğer_Ekipman Bakım Tamirat'),
            ('1197', 'Diğer_Malzeme İndirme Yükleme'),
            ('1198', 'Diğer_Malzeme Nakliye'),
            ('1199', 'Diğer_Traktör , Römork Bakım Tamirat'),
            ('1298', 'Nakliye_Gayrimamul'),
            ('1301', 'Supervisor_Supervisor'),
            ('1401', 'Kültürel İşlemler_Sürgün Kontrol'),
            ('1402', 'Kültürel İşlemler_Tepe Kırımı'),
        ]
        for kod, ad in stage_operasyonlar:
            cursor.execute("""
                INSERT OR IGNORE INTO stage_operasyonlar (kod, ad) VALUES (?, ?)
            """, (kod, ad))
        
        # Birim ücretler başlangıç verileri
        birim_ucretler = [
            (3, 'ADET', 1000.00),
            (4, 'YEVMİYE', 1200.00),
            (5, 'TEST', 5000.00)
        ]
        for birim_id, birim, ucret in birim_ucretler:
            cursor.execute("""
                INSERT OR IGNORE INTO birim_ucretler (id, birim, ucret) VALUES (?, ?, ?)
            """, (birim_id, birim, ucret))
        
        conn.commit()
        print("✅ SQLite Migration başarıyla tamamlandı!")
        print(f"✅ {len(bolge_kodlari)} bölge kodu eklendi!")
        print(f"✅ {len(kaynak_tipleri)} kaynak tipi eklendi!")
        print(f"✅ {len(stages)} stage eklendi!")
        print(f"✅ {len(operasyonlar)} operasyon eklendi!")
        print(f"✅ {len(stage_operasyonlar)} stage-operasyon kombinasyonu eklendi!")
        print(f"✅ {len(birim_ucretler)} birim ücret eklendi!")
    except Exception as e:
        print(f"❌ Migration hatası: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Migration'ı çalıştır
    migrate_db()

    # Tabloları oluştur
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS birim_ucretler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        birim TEXT,
        ucret REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bolge_kodlari (
        kod TEXT PRIMARY KEY,
        ad TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS kaynak_tipleri (
        kod TEXT PRIMARY KEY,
        ad TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stages (
        kod TEXT PRIMARY KEY,
        ad TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS operasyonlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stage_kod TEXT NOT NULL,
        operasyon_kod TEXT NOT NULL,
        operasyon_ad TEXT NOT NULL,
        FOREIGN KEY (stage_kod) REFERENCES stages(kod),
        UNIQUE (stage_kod, operasyon_kod)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stage_operasyonlar (
        kod TEXT PRIMARY KEY,
        ad TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'normal',
        default_bolge_kodu TEXT
    )
    ''')

    # Kullanıcı-bölge ilişkisi tablosu (bir kullanıcının birden fazla bölgesi olabilir)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_bolgeler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        bolge_kodu TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, bolge_kodu)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        tarih DATE NOT NULL,
        bolge_kodu TEXT,
        kaynak_tipi TEXT,
        stage TEXT,
        stage_operasyon TEXT,
        no_su TEXT,
        kimden_alindigi TEXT,
        aciklama TEXT,
        tutar REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Harcama talep tablosu (kullanıcıdan bağımsız)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS harcama_talep (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        no INTEGER,
        tarih DATE NOT NULL,
        bolge_kodu TEXT,
        kaynak_tipi_kodu TEXT,
        stage_kodu TEXT,
        stage_operasyon_kodu TEXT,
        safha TEXT,
        harcama_kalemi TEXT,
        birim TEXT,
        miktar REAL,
        birim_ucret REAL,
        toplam REAL,
        aciklama TEXT,
        is_manuel INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Manuel değişiklikler tablosu (hangi kullanıcı ne değiştirdi)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS harcama_talep_manuel_degisiklikler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        harcama_talep_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        alan_adi TEXT NOT NULL,
        eski_deger TEXT,
        yeni_deger TEXT,
        degisiklik_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (harcama_talep_id) REFERENCES harcama_talep(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Başlangıç verilerini ekle

    # birim_ucretler
    cursor.executemany('INSERT OR IGNORE INTO birim_ucretler (id, birim, ucret) VALUES (?, ?, ?)', [
        (3, 'ADET', 1000.00),
        (4, 'YEVMİYE', 1200.00),
        (5, 'TEST', 5000.00)
    ])

    # bolge_kodlari
    cursor.executemany('INSERT OR IGNORE INTO bolge_kodlari (kod, ad) VALUES (?, ?)', [
        ('10', 'ADY - DOĞU'),
        ('11', 'ADY - BATI'),
        ('20', 'MAN'),
        ('30', 'MAR'),
        ('21', 'MAN - FCV MAK.'),
        ('24', 'MAN - N.RUSTICA'),
        ('35', 'MAR - IZ'),
        ('25', 'MAN - IZMIR'),
        ('12', 'ADY DOĞU-JTI SCV'),
        ('13', 'ADY BATI-JTI SCV'),
        ('22', 'MAN-JTI SCV'),
        ('32', 'MAR-JTI SCV'),
        ('14', 'ADY DOĞU-SCV TOPPING'),
        ('15', 'ADY BATI-SCV TOPPING'),
        ('26', 'MAN-SCV TOPPING'),
        ('36', 'MAR-SCV TOPPING'),
        ('16', 'ADY DOĞU-PMI SCV'),
        ('17', 'ADY BATI-PMI SCV'),
        ('23', 'MAN-PMI SCV'),
        ('33', 'MAR-PMI SCV'),
        ('18', 'ADY BATI - N.RUSTICA'),
        ('37', 'MAR-BASMA'),
        ('34', 'MAR-N.RUSTICA'),
        ('38', 'MAR-PRILEP'),
        ('39', 'MAR-KATERINI')
    ])

    # kaynak_tipleri
    cursor.executemany('INSERT OR IGNORE INTO kaynak_tipleri (kod, ad) VALUES (?, ?)', [
        ('01', 'İşçilik'),
        ('02', 'Malzeme'),
        ('03', 'Hizmet'),
        ('04', 'Enerji'),
        ('05', 'Kiralama')
    ])

    # stages
    cursor.executemany('INSERT OR IGNORE INTO stages (kod, ad) VALUES (?, ?)', [
        ('01', 'Fidelik'),
        ('02', 'Tarla Hazırlığı'),
        ('03', 'Gübre Atma'),
        ('04', 'Dikim'),
        ('05', 'İlaç Uygulama'),
        ('06', 'Sulama'),
        ('07', 'Çapalama'),
        ('08', 'Kırım'),
        ('09', 'Kurutma'),
        ('10', 'Kutulama'),
        ('11', 'Diğer is-işçilik'),
        ('12', 'Nakliye'),
        ('13', 'Supervisor'),
        ('14', 'Kültürel İşlemler'),
        ('15', 'TESTRRR')
    ])

    # operasyonlar (TÜM veriler)
    cursor.executemany('''
    INSERT OR IGNORE INTO operasyonlar (id, stage_kod, operasyon_kod, operasyon_ad) 
    VALUES (?, ?, ?, ?)
    ''', [
        (164, '01', '01', 'Fide Yastığı Hazırlama'),
        (165, '01', '02', 'Tohum Atma'),
        (166, '01', '03', 'Sulama'),
        (167, '01', '04', 'Fide Çekimi'),
        (168, '01', '05', 'Gübre Uygulama'),
        (169, '01', '06', 'Ot Temizleme'),
        (170, '01', '07', 'Sera Havalandırma - Kapatma'),
        (171, '01', '08', 'İlaçlama'),
        (172, '01', '09', 'Fide Kırpma'),
        (173, '01', '97', 'Malzeme İndirme Yükleme'),
        (174, '01', '98', 'Malzeme Nakliye'),
        (175, '01', '99', 'Ekipman Bakım Tamirat'),
        (176, '02', '01', 'Tarla Kirası'),
        (177, '02', '02', 'Çiflik Ve Depo Kirası'),
        (178, '02', '03', 'Soil Analysis'),
        (179, '02', '04', 'Güz Sürüm'),
        (180, '02', '05', 'Bahar Sürümü'),
        (181, '02', '06', 'Dal Parçalama'),
        (182, '02', '07', 'Bahar Sürümü 2'),
        (183, '02', '08', 'Bahar Sürümü 3'),
        (184, '02', '97', 'Malzeme İndirme Yükleme'),
        (185, '02', '98', 'Malzeme Nakliye'),
        (186, '02', '99', 'Ekipman Bakım Tamirat'),
        (187, '03', '01', 'Gübre Uygulama'),
        (188, '03', '02', 'Gübre Uygulama Destek'),
        (189, '03', '97', 'Malzeme İndirme Yükleme'),
        (190, '03', '98', 'Malzeme Nakliye'),
        (191, '03', '99', 'Ekipman Bakım Tamirat'),
        (192, '04', '01', 'Dikim'),
        (193, '04', '02', 'Dikim Destek'),
        (194, '04', '03', 'Aşılama'),
        (195, '04', '97', 'Malzeme İndirme Yükleme'),
        (196, '04', '98', 'Malzeme Nakliye'),
        (197, '04', '99', 'Ekipman Bakım Tamirat'),
        (198, '05', '01', 'Herbicide Round-up'),
        (199, '05', '02', 'Herbicide Dual 960'),
        (200, '05', '03', 'Fungucide'),
        (201, '05', '04', 'Insecticide'),
        (202, '05', '05', 'Tarot'),
        (203, '05', '06', 'Herbicide Round-up destek'),
        (204, '05', '07', 'Herbicide Dual 960 destek'),
        (205, '05', '08', 'Fungucide destek'),
        (206, '05', '09', 'Insecticide destek'),
        (207, '05', '97', 'Malzeme İndirme Yükleme'),
        (208, '05', '98', 'Malzeme Nakliye'),
        (209, '05', '99', 'Ekipman Bakım Tamirat'),
        (210, '06', '01', 'Sulama Kurulumu'),
        (211, '06', '02', 'Sulama'),
        (212, '06', '03', 'Sulama Tamir'),
        (213, '06', '97', 'Malzeme İndirme Yükleme'),
        (214, '06', '98', 'Malzeme Nakliye'),
        (215, '06', '99', 'Ekipman Bakım Tamirat'),
        (216, '07', '01', 'Elle Çapalama'),
        (217, '07', '02', 'Mekanik Çapalama'),
        (218, '07', '97', 'Malzeme İndirme Yükleme'),
        (219, '07', '98', 'Malzeme Nakliye'),
        (220, '07', '99', 'Ekipman Bakım Tamirat'),
        (221, '08', '01', 'Kırım'),
        (222, '08', '02', 'Kırım Destek'),
        (223, '08', '03', 'Kırımdan Dikiş Mak. Taşıma'),
        (224, '08', '97', 'Malzeme İndirme Yükleme'),
        (225, '08', '98', 'Malzeme Nakliye'),
        (226, '08', '99', 'Ekipman Bakım Tamirat'),
        (227, '09', '01', 'Dikiş Mak.'),
        (228, '09', '02', 'Dikiş Mak. Destek'),
        (229, '09', '03', 'Dikiş Mak.Dan Seraya Taşıma'),
        (230, '09', '04', 'Sera Kurutma Kontrol'),
        (231, '09', '05', 'İstifleme'),
        (232, '09', '06', 'Sera Kurulumu'),
        (233, '09', '07', 'Seralarda Ot Temizliği'),
        (234, '09', '08', 'Yaprak Kesme'),
        (235, '09', '09', 'Fırın Bakım Ve Kontrol İşçiliği'),
        (236, '09', '10', 'Fırına Taşıma Ve Yerleştirme İşçiliği'),
        (237, '09', '11', 'Raks Doldurma İşçiliği'),
        (238, '09', '12', 'Seraya Taşıma Ve Serme İşçiliği'),
        (239, '09', '13', 'Yaprak Düzenleme İşçiliği'),
        (240, '09', '97', 'Malzeme İndirme Yükleme'),
        (241, '09', '98', 'Malzeme Nakliye'),
        (242, '09', '99', 'Ekipman Bakım Tamirat'),
        (243, '10', '01', 'Kutulama'),
        (244, '10', '02', 'Tavlama'),
        (245, '10', '97', 'Malzeme İndirme Yükleme'),
        (246, '10', '98', 'Malzeme Nakliye'),
        (247, '10', '99', 'Ekipman Bakım Tamirat'),
        (248, '11', '01', 'Çevre Düzenleme'),
        (249, '11', '02', 'Kahya / Aile'),
        (250, '11', '03', 'Diğer'),
        (251, '11', '04', 'Dayıbaşı'),
        (252, '11', '05', 'Bakım'),
        (253, '11', '06', 'Tespit-Tesellüm'),
        (254, '11', '07', 'Kasko , Sigorta Poliçeleri'),
        (255, '11', '08', 'Müşteri Temsil Ağırlama'),
        (256, '11', '09', 'Ekipman Bakım Tamirat'),
        (257, '11', '97', 'Malzeme İndirme Yükleme'),
        (258, '11', '98', 'Malzeme Nakliye'),
        (259, '11', '99', 'Traktör , Römork Bakım Tamirat'),
        (260, '12', '98', 'Gayrimamul'),
        (261, '13', '01', 'Supervisor'),
        (262, '14', '01', 'Sürgün Kontrol'),
        (263, '14', '02', 'Tepe Kırımı'),
        (268, '01', '15', 'TEST'),
        (269, '07', '55', 'gxfhgdfhf')
    ])

    # stage_operasyonlar (TÜM veriler)
    cursor.executemany('''
    INSERT OR IGNORE INTO stage_operasyonlar (kod, ad) 
    VALUES (?, ?)
    ''', [
        ('0101', 'Fidelik_Fide Yastığı Hazırlama'),
        ('0102', 'Fidelik_Tohum Atma'),
        ('0103', 'Fidelik_Fidelik Sulama'),
        ('0104', 'Fidelik_Fide Çekimi'),
        ('0105', 'Fidelik_Gübre Uygulama'),
        ('0106', 'Fidelik_Ot Temizleme'),
        ('0107', 'Fidelik_Sera Havalandırma - Kapatma'),
        ('0108', 'Fidelik_İlaçlama'),
        ('0109', 'Fidelik_Fide Kırpma'),
        ('0115', 'Fidelik TEST'),
        ('0197', 'Fidelik_Malzeme İndirme Yükleme'),
        ('0198', 'Fidelik_Malzeme Nakliye'),
        ('0199', 'Fidelik_Ekipman Bakım Tamirat'),
        ('0201', 'Tarla Hazırlığı_Tarla Kirası'),
        ('0202', 'Tarla Hazırlığı_Çiflik Ve Depo Kirası'),
        ('0203', 'Tarla Hazırlığı_Soil Analysis'),
        ('0204', 'Tarla Hazırlığı_Güz Sürüm'),
        ('0205', 'Tarla Hazırlığı_Bahar Sürümü'),
        ('0206', 'Tarla Hazırlığı_Dal Parçalama'),
        ('0207', 'Tarla Hazırlığı_Bahar Sürümü 2'),
        ('0208', 'Tarla Hazırlığı_Bahar Sürümü 3'),
        ('0297', 'Tarla Hazırlığı_Malzeme İndirme Yükleme'),
        ('0298', 'Tarla Hazırlığı_Malzeme Nakliye'),
        ('0299', 'Tarla Hazırlığı_Ekipman Bakım Tamirat'),
        ('0301', 'Gübreleme_Gübre Uygulama'),
        ('0302', 'Gübreleme_Gübre Uygulama Destek'),
        ('0397', 'Gübreleme_Malzeme İndirme Yükleme'),
        ('0398', 'Gübreleme_Malzeme Nakliye'),
        ('0399', 'Gübreleme_Ekipman Bakım Tamirat'),
        ('0401', 'Dikim_Dikim'),
        ('0402', 'Dikim_Dikim Destek'),
        ('0403', 'Dikim_Aşılama'),
        ('0497', 'Dikim_Malzeme İndirme Yükleme'),
        ('0498', 'Dikim_Malzeme Nakliye'),
        ('0499', 'Dikim_Ekipman Bakım Tamirat'),
        ('0501', 'İlaçlama_Herbicide Round-up'),
        ('0502', 'İlaçlama_Herbicide Dual 960'),
        ('0503', 'İlaçlama_Fungucide'),
        ('0504', 'İlaçlama_Insecticide'),
        ('0505', 'İlaçlama_Tarot'),
        ('0506', 'İlaçlama_Herbicide Round-up destek'),
        ('0507', 'İlaçlama_Herbicide Dual 960 destek'),
        ('0508', 'İlaçlama_Fungucide destek'),
        ('0509', 'İlaçlama_Insecticide destek'),
        ('0597', 'İlaçlama_Malzeme İndirme Yükleme'),
        ('0598', 'İlaçlama_Malzeme Nakliye'),
        ('0599', 'İlaçlama_Ekipman Bakım Tamirat'),
        ('0601', 'Sulama_Sulama Kurulumu'),
        ('0602', 'Sulama_Sulama'),
        ('0603', 'Sulama_Sulama Tamir'),
        ('0697', 'Sulama_Malzeme İndirme Yükleme'),
        ('0698', 'Sulama_Malzeme Nakliye'),
        ('0699', 'Sulama_Ekipman Bakım Tamirat'),
        ('0701', 'Çapalama_Elle Çapalama'),
        ('0702', 'Çapalama_Mekanik Çapalama'),
        ('0755', 'Çapalama gxfhgdfhf'),
        ('0797', 'Çapalama_Malzeme İndirme Yükleme'),
        ('0798', 'Çapalama_Malzeme Nakliye'),
        ('0799', 'Çapalama_Ekipman Bakım Tamirat'),
        ('0801', 'Kırım_Kırım'),
        ('0802', 'Kırım_Kırım Destek'),
        ('0803', 'Kırım_Kırımdan Dikiş Mak. Taşıma'),
        ('0897', 'Kırım_Malzeme İndirme Yükleme'),
        ('0898', 'Kırım_Malzeme Nakliye'),
        ('0899', 'Kırım_Ekipman Bakım Tamirat'),
        ('0901', 'Kurutma_Dikiş Mak.'),
        ('0902', 'Kurutma_Dikiş Mak. Destek'),
        ('0903', 'Kurutma_Dikiş Mak.Dan Seraya Taşıma'),
        ('0904', 'Kurutma_Sera Kurutma Kontrol'),
        ('0905', 'Kurutma_İstifleme'),
        ('0906', 'Kurutma_Sera Kurulumu'),
        ('0907', 'Kurutma_Seralarda Ot Temizliği'),
        ('0908', 'Kurutma_Yaprak Kesme'),
        ('0909', 'Kurutma_Fırın Bakım Ve Kontrol İşçiliği'),
        ('0910', 'Kurutma_Fırına Taşıma Ve Yerleştirme İşçiliği'),
        ('0911', 'Kurutma_Raks Doldurma İşçiliği'),
        ('0912', 'Kurutma_Seraya Taşıma Ve Serme İşçiliği'),
        ('0913', 'Kurutma_Yaprak Düzenleme İşçiliği'),
        ('0997', 'Kurutma_Malzeme İndirme Yükleme'),
        ('0998', 'Kurutma_Malzeme Nakliye'),
        ('0999', 'Kurutma_Ekipman Bakım Tamirat'),
        ('1001', 'Kutulama_Kutulama'),
        ('1002', 'Kutulama_Tavlama'),
        ('1097', 'Kutulama_Malzeme İndirme Yükleme'),
        ('1098', 'Kutulama_Malzeme Nakliye'),
        ('1099', 'Kutulama_Ekipman Bakım Tamirat'),
        ('1101', 'Diğer_Çevre Düzenleme'),
        ('1102', 'Diğer_Kahya / Aile'),
        ('1103', 'Diğer_Diğer'),
        ('1104', 'Diğer_Dayıbaşı'),
        ('1105', 'Diğer_Bakım'),
        ('1106', 'Diğer_Tespit-Tesellüm'),
        ('1107', 'Diğer_Kasko , Sigorta Poliçeleri'),
        ('1108', 'Diğer_Müşteri Temsil Ağırlama'),
        ('1109', 'Diğer_Ekipman Bakım Tamirat'),
        ('1197', 'Diğer_Malzeme İndirme Yükleme'),
        ('1198', 'Diğer_Malzeme Nakliye'),
        ('1199', 'Diğer_Traktör , Römork Bakım Tamirat'),
        ('1298', 'Nakliye_Gayrimamul'),
        ('1301', 'Supervisor_Supervisor'),
        ('1401', 'Kültürel İşlemler_Sürgün Kontrol'),
        ('1402', 'Kültürel İşlemler_Tepe Kırımı')
    ])

    # users - Varsayılan admin kullanıcısı
    password_hash_admin = generate_password_hash('admin123')  # Admin şifresi: admin123
    
    # SQL Server için INSERT komutu
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM users WHERE username = 'admin')
        BEGIN
            INSERT INTO users (username, password_hash, role) 
            VALUES ('admin', ?, 'admin')
        END
    """, (password_hash_admin,))
    
    # Eski kullanıcılar (opsiyonel - varsa ekle)
    password_hash1 = generate_password_hash('bunyamin_password')
    password_hash2 = generate_password_hash('gunnur_password')
    
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM users WHERE username = 'bunyamin')
        BEGIN
            INSERT INTO users (username, password_hash, role) 
            VALUES ('bunyamin', ?, 'normal')
        END
    """, (password_hash1,))
    
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM users WHERE username = 'gunnur')
        BEGIN
            INSERT INTO users (username, password_hash, role) 
            VALUES ('gunnur', ?, 'normal')
        END
    """, (password_hash2,))
    
    # Admin kullanıcısına tüm bölgelere erişim için bölge eklemeye gerek yok (admin rolü tüm bölgelere erişir)
    # Örnek kullanıcılara bölge ekle (SQL Server için)
    
    # bunyamin kullanıcısına bölge ekle
    cursor.execute("SELECT id FROM users WHERE username = 'bunyamin'")
    bunyamin_row = cursor.fetchone()
    if bunyamin_row:
        bunyamin_id = bunyamin_row[0]
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM user_bolgeler WHERE user_id = ? AND bolge_kodu = '10')
            BEGIN
                INSERT INTO user_bolgeler (user_id, bolge_kodu) VALUES (?, '10')
            END
        """, (bunyamin_id, bunyamin_id))
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM user_bolgeler WHERE user_id = ? AND bolge_kodu = '20')
            BEGIN
                INSERT INTO user_bolgeler (user_id, bolge_kodu) VALUES (?, '20')
            END
        """, (bunyamin_id, bunyamin_id))
    
    # gunnur kullanıcısına bölge ekle
    cursor.execute("SELECT id FROM users WHERE username = 'gunnur'")
    gunnur_row = cursor.fetchone()
    if gunnur_row:
        gunnur_id = gunnur_row[0]
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM user_bolgeler WHERE user_id = ? AND bolge_kodu = '22')
            BEGIN
                INSERT INTO user_bolgeler (user_id, bolge_kodu) VALUES (?, '22')
            END
        """, (gunnur_id, gunnur_id))
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM user_bolgeler WHERE user_id = ? AND bolge_kodu = '30')
            BEGIN
                INSERT INTO user_bolgeler (user_id, bolge_kodu) VALUES (?, '30')
            END
        """, (gunnur_id, gunnur_id))

    # expenses (TÜM veriler)
    cursor.executemany('''
    INSERT OR IGNORE INTO expenses (id, user_id, tarih, bolge_kodu, kaynak_tipi, stage, 
                         stage_operasyon, no_su, kimden_alindigi, aciklama, tutar, created_at) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (23, 1, '2025-06-11', '10.', '01', '01', '0101', '85', 'dfd', 'vhjvb', 8600.00, '2025-06-11 18:37:39.5700000'),
        (24, 1, '2025-06-12', '10.', '05', '03', '0301', '333', 'sxd', 'xacsdc', 11111.00,
         '2025-06-12 12:21:12.4570000'),
        (25, 1, '2025-06-12', '23', '01', '03', '0399', '11112', 'dsfs', 'sdgdfg', 88888.00,
         '2025-06-12 14:02:56.8000000'),
        (27, 1, '2025-06-12', '10.', '04', '01', '0105', '2222', 'akakakka', 'skmms', 4444.00,
         '2025-06-12 14:31:56.5500000'),
        (30, 1, '2025-06-12', '10.', '01', '02', '0204', '555', 'kk', 'jjh', 1000.00, '2025-06-12 15:16:27.5600000'),
        (31, 1, '2025-06-12', '10.', '05', '01', '0103', '2', 'ddd', 'ss', 222.00, '2025-06-12 15:20:19.3530000'),
        (34, 2, '2025-06-14', '22', '01', '01', '0105', '7', 'asa', 'ad', 888.00, '2025-06-14 13:50:43.1400000'),
        (35, 1, '2025-06-14', '10.', '01', '04', '0401', '12', 'aa', 'aa', 2000.00, '2025-06-14 13:58:45.3870000'),
        (36, 2, '2025-06-17', '22', '01', '04', '0403', '125', 'kkkkk', 'gjhghj', 2000.00,
         '2025-06-17 10:33:54.6870000'),
        (37, 1, '2025-06-22', '10.', '01', '01', '0101', '111', 'wsds', 'dsds', 1111.00, '2025-06-22 09:55:51.0370000')
    ])

    conn.commit()
    conn.close()

@app.route('/api/register', methods=['POST'])
def register():
    """Kullanıcı kayıt - Sadece admin tarafından kullanılabilir"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    admin_username = data.get('admin_username')  # İstek yapan admin kullanıcısı
    admin_password = data.get('admin_password')  # Admin şifresi (doğrulama için)

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    # Admin doğrulaması
    if not admin_username or not admin_password:
        return jsonify({'error': 'Admin credentials required'}), 403

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        
        # Admin kullanıcısını doğrula
        cursor.execute("SELECT id, password_hash, role FROM users WHERE username = ?", (admin_username,))
        admin_row = cursor.fetchone()
        if not admin_row:
            return jsonify({'error': 'Admin user not found'}), 403
        
        admin_id, admin_password_hash, admin_role = admin_row
        
        # Şifreyi kontrol et
        if not check_password_hash(admin_password_hash, admin_password):
            return jsonify({'error': 'Invalid admin credentials'}), 403
        
        # Admin rolü kontrolü
        if admin_role != 'admin':
            return jsonify({'error': 'Only admin users can register new users'}), 403

        # Kullanıcı adı daha önce varsa hata ver
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return jsonify({'error': 'Username already exists'}), 409

        # Yeni kullanıcı ekle (varsayılan rol: normal)
        password_hash = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'normal')", 
                      (username, password_hash))
        conn.commit()
        return jsonify({'message': 'Kullanıcı Başarıyla Kayıt Edildi'}), 201
    except Exception as e:
        print(f"DB error: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    # Önce migration'ı çalıştır (kolonlar yoksa ekler)
    migrate_db()

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        
        # Admin kullanıcısı yoksa oluştur
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin_exists = cursor.fetchone()
        if not admin_exists:
            password_hash_admin = generate_password_hash('admin123')
            try:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role) 
                    VALUES ('admin', ?, 'admin')
                """, (password_hash_admin,))
                conn.commit()
                print("✅ Admin kullanıcısı oluşturuldu (kullanıcı adı: admin, şifre: admin123)")
            except Exception as admin_error:
                print(f"Admin kullanıcısı oluşturulurken hata: {admin_error}")
                conn.rollback()
        
        # Kolonların varlığını kontrol et ve güvenli SELECT yap
        try:
            cursor.execute("SELECT id, password_hash, role, default_bolge_kodu FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row is None:
                return jsonify({'error': 'Invalid username or password'}), 401
            user_id, password_hash, role, default_bolge_kodu = row
        except Exception as col_error:
            # Kolonlar yoksa eski SELECT'i dene
            print(f"Kolon hatası, eski SELECT deneniyor: {col_error}")
            cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row is None:
                return jsonify({'error': 'Invalid username or password'}), 401
            user_id, password_hash = row
            role = 'normal'
            default_bolge_kodu = None
            # Migration'ı tekrar çalıştır
            migrate_db()
            # Tekrar dene
            try:
                cursor.execute("SELECT id, password_hash, role, default_bolge_kodu FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
                if row:
                    user_id, password_hash, role, default_bolge_kodu = row
            except:
                pass  # Eski değerleri kullan
        
        # Şifre kontrolü
        password_match = check_password_hash(password_hash, password)
        if not password_match:
            print(f"DEBUG - Şifre kontrolü başarısız. Kullanıcı: {username}")
            return jsonify({'error': 'Invalid username or password'}), 401
        
        if password_match:
            # Kullanıcının bölgelerini al
            cursor.execute("SELECT bolge_kodu FROM user_bolgeler WHERE user_id = ?", (user_id,))
            bolge_rows = cursor.fetchall()
            bolge_kodlari = [row[0] for row in bolge_rows]
            
            # Eğer user_bolgeler tablosunda kayıt yoksa default_bolge_kodu'nu kullan
            if not bolge_kodlari and default_bolge_kodu:
                bolge_kodlari = [default_bolge_kodu]
            
            # Role varsayılan değer atama
            if not role:
                role = 'normal'
            
            # Giriş başarılı - kullanıcı bilgilerini döndür
            return jsonify({
                'message': 'Giriş Başarılı',
                'user_id': user_id,
                'username': username,
                'role': role,
                'bolge_kodlari': bolge_kodlari,
                'default_bolge_kodu': default_bolge_kodu
            }), 200
        else:
            return jsonify({'error': 'Yanlış kullanıcı adı veya şifre'}), 401
    except Exception as e:
        print(f"DB error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Database error'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/bolge_kodlari', methods=['GET'])
def get_bolge_kodlari():
    """Tüm bölge kodlarını döndürür (admin ve üst düzey yönetici için)"""
    user_id = request.args.get('user_id', type=int)
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Eğer user_id verilmişse, kullanıcının rolünü kontrol et
            if user_id:
                cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
                user_row = cursor.fetchone()
                if user_row:
                    role = user_row[0] or 'normal'
                    
                    # Admin veya üst düzey yönetici ise tüm bölgeleri döndür
                    if role in ['admin', 'ust_duzey_yonetici']:
                        cursor.execute("SELECT kod, ad FROM bolge_kodlari")
                        rows = cursor.fetchall()
                        result = {row[0]: row[1] for row in rows}
                        return jsonify(result)
                    else:
                        # Normal kullanıcı ise sadece kendi bölgelerini döndür
                        cursor.execute("""
                            SELECT bk.kod, bk.ad 
                            FROM bolge_kodlari bk
                            INNER JOIN user_bolgeler ub ON bk.kod = ub.bolge_kodu
                            WHERE ub.user_id = ?
                        """, (user_id,))
                        rows = cursor.fetchall()
                        result = {row[0]: row[1] for row in rows}
                        return jsonify(result)
            
            # user_id verilmemişse tüm bölgeleri döndür
            cursor.execute("SELECT kod, ad FROM bolge_kodlari")
            rows = cursor.fetchall()
            result = {row[0]: row[1] for row in rows}
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "Database connection failed"}), 500

@app.route('/api/kaynak_tipleri', methods=['GET'])
def get_kaynak_tipleri():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT kod, ad FROM kaynak_tipleri")
            rows = cursor.fetchall()
            result = {row[0]: row[1] for row in rows}
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "Database connection failed"}), 500

@app.route('/api/stages', methods=['GET'])
def get_stages():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT kod, ad FROM stages")
            rows = cursor.fetchall()
            result = {row[0]: row[1] for row in rows}
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "Database connection failed"}), 500

@app.route('/api/operasyonlar', methods=['GET'])
def get_operasyonlar():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT stage_kod, operasyon_kod, operasyon_ad FROM operasyonlar")
            rows = cursor.fetchall()

            # Organize by stage_kod
            result = {}
            for row in rows:
                stage_kod = row[0]  # Access by index instead of name
                if stage_kod not in result:
                    result[stage_kod] = {}
                result[stage_kod][row[1]] = row[2]  # operasyon_kod and operasyon_ad

            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "Database connection failed"}), 500

@app.route('/api/stage_operasyonlar', methods=['GET'])
def get_stage_operasyonlar():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT kod, ad FROM stage_operasyonlar")
            rows = cursor.fetchall()
            result = {row[0]: row[1] for row in rows}
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"error": "Database connection failed"}), 500

@app.route('/api/birim_ucretler', methods=['GET'])
def get_birim_ucretler():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT birim, ucret FROM birim_ucretler")
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            data = [dict(zip(column_names, row)) for row in rows]
            return jsonify(data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            connection.close()
    else:
        return jsonify({'error': 'Veritabanına bağlanılamadı'}), 500

@app.route('/api/all_data', methods=['GET'])
def get_all_data():
    """Get all data needed for the application in one request"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()

            # Get bölge kodları
            cursor.execute("SELECT kod, ad FROM bolge_kodlari")
            bolge_rows = cursor.fetchall()
            bolge_kodlari = {row[0]: row[1] for row in bolge_rows}

            # Get kaynak tipleri
            cursor.execute("SELECT kod, ad FROM kaynak_tipleri")
            kaynak_rows = cursor.fetchall()
            kaynak_tipleri = {row[0]: row[1] for row in kaynak_rows}

            # Get stages
            cursor.execute("SELECT kod, ad FROM stages")
            stage_rows = cursor.fetchall()
            stages = {row[0]: row[1] for row in stage_rows}

            # Get operasyonlar
            cursor.execute("SELECT stage_kod, operasyon_kod, operasyon_ad FROM operasyonlar")
            operasyon_rows = cursor.fetchall()
            operasyonlar = {}
            for row in operasyon_rows:
                stage_kod = row[0]
                if stage_kod not in operasyonlar:
                    operasyonlar[stage_kod] = {}
                operasyonlar[stage_kod][row[1]] = row[2]

            # Get stage-operasyon combinations
            cursor.execute("SELECT kod, ad FROM stage_operasyonlar")
            stage_op_rows = cursor.fetchall()
            stage_operasyonlar = {row[0]: row[1] for row in stage_op_rows}

            result = {
                'bolge_kodlari': bolge_kodlari,
                'kaynak_tipleri': kaynak_tipleri,
                'stages': stages,
                'operasyonlar': operasyonlar,
                'stage_operasyonlar': stage_operasyonlar
            }

            return jsonify({"success": True, "data": result})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "error": "Database connection failed"}), 500


@app.route('/api/add_kaynak_tipi', methods=['POST'])
def add_kaynak_tipi():
    data = request.json
    if not data or 'kod' not in data or 'ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = "INSERT INTO kaynak_tipleri (kod, ad) VALUES (?, ?)"
            cursor.execute(query, (data['kod'], data['ad']))
            connection.commit()
            return jsonify({"success": True, "message": "Kaynak tipi başarıyla eklendi"}), 201
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

@app.route('/api/add_stage', methods=['POST'])
def add_stage():
    data = request.json
    if not data or 'kod' not in data or 'ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = "INSERT INTO stages (kod, ad) VALUES (?, ?)"
            cursor.execute(query, (data['kod'], data['ad']))
            connection.commit()
            return jsonify({"success": True, "message": "Stage başarıyla eklendi"}), 201
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

@app.route('/api/add_operasyon', methods=['POST'])
def add_operasyon():
    data = request.json
    if not data or 'stage_kod' not in data or 'operasyon_kod' not in data or 'operasyon_ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400

    stage_kod = data['stage_kod']
    operasyon_kod = data['operasyon_kod']
    operasyon_ad = data['operasyon_ad']

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()

            # 1. stage_kod veritabanında var mı kontrol et
            cursor.execute("SELECT ad FROM stages WHERE kod = ?", (stage_kod,))
            stage_row = cursor.fetchone()
            if not stage_row:
                return jsonify({
                    "success": False,
                    "message": f"'{stage_kod}' kodlu stage DB'de bulunamadı. Lütfen önce stage kodları tablosundan bu stage'i ekleyin.",
                    "redirect": "stages_tab"
                }), 201

            stage_ad = stage_row[0]

            # 2. operasyonlar tablosunda zaten var mı kontrol et
            cursor.execute(
                "SELECT operasyon_ad FROM operasyonlar WHERE stage_kod = ? AND operasyon_kod = ?",
                (stage_kod, operasyon_kod)
            )
            existing_operasyon = cursor.fetchone()
            
            # 3. stage_operasyonlar tablosunda zaten var mı kontrol et
            kod = f"{stage_kod}{operasyon_kod}"
            cursor.execute("SELECT ad FROM stage_operasyonlar WHERE kod = ?", (kod,))
            existing_stage_op = cursor.fetchone()

            # Eğer operasyon zaten varsa, hata döndür (UNIQUE constraint)
            if existing_operasyon:
                return jsonify({
                    "success": False,
                    "message": f"Bu operasyon zaten mevcut: Stage {stage_kod}, Operasyon {operasyon_kod}. Mevcut ad: {existing_operasyon[0]}"
                }), 400

            # 4. operasyonlar tablosuna ekle
            cursor.execute(
                "INSERT INTO operasyonlar (stage_kod, operasyon_kod, operasyon_ad) VALUES (?, ?, ?)",
                (stage_kod, operasyon_kod, operasyon_ad)
            )

            # 5. stage_operasyonlar tablosuna ekle veya güncelle
            ad = f"{stage_ad}_{operasyon_ad}"
            if not existing_stage_op:
                # Eğer yoksa, ekle
                cursor.execute(
                    "INSERT INTO stage_operasyonlar (kod, ad) VALUES (?, ?)",
                    (kod, ad)
                )
            else:
                # Eğer varsa, adını güncelle (operasyon adı değişmiş olabilir)
                cursor.execute(
                    "UPDATE stage_operasyonlar SET ad = ? WHERE kod = ?",
                    (ad, kod)
                )

            connection.commit()
            return jsonify({"success": True, "message": "Operasyon başarıyla eklendi"}), 201

        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()

    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

@app.route('/api/add_stage_operasyon', methods=['POST'])
def add_stage_operasyon():
    data = request.json
    if not data or 'kod' not in data or 'ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = "INSERT INTO stage_operasyonlar (kod, ad) VALUES (?, ?)"
            cursor.execute(query, (data['kod'], data['ad']))
            connection.commit()
            return jsonify({"success": True, "message": "Stage-operasyon başarıyla eklendi"}), 201
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

@app.route('/api/add_birim', methods=['POST'])
def add_birim():
    data = request.json
    if not data or 'birim' not in data or 'ucret' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = "INSERT INTO birim_ucretler (birim, ucret) VALUES (?, ?)"
            cursor.execute(query, (data['birim'], data['ucret']))
            connection.commit()
            return jsonify({"success": True, "message": "Birim başarıyla eklendi"}), 201
        except Exception as e:
            print("Veritabanı hatası:", e)
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()

    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

# Bölge Kodları
@app.route('/api/delete_bolge/<kod>', methods=['DELETE'])
def delete_bolge(kod):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM bolge_kodlari WHERE kod = ?", (kod,))
            connection.commit()
            return jsonify({"success": True, "message": "Bölge silindi"}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

@app.route('/api/update_bolge', methods=['PUT'])
def update_bolge():
    data = request.json
    if not data or 'eski_kod' not in data or 'yeni_kod' not in data or 'ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE bolge_kodlari SET kod = ?, ad = ? WHERE kod = ?",
                (data['yeni_kod'], data['ad'], data['eski_kod'])
            )
            connection.commit()
            return jsonify({"success": True, "message": "Bölge güncellendi"}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

# Kaynak Tipi
@app.route('/api/delete_kaynak_tipi/<kod>', methods=['DELETE'])
def delete_kaynak_tipi(kod):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM kaynak_tipleri WHERE kod = ?", (kod,))
            connection.commit()
            return jsonify({"success": True, "message": "Kaynak tipi silindi"}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

@app.route('/api/update_kaynak_tipi', methods=['PUT'])
def update_kaynak_tipi():
    data = request.json
    if not data or 'kod' not in data or 'yeni_kod' not in data or 'ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE kaynak_tipleri SET kod = ?, ad = ? WHERE kod = ?", (data['yeni_kod'], data['ad'], data['kod']))
            connection.commit()
            return jsonify({"success": True, "message": "Kaynak tipi güncellendi"}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

# Stage
@app.route('/api/delete_stage/<kod>', methods=['DELETE'])
def delete_stage(kod):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM stages WHERE kod = ?", (kod,))
            connection.commit()
            return jsonify({"success": True, "message": "Stage silindi"}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

@app.route('/api/update_stage', methods=['PUT'])
def update_stage():
    data = request.json
    if not data or 'kod' not in data or 'yeni_kod' not in data or 'ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE stages SET kod = ?, ad = ? WHERE kod = ?", (data['yeni_kod'], data['ad'], data['kod']))
            connection.commit()
            return jsonify({"success": True, "message": "Stage güncellendi"}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

# Operasyon
@app.route('/api/delete_operasyon/<stage_kod>/<op_kod>', methods=['DELETE'])
def delete_operasyon(stage_kod, op_kod):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM operasyonlar WHERE stage_kod = ? AND operasyon_kod = ?", (stage_kod, op_kod))
            connection.commit()
            return jsonify({"success": True, "message": "Operasyon silindi"}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

@app.route('/api/update_operasyon', methods=['PUT'])
def update_operasyon():
    data = request.json
    if not data or 'stage_kod' not in data or 'operasyon_kod' not in data or 'operasyon_ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE operasyonlar SET operasyon_ad = ? WHERE stage_kod = ? AND operasyon_kod = ?", (data['operasyon_ad'], data['stage_kod'], data['operasyon_kod']))
            connection.commit()
            return jsonify({"success": True, "message": "Operasyon güncellendi"}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

# Birim
@app.route('/api/delete_birim/<birim>', methods=['DELETE'])
def delete_birim(birim):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM birim_ucretler WHERE birim = ?", (birim,))
            connection.commit()
            return jsonify({"success": True, "message": "Birim silindi"}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

@app.route('/api/update_birim', methods=['PUT'])
def update_birim():
    data = request.json
    if not data or 'birim' not in data or 'ucret' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE birim_ucretler SET ucret = ? WHERE birim = ?", (data['ucret'], data['birim']))
            connection.commit()
            return jsonify({"success": True, "message": "Birim güncellendi"}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500


@app.route('/api/save_expense', methods=['POST'])
def save_expense():
    data = request.json
    print(f"Received save_expense request with data: {data}")  # Debug log

    if not data or 'user_id' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400

    # Tutar kontrolü ve dönüşümü
    try:
        tutar = data.get('tutar', 0)
        if isinstance(tutar, str):
            # String ise temizle ve float'a çevir
            tutar_clean = tutar.replace('₺', '').replace(',', '.').strip()
            tutar = float(tutar_clean)
        elif not isinstance(tutar, (int, float)):
            raise ValueError("Geçersiz tutar formatı")
    except (ValueError, TypeError) as e:
        print(f"Tutar dönüşüm hatası: {str(e)}")  # Debug log
        return jsonify({"success": False, "message": f"Geçersiz tutar formatı: {str(e)}"}), 400

    connection = get_db_connection()
    if not connection:
        print("Database connection failed!")  # Debug log
        return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

    try:
        cursor = connection.cursor()
        
        # Önce veriyi ekle
        insert_query = """
        INSERT INTO expenses (
            user_id, tarih, bolge_kodu, kaynak_tipi, stage, 
            stage_operasyon, no_su, kimden_alindigi, aciklama, tutar
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_query, (
            data['user_id'],
            data['tarih'],
            data['bolge_kodu'],
            data['kaynak_tipi'],
            data['stage'],
            data['stage_operasyon'],
            data['no_su'],
            data['kimden_alindigi'],
            data['aciklama'],
            tutar
        ))
        
        # SQLite için lastrowid ile son eklenen ID'yi al
        expense_id = cursor.lastrowid
        connection.commit()
        
        print(f"Successfully saved expense with ID: {expense_id}")  # Debug log
        
        # Return success response with the saved data
        return jsonify({
            'success': True, 
            'message': 'Masraf başarıyla kaydedildi.',
            'data': {
                'expense_id': expense_id,
                'expense': {
                    'tarih': data['tarih'],
                    'bolge_kodu': data['bolge_kodu'],
                    'kaynak_tipi': data['kaynak_tipi'],
                    'stage': data['stage'],
                    'stage_operasyon': data['stage_operasyon'],
                    'no_su': data['no_su'],
                    'kimden_alindigi': data['kimden_alindigi'],
                    'aciklama': data['aciklama'],
                    'tutar': tutar
                }
            }
        }), 201

    except Exception as e:
        print(f"Error saving expense: {str(e)}")  # Debug log
        connection.rollback()  # Hata durumunda değişiklikleri geri al
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()


@app.route('/api/get_expenses', methods=['GET'])
def get_expenses():
    """Masraf listeleme (kullanıcıya göre filtrelenmiş)"""
    user_id = request.args.get('user_id', type=int)
    bolge_kodu = request.args.get('bolge_kodu')
    stage_kodu = request.args.get('stage_kodu')
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

    try:
        cursor = connection.cursor()
        
        # Kullanıcı rolünü kontrol et
        role = 'normal'
        user_bolgeler = []
        if user_id:
            cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            if user_row:
                role = user_row[0] or 'normal'
                
                # Normal kullanıcı ise bölgelerini al
                if role == 'normal':
                    cursor.execute("SELECT bolge_kodu FROM user_bolgeler WHERE user_id = ?", (user_id,))
                    user_bolgeler = [row[0] for row in cursor.fetchall()]
        
        # SQL sorgusu oluştur
        query = """
        SELECT id, tarih, bolge_kodu, kaynak_tipi, stage, stage_operasyon, 
               no_su, kimden_alindigi, aciklama, tutar
        FROM expenses 
        WHERE 1=1
        """
        params = []
        
        # Normal kullanıcı ise sadece kendi bölgelerini göster
        if role == 'normal' and user_bolgeler:
            # Bölge kodlarını normalize et ve hem noktalı hem noktasız versiyonları ekle
            normalized_bolgeler = []
            for bolge in user_bolgeler:
                bolge_normalized = str(bolge).strip()
                if bolge_normalized.endswith('.'):
                    bolge_normalized = bolge_normalized[:-1]
                normalized_bolgeler.append(bolge_normalized)
                normalized_bolgeler.append(bolge_normalized + '.')
            
            if normalized_bolgeler:
                query += " AND bolge_kodu IN (" + ",".join(["?"] * len(normalized_bolgeler)) + ")"
                params.extend(normalized_bolgeler)
        
        # Bölge kodu filtresi
        if bolge_kodu:
            # Bölge kodunu normalize et (nokta varsa kaldır)
            bolge_kodu_normalized = str(bolge_kodu).strip()
            if bolge_kodu_normalized.endswith('.'):
                bolge_kodu_normalized = bolge_kodu_normalized[:-1]
            # Hem noktalı hem noktasız versiyonları kontrol et
            query += " AND (bolge_kodu = ? OR bolge_kodu = ?)"
            params.append(bolge_kodu_normalized)
            params.append(bolge_kodu_normalized + '.')
        
        # Stage filtresi
        if stage_kodu:
            query += " AND stage = ?"
            params.append(stage_kodu)
        
        query += " ORDER BY tarih DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            return jsonify({
                "success": True,
                "data": [],
                "expenses": [],
                "count": 0,
                "message": "Tabloda masraf bulunamadı"
            }), 200

        expenses = []
        for row in rows:
            # Tarih verisini işle - string veya datetime olabilir
            tarih_value = row[1]
            if tarih_value:
                if isinstance(tarih_value, str):
                    # Zaten string ise olduğu gibi kullan
                    tarih = tarih_value
                else:
                    # DateTime objesi ise formatla
                    from datetime import datetime
                    if isinstance(tarih_value, datetime):
                        tarih = tarih_value.strftime('%Y-%m-%d')
                    else:
                        # Diğer durumlar için string'e çevir
                        tarih = str(tarih_value)
            else:
                tarih = None
            
            expense = {
                'id': row[0],
                'tarih': tarih,
                'bolge_kodu': row[2],
                'kaynak_tipi': row[3],
                'stage': row[4],
                'stage_operasyon': row[5],
                'no_su': row[6],
                'kimden_alindigi': row[7],
                'aciklama': row[8],
                'tutar': float(row[9]) if row[9] is not None else 0.0
            }
            expenses.append(expense)

        return jsonify({
            "success": True,
            "data": expenses,  # bolgeGoruntuleOperations.py için
            "expenses": expenses,  # Diğer kullanımlar için
            "count": len(expenses)
        }), 200

    except Exception as e:
        print(f"Error in get_expenses: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": str(e),
            "error_details": f"Full error: {traceback.format_exc()}"
        }), 500
    finally:
        cursor.close()
        connection.close()


@app.route('/api/clear_expenses/<user_id>', methods=['DELETE'])
def clear_expenses(user_id):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
            connection.commit()
            return jsonify({"success": True, "message": "Masraflar başarıyla temizlendi"}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500

@app.route('/api/update_expense/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    """Masraf güncelleme"""
    data = request.json
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Veritabanı bağlantı hatası"}), 500

    try:
        cursor = connection.cursor()

        # Önce böyle bir masraf var mı kontrol edelim
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"success": False, "message": "Masraf bulunamadı"}), 404

        # Güncellenecek alanları belirle
        update_fields = []
        update_values = []
        
        fields = ['tarih', 'bolge_kodu', 'kaynak_tipi', 'stage', 'stage_operasyon', 
                 'no_su', 'kimden_alindigi', 'aciklama', 'tutar']
        
        for field in fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                update_values.append(data[field])
        
        if update_fields:
            update_values.append(expense_id)
            query = f"UPDATE expenses SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, update_values)
            connection.commit()
            return jsonify({"success": True, "message": "Masraf başarıyla güncellendi"})
        else:
            return jsonify({"success": False, "message": "Güncellenecek alan bulunamadı"}), 400
            
    except Exception as e:
        connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/delete_expense/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Veritabanı bağlantı hatası"}), 500

    try:
        cursor = connection.cursor()

        # Önce böyle bir masraf var mı kontrol edelim
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"success": False, "message": "Masraf bulunamadı"}), 404

        # Masrafı sil
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        connection.commit()
        return jsonify({"success": True, "message": "Masraf başarıyla silindi"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        connection.close()

@app.route('/api/get_user_id', methods=['POST'])
def get_user_id():
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Username required'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row is None:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'user_id': row[0]}), 200
    except Exception as e:
        print(f"DB error: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/get_operations_by_stage/<stage_kod>', methods=['GET'])
def get_operations_by_stage(stage_kod):
    print(f"DEBUG - Getting operations for stage: {stage_kod}")
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = "SELECT operasyon_kod, operasyon_ad FROM operasyonlar WHERE stage_kod = ?"
            print(f"DEBUG - Executing query: {query} with stage_kod: {stage_kod}")
            
            cursor.execute(query, (stage_kod,))
            rows = cursor.fetchall()
            
            if not rows:
                print(f"WARNING - No operations found for stage: {stage_kod}")
                return jsonify({"success": True, "data": {}})
            
            result = {row[0]: row[1] for row in rows}
            print(f"DEBUG - Found {len(result)} operations for stage {stage_kod}")
            return jsonify({"success": True, "data": result})
            
        except Exception as e:
            error_msg = f"Database error: {str(e)}"
            print(f"ERROR - {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 500
        finally:
            cursor.close()
            connection.close()
    
    error_msg = "Database connection failed"
    print(f"ERROR - {error_msg}")
    return jsonify({"success": False, "error": error_msg}), 500

@app.route('/api/add_bolge', methods=['POST'])
def add_bolge():
    """Yeni bölge kodu ekle"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            data = request.get_json()
            kod = data.get('kod')
            ad = data.get('ad')
            
            if not kod or not ad:
                return jsonify({"success": False, "error": "Kod ve ad alanları gerekli"}), 400
            
            # Aynı kod var mı kontrol et
            cursor.execute("SELECT COUNT(*) FROM bolge_kodlari WHERE kod = ?", (kod,))
            if cursor.fetchone()[0] > 0:
                return jsonify({"success": False, "error": "Bu kod zaten mevcut"}), 400
            
            cursor.execute("INSERT INTO bolge_kodlari (kod, ad) VALUES (?, ?)", (kod, ad))
            connection.commit()
            
            return jsonify({"success": True, "message": "Bölge kodu başarıyla eklendi"})
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    
    return jsonify({"success": False, "error": "Database connection failed"}), 500

@app.route('/api/bulk_add_bolge', methods=['POST'])
def bulk_add_bolge():
    """Toplu bölge kodu ekleme"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            data = request.get_json()
            bolge_listesi = data.get('bolge_listesi', [])
            
            if not bolge_listesi:
                return jsonify({"success": False, "error": "Bölge listesi boş"}), 400
            
            added_count = 0
            skipped_count = 0
            errors = []
            
            for bolge in bolge_listesi:
                try:
                    kod = bolge.get('kod')
                    ad = bolge.get('ad')
                    
                    if not kod or not ad:
                        errors.append(f"Kod veya ad eksik: {bolge}")
                        continue
                    
                    # Aynı kod var mı kontrol et
                    cursor.execute("SELECT COUNT(*) FROM bolge_kodlari WHERE kod = ?", (kod,))
                    if cursor.fetchone()[0] > 0:
                        skipped_count += 1
                        continue
                    
                    cursor.execute("INSERT INTO bolge_kodlari (kod, ad) VALUES (?, ?)", (kod, ad))
                    added_count += 1
                    
                except Exception as e:
                    errors.append(f"Bölge eklenirken hata ({bolge}): {str(e)}")
            
            connection.commit()
            
            result = {
                "success": True,
                "message": f"{added_count} bölge eklendi, {skipped_count} atlandı",
                "added_count": added_count,
                "skipped_count": skipped_count,
                "errors": errors
            }
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    
    return jsonify({"success": False, "error": "Database connection failed"}), 500

# ==================== HARCAMA TALEP ENDPOINT'LERİ ====================

@app.route('/api/harcama_talep', methods=['POST'])
def save_harcama_talep():
    """Harcama talep kaydetme (kullanıcıdan bağımsız)"""
    data = request.json
    print(f"DEBUG - save_harcama_talep çağrıldı, data: {data}")
    user_id = data.get('user_id')  # Hangi kullanıcı kaydetti (opsiyonel)
    
    connection = get_db_connection()
    if not connection:
        print("ERROR - Veritabanı bağlantısı başarısız")
        return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500
    
    try:
        cursor = connection.cursor()
        
        # En yüksek no değerini bul
        cursor.execute("SELECT MAX(no) FROM harcama_talep")
        max_no = cursor.fetchone()[0]
        no = (max_no or 0) + 1
        print(f"DEBUG - Yeni no değeri: {no}")
        
        # Harcama talep kaydı - SQLite için lastrowid kullan
        cursor.execute("""
            INSERT INTO harcama_talep 
            (no, tarih, bolge_kodu, kaynak_tipi_kodu, stage_kodu, stage_operasyon_kodu,
             safha, harcama_kalemi, birim, miktar, birim_ucret, toplam, aciklama, is_manuel)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            no,
            data.get('tarih'),
            data.get('bolge_kodu'),
            data.get('kaynak_tipi_kodu'),
            data.get('stage_kodu'),
            data.get('stage_operasyon_kodu'),
            data.get('safha'),
            data.get('harcama_kalemi'),
            data.get('birim'),
            data.get('miktar'),
            data.get('birim_ucret'),
            data.get('toplam'),
            data.get('aciklama'),
            data.get('is_manuel', 0)
        ))
        
        # SQLite için lastrowid ile son eklenen ID'yi al
        harcama_talep_id = cursor.lastrowid
        print(f"DEBUG - lastrowid sonucu: {harcama_talep_id}")
        
        # Commit yap
        connection.commit()
        print(f"DEBUG - Commit başarılı, harcama_talep_id: {harcama_talep_id}")
        
        # Kaydın gerçekten eklenip eklenmediğini kontrol et
        if harcama_talep_id:
            cursor.execute("SELECT COUNT(*) FROM harcama_talep WHERE id = ?", (harcama_talep_id,))
            count = cursor.fetchone()[0]
            print(f"DEBUG - Kayıt kontrolü: ID {harcama_talep_id} için {count} kayıt bulundu")
        
        print(f"DEBUG - Harcama talep kaydedildi, ID: {harcama_talep_id}")
        
        return jsonify({
            'success': True,
            'message': 'Harcama talep başarıyla kaydedildi.',
            'harcama_talep_id': harcama_talep_id
        }), 201
        
    except Exception as e:
        connection.rollback()
        print(f"ERROR - save_harcama_talep hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/harcama_talep', methods=['GET'])
def get_harcama_talep():
    """Harcama talep listeleme (kullanıcıya göre filtrelenmiş)"""
    user_id = request.args.get('user_id', type=int)
    bolge_kodu = request.args.get('bolge_kodu')
    safha = request.args.get('safha')
    stage_kodu = request.args.get('stage_kodu')
    
    print(f"DEBUG - get_harcama_talep çağrıldı, user_id: {user_id}, bolge_kodu: {bolge_kodu}, safha: {safha}, stage_kodu: {stage_kodu}")
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500
    
    try:
        cursor = connection.cursor()
        
        # Önce toplam kayıt sayısını kontrol et (debug için)
        cursor.execute("SELECT COUNT(*) FROM harcama_talep")
        total_count = cursor.fetchone()[0]
        print(f"DEBUG - Toplam harcama_talep kayıt sayısı: {total_count}")
        
        # Kullanıcı rolünü kontrol et
        role = 'normal'
        user_bolgeler = []
        if user_id:
            cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            if user_row:
                role = user_row[0] or 'normal'
                print(f"DEBUG - Kullanıcı rolü: {role}")
                
                # Normal kullanıcı ise bölgelerini al
                if role == 'normal':
                    cursor.execute("SELECT bolge_kodu FROM user_bolgeler WHERE user_id = ?", (user_id,))
                    user_bolgeler = [row[0] for row in cursor.fetchall()]
                    print(f"DEBUG - Kullanıcı bölgeleri: {user_bolgeler}")
        
        # SQL sorgusu oluştur
        query = "SELECT * FROM harcama_talep WHERE 1=1"
        params = []
        
        # Normal kullanıcı ise sadece kendi bölgelerini göster (admin ve üst düzey yönetici tümünü görür)
        if role == 'normal' and user_bolgeler:
            # Bölge kodlarını normalize et ve hem noktalı hem noktasız versiyonları ekle
            normalized_bolgeler = []
            for bolge in user_bolgeler:
                bolge_normalized = str(bolge).strip()
                if bolge_normalized.endswith('.'):
                    bolge_normalized = bolge_normalized[:-1]
                normalized_bolgeler.append(bolge_normalized)
                normalized_bolgeler.append(bolge_normalized + '.')
            
            if normalized_bolgeler:
                query += " AND bolge_kodu IN (" + ",".join(["?"] * len(normalized_bolgeler)) + ")"
                params.extend(normalized_bolgeler)
                print(f"DEBUG - Normal kullanıcı için bölge filtresi eklendi: {normalized_bolgeler}")
        
        # Filtreler
        if bolge_kodu:
            # Bölge kodunu normalize et (nokta varsa kaldır)
            bolge_kodu_normalized = str(bolge_kodu).strip()
            if bolge_kodu_normalized.endswith('.'):
                bolge_kodu_normalized = bolge_kodu_normalized[:-1]
            # Hem noktalı hem noktasız versiyonları kontrol et
            query += " AND (bolge_kodu = ? OR bolge_kodu = ?)"
            params.append(bolge_kodu_normalized)
            params.append(bolge_kodu_normalized + '.')
        
        if safha:
            query += " AND safha = ?"
            params.append(safha)
        
        if stage_kodu:
            query += " AND stage_kodu = ?"
            params.append(stage_kodu)
        
        query += " ORDER BY no, tarih"
        
        print(f"DEBUG - SQL sorgusu: {query}")
        print(f"DEBUG - SQL parametreleri: {params}")
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        print(f"DEBUG - Bulunan kayıt sayısı: {len(rows)}")
        
        # Kolon isimlerini al
        columns = [column[0] for column in cursor.description]
        
        # Sonuçları dict formatına çevir
        results = []
        for row in rows:
            result_dict = dict(zip(columns, row))
            results.append(result_dict)
        
        print(f"DEBUG - Döndürülen sonuç sayısı: {len(results)}")
        
        return jsonify({
            'success': True,
            'data': results
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/harcama_talep/<int:harcama_talep_id>', methods=['PUT'])
def update_harcama_talep(harcama_talep_id):
    """Harcama talep güncelleme (manuel değişiklikleri kaydetme)"""
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "message": "user_id gerekli"}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500
    
    try:
        cursor = connection.cursor()
        
        # Mevcut kaydı al
        cursor.execute("SELECT * FROM harcama_talep WHERE id = ?", (harcama_talep_id,))
        old_row = cursor.fetchone()
        if not old_row:
            return jsonify({"success": False, "message": "Kayıt bulunamadı"}), 404
        
        columns = [column[0] for column in cursor.description]
        old_data = dict(zip(columns, old_row))
        
        # Güncellenecek alanları belirle
        update_fields = []
        update_values = []
        
        # Manuel değişiklikleri kaydet
        for field in ['bolge_kodu', 'kaynak_tipi_kodu', 'stage_kodu', 'stage_operasyon_kodu',
                      'safha', 'harcama_kalemi', 'birim', 'miktar', 'birim_ucret', 'toplam', 'aciklama']:
            if field in data and str(data[field]) != str(old_data.get(field, '')):
                update_fields.append(f"{field} = ?")
                update_values.append(data[field])
                
                # Manuel değişiklik kaydı
                cursor.execute("""
                    INSERT INTO harcama_talep_manuel_degisiklikler
                    (harcama_talep_id, user_id, alan_adi, eski_deger, yeni_deger)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    harcama_talep_id,
                    user_id,
                    field,
                    str(old_data.get(field, '')),
                    str(data[field])
                ))
        
        # Eğer değişiklik varsa güncelle
        if update_fields:
            update_values.append(harcama_talep_id)
            # SQLite için CURRENT_TIMESTAMP kullan
            query = f"UPDATE harcama_talep SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            cursor.execute(query, update_values)
            connection.commit()
        
        return jsonify({
            'success': True,
            'message': 'Harcama talep başarıyla güncellendi.'
        }), 200
        
    except Exception as e:
        connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/harcama_talep/<int:harcama_talep_id>', methods=['DELETE'])
def delete_harcama_talep(harcama_talep_id):
    """Harcama talep silme"""
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500
    
    try:
        cursor = connection.cursor()
        
        # Manuel değişiklik kayıtlarını sil
        cursor.execute("DELETE FROM harcama_talep_manuel_degisiklikler WHERE harcama_talep_id = ?", (harcama_talep_id,))
        
        # Harcama talep kaydını sil
        cursor.execute("DELETE FROM harcama_talep WHERE id = ?", (harcama_talep_id,))
        
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': 'Harcama talep başarıyla silindi.'
        }), 200
        
    except Exception as e:
        connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/clear_harcama_talep', methods=['DELETE'])
def clear_harcama_talep():
    """Tüm harcama talep kayıtlarını silme (admin için)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500
    
    try:
        cursor = connection.cursor()
        
        # Önce manuel değişiklik kayıtlarını sil
        cursor.execute("DELETE FROM harcama_talep_manuel_degisiklikler")
        
        # Sonra tüm harcama talep kayıtlarını sil
        cursor.execute("DELETE FROM harcama_talep")
        
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tüm harcama talep kayıtları başarıyla silindi.'
        }), 200
        
    except Exception as e:
        connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/clear_all_expenses', methods=['DELETE'])
def clear_all_expenses():
    """Tüm masraf kayıtlarını silme (admin için)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500
    
    try:
        cursor = connection.cursor()
        
        # Tüm masraf kayıtlarını sil
        cursor.execute("DELETE FROM expenses")
        
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tüm masraf kayıtları başarıyla silindi.'
        }), 200
        
    except Exception as e:
        connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# ==================== KULLANICI YÖNETİM ENDPOINT'LERİ ====================

@app.route('/api/users/<username>/role', methods=['PUT'])
def update_user_role(username):
    """Kullanıcı rolünü güncelle"""
    data = request.json
    role = data.get('role')
    
    if not role or role not in ['normal', 'admin', 'ust_duzey_yonetici']:
        return jsonify({"success": False, "message": "Geçersiz rol. Rol: 'normal', 'admin' veya 'ust_duzey_yonetici' olmalı"}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500
    
    try:
        cursor = connection.cursor()
        
        # Kullanıcıyı kontrol et
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        if not user_row:
            return jsonify({"success": False, "message": "Kullanıcı bulunamadı"}), 404
        
        # Rolü güncelle
        cursor.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': f"Kullanıcı '{username}' rolü '{role}' olarak güncellendi."
        }), 200
        
    except Exception as e:
        connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def get_related_bolge_kodlari(ana_bolge_kodu):
    """Ana bölge koduna göre ilgili tüm alt bölge kodlarını döndürür"""
    # Ana bölge-alt bölge ilişkileri
    ana_bolge_alt_bolgeler = {
        '10': ['10', '12', '14', '16'],  # ADY - DOĞU -> ADY DOĞU ile başlayan tüm bölgeler
        '11': ['11', '13', '15', '17', '18'],  # ADY - BATI -> ADY BATI ile başlayan tüm bölgeler
        '20': ['20', '21', '24', '25', '22', '26', '23'],  # MAN -> MAN ile başlayan tüm bölgeler
        '30': ['30', '32', '35', '36', '33', '37', '34', '38', '39'],  # MAR -> MAR ile başlayan tüm bölgeler
    }
    
    # Ana bölge koduna göre ilgili bölgeleri döndür
    return ana_bolge_alt_bolgeler.get(ana_bolge_kodu, [ana_bolge_kodu])

@app.route('/api/users/<username>/bolge', methods=['POST'])
def add_user_bolge(username):
    """Kullanıcıya bölge kodu ekle (ana bölge eklenirse alt bölgeler de otomatik eklenir)"""
    data = request.json
    bolge_kodu = data.get('bolge_kodu')
    
    if not bolge_kodu:
        return jsonify({"success": False, "message": "Bölge kodu gerekli"}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500
    
    try:
        cursor = connection.cursor()
        
        # Kullanıcıyı kontrol et
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        if not user_row:
            return jsonify({"success": False, "message": "Kullanıcı bulunamadı"}), 404
        
        user_id = user_row[0]
        
        # Ana bölge kodları: 10, 11, 20, 30
        ana_bolge_kodlari = ['10', '11', '20', '30']
        
        # Eğer ana bölge kodu ekleniyorsa, ilgili tüm alt bölgeleri de ekle
        if bolge_kodu in ana_bolge_kodlari:
            ilgili_bolgeler = get_related_bolge_kodlari(bolge_kodu)
            eklenen_bolgeler = []
            zaten_var_olanlar = []
            
            for bolge in ilgili_bolgeler:
                # Bölge kodunun geçerli olup olmadığını kontrol et
                cursor.execute("SELECT kod FROM bolge_kodlari WHERE kod = ?", (bolge,))
                if not cursor.fetchone():
                    continue  # Geçersiz bölge kodu, atla
                
                # Bölge kodunu ekle (zaten varsa hata verme)
                try:
                    cursor.execute("INSERT INTO user_bolgeler (user_id, bolge_kodu) VALUES (?, ?)", 
                                  (user_id, bolge))
                    eklenen_bolgeler.append(bolge)
                except Exception as e:
                    if 'UNIQUE constraint' in str(e):
                        zaten_var_olanlar.append(bolge)
                    else:
                        raise
            
            connection.commit()
            
            mesaj = f"Ana bölge '{bolge_kodu}' ve ilgili {len(eklenen_bolgeler)} alt bölge kullanıcı '{username}' için eklendi."
            if zaten_var_olanlar:
                mesaj += f" ({len(zaten_var_olanlar)} bölge zaten mevcuttu)"
            
            return jsonify({
                'success': True,
                'message': mesaj,
                'eklenen_bolgeler': eklenen_bolgeler,
                'zaten_var_olanlar': zaten_var_olanlar
            }), 200
        else:
            # Alt bölge kodu ekleniyorsa, sadece o bölgeyi ekle
            cursor.execute("SELECT kod FROM bolge_kodlari WHERE kod = ?", (bolge_kodu,))
            if not cursor.fetchone():
                return jsonify({"success": False, "message": "Geçersiz bölge kodu"}), 400
            
            try:
                cursor.execute("INSERT INTO user_bolgeler (user_id, bolge_kodu) VALUES (?, ?)", 
                              (user_id, bolge_kodu))
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': f"Bölge kodu '{bolge_kodu}' kullanıcı '{username}' için eklendi."
                }), 200
            except Exception as e:
                if 'UNIQUE constraint' in str(e):
                    return jsonify({"success": False, "message": "Bu bölge kodu zaten eklenmiş"}), 409
                raise
        
    except Exception as e:
        connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/users/<username>/bolge/<bolge_kodu>', methods=['DELETE'])
def remove_user_bolge(username, bolge_kodu):
    """Kullanıcıdan bölge kodu kaldır"""
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500
    
    try:
        cursor = connection.cursor()
        
        # Kullanıcıyı kontrol et
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        if not user_row:
            return jsonify({"success": False, "message": "Kullanıcı bulunamadı"}), 404
        
        user_id = user_row[0]
        
        # Bölge kodunu kaldır
        cursor.execute("DELETE FROM user_bolgeler WHERE user_id = ? AND bolge_kodu = ?", 
                      (user_id, bolge_kodu))
        connection.commit()
        
        if cursor.rowcount > 0:
            return jsonify({
                'success': True,
                'message': f"Bölge kodu '{bolge_kodu}' kullanıcı '{username}' için kaldırıldı."
            }), 200
        else:
            return jsonify({"success": False, "message": "Bölge kodu bulunamadı"}), 404
        
    except Exception as e:
        connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/users/<username>', methods=['GET'])
def get_user_info(username):
    """Kullanıcı bilgilerini getir"""
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500
    
    try:
        cursor = connection.cursor()
        
        # Kullanıcı bilgilerini al
        cursor.execute("SELECT id, username, role, default_bolge_kodu FROM users WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        if not user_row:
            return jsonify({"success": False, "message": "Kullanıcı bulunamadı"}), 404
        
        user_id, username, role, default_bolge_kodu = user_row
        
        # Bölge kodlarını al
        cursor.execute("SELECT bolge_kodu FROM user_bolgeler WHERE user_id = ?", (user_id,))
        bolge_rows = cursor.fetchall()
        bolge_kodlari = [row[0] for row in bolge_rows]
        
        return jsonify({
            'success': True,
            'username': username,
            'role': role or 'normal',
            'default_bolge_kodu': default_bolge_kodu,
            'bolge_kodlari': bolge_kodlari
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/api/users', methods=['GET'])
def list_all_users():
    """Tüm kullanıcıları listele"""
    connection = get_db_connection()
    if not connection:
        return jsonify({"success": False, "message": "Veritabanı bağlantısı başarısız"}), 500
    
    try:
        cursor = connection.cursor()
        
        # Tüm kullanıcıları al (kolonlar yoksa güvenli SELECT)
        try:
            cursor.execute("SELECT id, username, role, default_bolge_kodu FROM users")
            users_rows = cursor.fetchall()
        except:
            # Kolonlar yoksa eski SELECT
            cursor.execute("SELECT id, username FROM users")
            users_rows = cursor.fetchall()
        
        users = []
        for row in users_rows:
            if len(row) == 4:
                user_id, username, role, default_bolge_kodu = row
            else:
                user_id, username = row
                role = 'normal'
                default_bolge_kodu = None
            
            # Her kullanıcının bölge kodlarını al
            try:
                cursor.execute("SELECT bolge_kodu FROM user_bolgeler WHERE user_id = ?", (user_id,))
                bolge_rows = cursor.fetchall()
                bolge_kodlari = [row[0] for row in bolge_rows]
            except:
                bolge_kodlari = []
            
            users.append({
                'username': username,
                'role': role or 'normal',
                'default_bolge_kodu': default_bolge_kodu,
                'bolge_kodlari': bolge_kodlari
            })
        
        return jsonify({
            'success': True,
            'data': users  # 'users' yerine 'data' kullanıyoruz (GUI ile uyumlu)
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    # Uygulama başlarken migration'ı çalıştır
    print("🔄 Veritabanı migration kontrolü yapılıyor...")
    try:
        migrate_db()
        print("✅ Migration kontrolü tamamlandı!")
    except Exception as e:
        print(f"❌ Migration hatası: {e}")
        import traceback
        traceback.print_exc()
        # Hata olsa bile devam et
    
    # Admin kullanıcısını oluştur (yoksa)
    print("🔄 Admin kullanıcısı kontrol ediliyor...")
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Admin kullanıcısı var mı kontrol et
            admin_username = get_admin_username()
            cursor.execute("SELECT id FROM users WHERE username = ?", (admin_username,))
            admin_exists = cursor.fetchone()

            if not admin_exists:
                pwd = get_admin_initial_password()
                generated = False
                if not pwd:
                    if is_production():
                        print(
                            "UYARI: ADMIN_INITIAL_PASSWORD tanimlanmadi; ilk admin kullanicisi olusturulmadi."
                        )
                    else:
                        import secrets

                        pwd = secrets.token_urlsafe(12)
                        generated = True
                        print(
                            f"GELISTIRME: Ilk admin '{admin_username}' sifresi (kaydedin): {pwd}"
                        )
                if pwd:
                    password_hash_admin = generate_password_hash(pwd)
                    cursor.execute(
                        """
                        INSERT INTO users (username, password_hash, role)
                        VALUES (?, ?, 'admin')
                        """,
                        (admin_username, password_hash_admin),
                    )
                    conn.commit()
                    if not generated:
                        print(f"✅ Admin kullanıcısı oluşturuldu: {admin_username}")
            else:
                print("✅ Admin kullanıcısı zaten mevcut")
        except Exception as e:
            print(f"❌ Admin kullanıcısı oluşturulurken hata: {e}")
            import traceback
            traceback.print_exc()
        finally:
            cursor.close()
            conn.close()
    
    print("🚀 Flask sunucusu başlatılıyor...")
    print(f"📁 SQLite veritabanı: {DATABASE_PATH}")
    app.run(debug=False, host=get_flask_host(), port=get_flask_port())
