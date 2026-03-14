"""
SQL Server'dan SQLite'a veri migration script'i
Bu script mevcut SQL Server veritabanındaki tüm verileri SQLite'a aktarır.
"""
import sqlite3
import pyodbc
import os
from werkzeug.security import generate_password_hash

# SQL Server bağlantı bilgileri (eski)
SERVER_NAME = r'DESKTOP-GVRQ3CP'
DATABASE_NAME = r'harcama_masraf_db'
DRIVER_NAME = r'ODBC Driver 11 for SQL Server'

connection_string_sqlserver = (
    f'DRIVER={{{DRIVER_NAME}}};'
    f'SERVER={SERVER_NAME};'
    f'DATABASE={DATABASE_NAME};'
    f'Trusted_Connection=yes;'
    f'TrustServerCertificate=yes;'
    f'Encrypt=no;'
)

# SQLite veritabanı yolu
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'harcama_masraf.db')

def get_sqlserver_connection():
    """SQL Server bağlantısı"""
    try:
        conn = pyodbc.connect(connection_string_sqlserver)
        return conn
    except Exception as e:
        print(f"SQL Server bağlantı hatası: {e}")
        return None

def get_sqlite_connection():
    """SQLite bağlantısı"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"SQLite bağlantı hatası: {e}")
        return None

def migrate_users():
    """Kullanıcıları migrate et"""
    sqlserver_conn = get_sqlserver_connection()
    sqlite_conn = get_sqlite_connection()
    
    if not sqlserver_conn or not sqlite_conn:
        print("❌ Bağlantı hatası!")
        return
    
    try:
        sqlserver_cursor = sqlserver_conn.cursor()
        sqlite_cursor = sqlite_conn.cursor()
        
        # SQL Server'dan kullanıcıları al
        sqlserver_cursor.execute("SELECT id, username, password_hash, role, default_bolge_kodu FROM users")
        users = sqlserver_cursor.fetchall()
        
        print(f"📦 {len(users)} kullanıcı bulundu...")
        
        for user in users:
            user_id, username, password_hash, role, default_bolge_kodu = user
            # SQLite'a ekle
            sqlite_cursor.execute("""
                INSERT OR REPLACE INTO users (id, username, password_hash, role, default_bolge_kodu)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, password_hash, role or 'normal', default_bolge_kodu))
        
        sqlite_conn.commit()
        print(f"✅ {len(users)} kullanıcı migrate edildi!")
        
    except Exception as e:
        print(f"❌ Kullanıcı migration hatası: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sqlserver_cursor.close()
        sqlite_cursor.close()
        sqlserver_conn.close()
        sqlite_conn.close()

def migrate_user_bolgeler():
    """Kullanıcı-bölge ilişkilerini migrate et"""
    sqlserver_conn = get_sqlserver_connection()
    sqlite_conn = get_sqlite_connection()
    
    if not sqlserver_conn or not sqlite_conn:
        return
    
    try:
        sqlserver_cursor = sqlserver_conn.cursor()
        sqlite_cursor = sqlite_conn.cursor()
        
        sqlserver_cursor.execute("SELECT user_id, bolge_kodu FROM user_bolgeler")
        user_bolgeler = sqlserver_cursor.fetchall()
        
        print(f"📦 {len(user_bolgeler)} kullanıcı-bölge ilişkisi bulundu...")
        
        for ub in user_bolgeler:
            user_id, bolge_kodu = ub
            sqlite_cursor.execute("""
                INSERT OR IGNORE INTO user_bolgeler (user_id, bolge_kodu)
                VALUES (?, ?)
            """, (user_id, bolge_kodu))
        
        sqlite_conn.commit()
        print(f"✅ {len(user_bolgeler)} kullanıcı-bölge ilişkisi migrate edildi!")
        
    except Exception as e:
        print(f"❌ Kullanıcı-bölge migration hatası: {e}")
    finally:
        sqlserver_cursor.close()
        sqlite_cursor.close()
        sqlserver_conn.close()
        sqlite_conn.close()

def migrate_table(table_name, columns, id_column='id', where_clause=''):
    """Genel tablo migration fonksiyonu"""
    sqlserver_conn = get_sqlserver_connection()
    sqlite_conn = get_sqlite_connection()
    
    if not sqlserver_conn or not sqlite_conn:
        return
    
    try:
        sqlserver_cursor = sqlserver_conn.cursor()
        sqlite_cursor = sqlite_conn.cursor()
        
        # SQL Server'dan verileri al
        columns_str = ', '.join(columns)
        query = f"SELECT {columns_str} FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        sqlserver_cursor.execute(query)
        rows = sqlserver_cursor.fetchall()
        
        print(f"📦 {len(rows)} {table_name} kaydı bulundu...")
        
        if len(rows) == 0:
            print(f"⚠️ {table_name} tablosunda veri yok, atlanıyor...")
            return
        
        # SQLite'a ekle
        placeholders = ', '.join(['?' for _ in columns])
        columns_str_insert = ', '.join(columns)
        
        count = 0
        for row in rows:
            try:
                # Row'u tuple'a çevir
                row_data = tuple(row)
                sqlite_cursor.execute(f"""
                    INSERT OR REPLACE INTO {table_name} ({columns_str_insert})
                    VALUES ({placeholders})
                """, row_data)
                count += 1
            except Exception as row_error:
                print(f"⚠️ Satır hatası ({table_name}): {row_error}")
                continue
        
        sqlite_conn.commit()
        print(f"✅ {count}/{len(rows)} {table_name} kaydı migrate edildi!")
        
    except Exception as e:
        print(f"❌ {table_name} migration hatası: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sqlserver_cursor.close()
        sqlite_cursor.close()
        sqlserver_conn.close()
        sqlite_conn.close()

def migrate_all():
    """Tüm verileri migrate et"""
    print("🚀 Veri migration başlatılıyor...")
    print("=" * 50)
    
    # Önce tabloları oluştur (RestApi.py'deki migrate_db fonksiyonunu çalıştır)
    from RestApi import migrate_db
    print("📋 Tablolar oluşturuluyor...")
    migrate_db()
    print()
    
    # Kullanıcıları migrate et
    print("👥 Kullanıcılar migrate ediliyor...")
    migrate_users()
    print()
    
    # Kullanıcı-bölge ilişkilerini migrate et
    print("🔗 Kullanıcı-bölge ilişkileri migrate ediliyor...")
    migrate_user_bolgeler()
    print()
    
    # Diğer tabloları migrate et
    tables_to_migrate = [
        ('bolge_kodlari', ['kod', 'ad']),
        ('kaynak_tipleri', ['kod', 'ad']),
        ('stages', ['kod', 'ad']),
        ('operasyonlar', ['id', 'stage_kod', 'operasyon_kod', 'operasyon_ad']),
        ('stage_operasyonlar', ['kod', 'ad']),
        ('birim_ucretler', ['id', 'birim', 'ucret']),
    ]
    
    for table_name, columns in tables_to_migrate:
        print(f"📊 {table_name} migrate ediliyor...")
        try:
            migrate_table(table_name, columns)
        except Exception as e:
            print(f"⚠️ {table_name} migration atlandı: {e}")
        print()
    
    # Harcama ve masraf tabloları (opsiyonel - büyük olabilir)
    print("📊 harcama_talep migrate ediliyor...")
    try:
        migrate_table('harcama_talep', 
                     ['id', 'no', 'tarih', 'bolge_kodu', 'kaynak_tipi_kodu', 
                      'stage_kodu', 'stage_operasyon_kodu', 'safha', 'harcama_kalemi',
                      'birim', 'miktar', 'birim_ucret', 'toplam', 'aciklama', 
                      'is_manuel', 'user_id', 'created_at', 'updated_at'])
    except Exception as e:
        print(f"⚠️ harcama_talep migration atlandı: {e}")
    print()
    
    print("📊 expenses migrate ediliyor...")
    try:
        migrate_table('expenses', 
                     ['id', 'user_id', 'tarih', 'bolge_kodu', 'kaynak_tipi', 
                      'stage', 'stage_operasyon', 'no_su', 'kimden_alindigi', 
                      'aciklama', 'tutar', 'created_at'])
    except Exception as e:
        print(f"⚠️ expenses migration atlandı: {e}")
    print()
    
    print("📊 masraf migrate ediliyor...")
    try:
        migrate_table('masraf', 
                     ['id', 'tarih', 'bolge_kodu', 'kaynak_tipi_kodu', 'stage_kodu',
                      'stage_operasyon_kodu', 'no', 'kimden_alindi', 'aciklama', 
                      'tutar', 'user_id', 'created_at', 'updated_at'])
    except Exception as e:
        print(f"⚠️ masraf migration atlandı: {e}")
    print()
    
    print("=" * 50)
    print("✅ Veri migration tamamlandı!")
    print(f"📁 SQLite veritabanı: {DATABASE_PATH}")

if __name__ == '__main__':
    migrate_all()

