import os
from config import (
    get_admin_initial_password,
    get_admin_username,
    get_database_path,
    get_flask_host,
    get_flask_port,
    get_flask_secret_key,
    get_jwt_expiration_seconds,
    is_production,
)
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from datetime import datetime

from api_error_handlers import register_global_error_handlers
from backend_logging import configure_backend_logging
from jwt_auth import issue_access_token, register_jwt_middleware
from db.init_database import migrate_db
from db.session import (
    close_flask_session,
    flask_transaction,
    get_flask_session,
    session_scope,
)
from repositories import CatalogRepository, ExpenseRepository, HarcamaRepository, UserRepository

app = Flask(__name__)
app.secret_key = get_flask_secret_key()
CORS(app)  # Enable CORS for all routes
configure_backend_logging(app)
register_global_error_handlers(app)
register_jwt_middleware(app)

# Veritabanı yolu: config.py + ortam degiskeni (DATABASE_PATH / SQLITE_PATH)
DATABASE_PATH = get_database_path()


@app.teardown_appcontext
def _teardown_sqlalchemy_session(exc):
    close_flask_session()


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

    try:
        with flask_transaction() as sess:
            users = UserRepository(sess)
            admin_u = users.get_by_username(admin_username)
            if not admin_u:
                return jsonify({'error': 'Admin user not found'}), 403
            if not check_password_hash(admin_u.password_hash, admin_password):
                return jsonify({'error': 'Invalid admin credentials'}), 403
            if admin_u.role != 'admin':
                return jsonify({'error': 'Only admin users can register new users'}), 403
            if users.username_exists(username):
                return jsonify({'error': 'Username already exists'}), 409
            users.create(username, generate_password_hash(password), 'normal')
            return jsonify({'message': 'Kullanıcı Başarıyla Kayıt Edildi'}), 201
    except Exception as e:
        print(f"DB error: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    migrate_db()

    # Ilk admin olusturma hemen commit edilir; sonraki adimlarda hata olursa admin kalir (onceki davranis).
    sess = get_flask_session()
    try:
        users = UserRepository(sess)
        admin_name = get_admin_username()
        if not users.get_by_username(admin_name):
            bootstrap_pw = get_admin_initial_password() or 'admin123'
            users.create(admin_name, generate_password_hash(bootstrap_pw), 'admin')
            sess.commit()
            print(f"✅ Admin kullanıcısı oluşturuldu (kullanıcı adı: {admin_name})")

        u = users.get_by_username(username)
        if not u or not check_password_hash(u.password_hash, password):
            print(f"DEBUG - Şifre kontrolü başarısız. Kullanıcı: {username}")
            return jsonify({'error': 'Invalid username or password'}), 401

        user_id = u.id
        role = u.role or 'normal'
        default_bolge_kodu = u.default_bolge_kodu
        bolge_kodlari = users.list_bolge_kodlari(user_id)
        if not bolge_kodlari and default_bolge_kodu:
            bolge_kodlari = [default_bolge_kodu]

        access_token = issue_access_token(user_id, username, role)
        exp_sec = get_jwt_expiration_seconds()
        return jsonify({
            'message': 'Giriş Başarılı',
            'user_id': user_id,
            'username': username,
            'role': role,
            'bolge_kodlari': bolge_kodlari,
            'default_bolge_kodu': default_bolge_kodu,
            'token': access_token,
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': exp_sec,
        }), 200
    except Exception as e:
        sess.rollback()
        print(f"DB error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/bolge_kodlari', methods=['GET'])
def get_bolge_kodlari():
    """Tüm bölge kodlarını döndürür (admin ve üst düzey yönetici için)"""
    user_id = request.args.get('user_id', type=int)
    try:
        sess = get_flask_session()
        cat = CatalogRepository(sess)
        users = UserRepository(sess)
        if user_id:
            role = users.get_role(user_id) or 'normal'
            if role in ('admin', 'ust_duzey_yonetici'):
                return jsonify(cat.bolge_dict_all())
            return jsonify(cat.bolge_dict_for_user_regions(user_id))
        return jsonify(cat.bolge_dict_all())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/kaynak_tipleri', methods=['GET'])
def get_kaynak_tipleri():
    try:
        sess = get_flask_session()
        return jsonify(CatalogRepository(sess).kaynak_tipleri_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stages', methods=['GET'])
def get_stages():
    try:
        sess = get_flask_session()
        return jsonify(CatalogRepository(sess).stages_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/operasyonlar', methods=['GET'])
def get_operasyonlar():
    try:
        sess = get_flask_session()
        return jsonify(CatalogRepository(sess).operasyonlar_nested())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stage_operasyonlar', methods=['GET'])
def get_stage_operasyonlar():
    try:
        sess = get_flask_session()
        return jsonify(CatalogRepository(sess).stage_operasyonlar_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/birim_ucretler', methods=['GET'])
def get_birim_ucretler():
    try:
        sess = get_flask_session()
        data = CatalogRepository(sess).birim_ucretler_list()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/all_data', methods=['GET'])
def get_all_data():
    """Get all data needed for the application in one request"""
    try:
        sess = get_flask_session()
        result = CatalogRepository(sess).all_reference_payload()
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/add_kaynak_tipi', methods=['POST'])
def add_kaynak_tipi():
    data = request.json
    if not data or 'kod' not in data or 'ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400
    try:
        with flask_transaction() as sess:
            CatalogRepository(sess).add_kaynak_tipi(data['kod'], data['ad'])
            return jsonify({"success": True, "message": "Kaynak tipi başarıyla eklendi"}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/add_stage', methods=['POST'])
def add_stage():
    data = request.json
    if not data or 'kod' not in data or 'ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400
    try:
        with flask_transaction() as sess:
            CatalogRepository(sess).add_stage(data['kod'], data['ad'])
            return jsonify({"success": True, "message": "Stage başarıyla eklendi"}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/add_operasyon', methods=['POST'])
def add_operasyon():
    data = request.json
    if not data or 'stage_kod' not in data or 'operasyon_kod' not in data or 'operasyon_ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400

    stage_kod = data['stage_kod']
    operasyon_kod = data['operasyon_kod']
    operasyon_ad = data['operasyon_ad']

    try:
        with flask_transaction() as sess:
            cat = CatalogRepository(sess)
            stage_ad = cat.get_stage_ad(stage_kod)
            if not stage_ad:
                return jsonify({
                    "success": False,
                    "message": f"'{stage_kod}' kodlu stage DB'de bulunamadı. Lütfen önce stage kodları tablosundan bu stage'i ekleyin.",
                    "redirect": "stages_tab"
                }), 201

            existing_ad = cat.find_operasyon(stage_kod, operasyon_kod)
            if existing_ad:
                return jsonify({
                    "success": False,
                    "message": f"Bu operasyon zaten mevcut: Stage {stage_kod}, Operasyon {operasyon_kod}. Mevcut ad: {existing_ad}"
                }), 400

            kombine_kod = f"{stage_kod}{operasyon_kod}"
            kombine_ad = f"{stage_ad}_{operasyon_ad}"
            cat.add_operasyon_pair(stage_kod, operasyon_kod, operasyon_ad, kombine_kod, kombine_ad)
            return jsonify({"success": True, "message": "Operasyon başarıyla eklendi"}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/add_stage_operasyon', methods=['POST'])
def add_stage_operasyon():
    data = request.json
    if not data or 'kod' not in data or 'ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400
    try:
        with flask_transaction() as sess:
            CatalogRepository(sess).add_stage_operasyon_row(data['kod'], data['ad'])
            return jsonify({"success": True, "message": "Stage-operasyon başarıyla eklendi"}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/add_birim', methods=['POST'])
def add_birim():
    data = request.json
    if not data or 'birim' not in data or 'ucret' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400

    try:
        with flask_transaction() as sess:
            CatalogRepository(sess).add_birim(data['birim'], float(data['ucret']))
            return jsonify({"success": True, "message": "Birim başarıyla eklendi"}), 201
    except Exception as e:
        print("Veritabanı hatası:", e)
        return jsonify({"success": False, "message": str(e)}), 500

# Bölge Kodları
@app.route('/api/delete_bolge/<kod>', methods=['DELETE'])
def delete_bolge(kod):
    try:
        with flask_transaction() as sess:
            CatalogRepository(sess).delete_bolge(kod)
            return jsonify({"success": True, "message": "Bölge silindi"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/update_bolge', methods=['PUT'])
def update_bolge():
    data = request.json
    if not data or 'eski_kod' not in data or 'yeni_kod' not in data or 'ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400

    try:
        with flask_transaction() as sess:
            CatalogRepository(sess).update_bolge_kod(data['eski_kod'], data['yeni_kod'], data['ad'])
            return jsonify({"success": True, "message": "Bölge güncellendi"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Kaynak Tipi
@app.route('/api/delete_kaynak_tipi/<kod>', methods=['DELETE'])
def delete_kaynak_tipi(kod):
    try:
        with flask_transaction() as sess:
            CatalogRepository(sess).delete_kaynak_tipi(kod)
            return jsonify({"success": True, "message": "Kaynak tipi silindi"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/update_kaynak_tipi', methods=['PUT'])
def update_kaynak_tipi():
    data = request.json
    if not data or 'kod' not in data or 'yeni_kod' not in data or 'ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400
    try:
        with flask_transaction() as sess:
            CatalogRepository(sess).update_kaynak_tipi_kod(data['kod'], data['yeni_kod'], data['ad'])
            return jsonify({"success": True, "message": "Kaynak tipi güncellendi"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Stage
@app.route('/api/delete_stage/<kod>', methods=['DELETE'])
def delete_stage(kod):
    try:
        with flask_transaction() as sess:
            CatalogRepository(sess).delete_stage(kod)
            return jsonify({"success": True, "message": "Stage silindi"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/update_stage', methods=['PUT'])
def update_stage():
    data = request.json
    if not data or 'kod' not in data or 'yeni_kod' not in data or 'ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400
    try:
        with flask_transaction() as sess:
            CatalogRepository(sess).update_stage_kod(data['kod'], data['yeni_kod'], data['ad'])
            return jsonify({"success": True, "message": "Stage güncellendi"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Operasyon
@app.route('/api/delete_operasyon/<stage_kod>/<op_kod>', methods=['DELETE'])
def delete_operasyon(stage_kod, op_kod):
    try:
        with flask_transaction() as sess:
            CatalogRepository(sess).delete_operasyon(stage_kod, op_kod)
            return jsonify({"success": True, "message": "Operasyon silindi"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/update_operasyon', methods=['PUT'])
def update_operasyon():
    data = request.json
    if not data or 'stage_kod' not in data or 'operasyon_kod' not in data or 'operasyon_ad' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400
    try:
        with flask_transaction() as sess:
            CatalogRepository(sess).update_operasyon_ad(
                data['stage_kod'], data['operasyon_kod'], data['operasyon_ad']
            )
            return jsonify({"success": True, "message": "Operasyon güncellendi"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Birim
@app.route('/api/delete_birim/<birim>', methods=['DELETE'])
def delete_birim(birim):
    try:
        with flask_transaction() as sess:
            CatalogRepository(sess).delete_birim_by_name(birim)
            return jsonify({"success": True, "message": "Birim silindi"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/update_birim', methods=['PUT'])
def update_birim():
    data = request.json
    if not data or 'birim' not in data or 'ucret' not in data:
        return jsonify({"success": False, "message": "Geçersiz istek verisi"}), 400
    try:
        with flask_transaction() as sess:
            CatalogRepository(sess).update_birim_ucret(data['birim'], float(data['ucret']))
            return jsonify({"success": True, "message": "Birim güncellendi"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


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

    try:
        with flask_transaction() as sess:
            er = ExpenseRepository(sess)
            expense_id = er.save(
                user_id=data['user_id'],
                tarih=data['tarih'],
                bolge_kodu=data.get('bolge_kodu'),
                kaynak_tipi=data.get('kaynak_tipi'),
                stage=data.get('stage'),
                stage_operasyon=data.get('stage_operasyon'),
                no_su=data.get('no_su'),
                kimden_alindigi=data.get('kimden_alindigi'),
                aciklama=data.get('aciklama'),
                tutar=tutar,
            )
            print(f"Successfully saved expense with ID: {expense_id}")  # Debug log
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
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/get_expenses', methods=['GET'])
def get_expenses():
    """Masraf listeleme (kullanıcıya göre filtrelenmiş)"""
    user_id = request.args.get('user_id', type=int)
    bolge_kodu = request.args.get('bolge_kodu')
    stage_kodu = request.args.get('stage_kodu')

    try:
        sess = get_flask_session()
        expenses = ExpenseRepository(sess).list_filtered(user_id, bolge_kodu, stage_kodu)
        if not expenses:
            return jsonify({
                "success": True,
                "data": [],
                "expenses": [],
                "count": 0,
                "message": "Tabloda masraf bulunamadı"
            }), 200
        return jsonify({
            "success": True,
            "data": expenses,
            "expenses": expenses,
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


@app.route('/api/clear_expenses/<user_id>', methods=['DELETE'])
def clear_expenses(user_id):
    try:
        with flask_transaction() as sess:
            ExpenseRepository(sess).clear_for_user(int(user_id))
            return jsonify({"success": True, "message": "Masraflar başarıyla temizlendi"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/update_expense/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    """Masraf güncelleme"""
    data = request.json or {}

    try:
        with flask_transaction() as sess:
            er = ExpenseRepository(sess)
            if er.get_by_id(expense_id) is None:
                return jsonify({"success": False, "message": "Masraf bulunamadı"}), 404
            if not any(k in data for k in (
                'tarih', 'bolge_kodu', 'kaynak_tipi', 'stage', 'stage_operasyon',
                'no_su', 'kimden_alindigi', 'aciklama', 'tutar'
            )):
                return jsonify({"success": False, "message": "Güncellenecek alan bulunamadı"}), 400
            er.update_whitelisted(expense_id, data)
            return jsonify({"success": True, "message": "Masraf başarıyla güncellendi"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/delete_expense/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    try:
        with flask_transaction() as sess:
            ok = ExpenseRepository(sess).delete_by_id(expense_id)
            if not ok:
                return jsonify({"success": False, "message": "Masraf bulunamadı"}), 404
            return jsonify({"success": True, "message": "Masraf başarıyla silindi"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/get_user_id', methods=['POST'])
def get_user_id():
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Username required'}), 400

    try:
        sess = get_flask_session()
        uid = UserRepository(sess).get_id_by_username(username)
        if uid is None:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'user_id': uid}), 200
    except Exception as e:
        print(f"DB error: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/get_operations_by_stage/<stage_kod>', methods=['GET'])
def get_operations_by_stage(stage_kod):
    print(f"DEBUG - Getting operations for stage: {stage_kod}")
    try:
        sess = get_flask_session()
        result = CatalogRepository(sess).operasyonlar_for_stage(stage_kod)
        if not result:
            print(f"WARNING - No operations found for stage: {stage_kod}")
            return jsonify({"success": True, "data": {}})
        print(f"DEBUG - Found {len(result)} operations for stage {stage_kod}")
        return jsonify({"success": True, "data": result})
    except Exception as e:
        error_msg = f"Database error: {str(e)}"
        print(f"ERROR - {error_msg}")
        return jsonify({"success": False, "error": error_msg}), 500

@app.route('/api/add_bolge', methods=['POST'])
def add_bolge():
    """Yeni bölge kodu ekle"""
    data = request.get_json()
    kod = data.get('kod')
    ad = data.get('ad')
    if not kod or not ad:
        return jsonify({"success": False, "error": "Kod ve ad alanları gerekli"}), 400
    try:
        with flask_transaction() as sess:
            cat = CatalogRepository(sess)
            if cat.bolge_exists(kod):
                return jsonify({"success": False, "error": "Bu kod zaten mevcut"}), 400
            cat.add_bolge(kod, ad)
            return jsonify({"success": True, "message": "Bölge kodu başarıyla eklendi"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/bulk_add_bolge', methods=['POST'])
def bulk_add_bolge():
    """Toplu bölge kodu ekleme"""
    data = request.get_json()
    bolge_listesi = data.get('bolge_listesi', [])
    if not bolge_listesi:
        return jsonify({"success": False, "error": "Bölge listesi boş"}), 400

    try:
        with flask_transaction() as sess:
            cat = CatalogRepository(sess)
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
                    if cat.bolge_exists(kod):
                        skipped_count += 1
                        continue
                    cat.add_bolge(kod, ad)
                    added_count += 1
                except Exception as e:
                    errors.append(f"Bölge eklenirken hata ({bolge}): {str(e)}")
            return jsonify({
                "success": True,
                "message": f"{added_count} bölge eklendi, {skipped_count} atlandı",
                "added_count": added_count,
                "skipped_count": skipped_count,
                "errors": errors
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== HARCAMA TALEP ENDPOINT'LERİ ====================

@app.route('/api/harcama_talep', methods=['POST'])
def save_harcama_talep():
    """Harcama talep kaydetme (kullanıcıdan bağımsız)"""
    data = request.json or {}
    print(f"DEBUG - save_harcama_talep çağrıldı, data: {data}")

    try:
        with flask_transaction() as sess:
            hr = HarcamaRepository(sess)
            print(f"DEBUG - Yeni no değeri: {hr.next_no()}")
            harcama_talep_id = hr.save_from_payload(data)
            print(f"DEBUG - Commit başarılı, harcama_talep_id: {harcama_talep_id}")
            print(f"DEBUG - Harcama talep kaydedildi, ID: {harcama_talep_id}")
            return jsonify({
                'success': True,
                'message': 'Harcama talep başarıyla kaydedildi.',
                'harcama_talep_id': harcama_talep_id
            }), 201
    except Exception as e:
        print(f"ERROR - save_harcama_talep hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/harcama_talep', methods=['GET'])
def get_harcama_talep():
    """Harcama talep listeleme (kullanıcıya göre filtrelenmiş)"""
    user_id = request.args.get('user_id', type=int)
    bolge_kodu = request.args.get('bolge_kodu')
    safha = request.args.get('safha')
    stage_kodu = request.args.get('stage_kodu')

    print(f"DEBUG - get_harcama_talep çağrıldı, user_id: {user_id}, bolge_kodu: {bolge_kodu}, safha: {safha}, stage_kodu: {stage_kodu}")

    try:
        sess = get_flask_session()
        hr = HarcamaRepository(sess)
        print(f"DEBUG - Toplam harcama_talep kayıt sayısı: {hr.count_all()}")
        results = hr.list_filtered(user_id, bolge_kodu, safha, stage_kodu)
        print(f"DEBUG - Bulunan kayıt sayısı: {len(results)}")
        return jsonify({'success': True, 'data': results}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/harcama_talep/<int:harcama_talep_id>', methods=['PUT'])
def update_harcama_talep(harcama_talep_id):
    """Harcama talep güncelleme (manuel değişiklikleri kaydetme)"""
    data = request.json or {}
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"success": False, "message": "user_id gerekli"}), 400

    try:
        with flask_transaction() as sess:
            hr = HarcamaRepository(sess)
            if hr.get_by_id(harcama_talep_id) is None:
                return jsonify({"success": False, "message": "Kayıt bulunamadı"}), 404
            hr.update_with_audit(harcama_talep_id, int(user_id), data)
            return jsonify({
                'success': True,
                'message': 'Harcama talep başarıyla güncellendi.'
            }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/harcama_talep/<int:harcama_talep_id>', methods=['DELETE'])
def delete_harcama_talep(harcama_talep_id):
    """Harcama talep silme"""
    try:
        with flask_transaction() as sess:
            HarcamaRepository(sess).delete_by_id(harcama_talep_id)
            return jsonify({
                'success': True,
                'message': 'Harcama talep başarıyla silindi.'
            }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/clear_harcama_talep', methods=['DELETE'])
def clear_harcama_talep():
    """Tüm harcama talep kayıtlarını silme (admin için)"""
    try:
        with flask_transaction() as sess:
            HarcamaRepository(sess).clear_all()
            return jsonify({
                'success': True,
                'message': 'Tüm harcama talep kayıtları başarıyla silindi.'
            }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/clear_all_expenses', methods=['DELETE'])
def clear_all_expenses():
    """Tüm masraf kayıtlarını silme (admin için)"""
    try:
        with flask_transaction() as sess:
            ExpenseRepository(sess).clear_all()
            return jsonify({
                'success': True,
                'message': 'Tüm masraf kayıtları başarıyla silindi.'
            }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== KULLANICI YÖNETİM ENDPOINT'LERİ ====================

@app.route('/api/users/<username>/role', methods=['PUT'])
def update_user_role(username):
    """Kullanıcı rolünü güncelle"""
    data = request.json
    role = data.get('role')

    if not role or role not in ['normal', 'admin', 'ust_duzey_yonetici']:
        return jsonify({"success": False, "message": "Geçersiz rol. Rol: 'normal', 'admin' veya 'ust_duzey_yonetici' olmalı"}), 400

    try:
        with flask_transaction() as sess:
            users = UserRepository(sess)
            if not users.update_role(username, role):
                return jsonify({"success": False, "message": "Kullanıcı bulunamadı"}), 404
            return jsonify({
                'success': True,
                'message': f"Kullanıcı '{username}' rolü '{role}' olarak güncellendi."
            }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

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

    try:
        with flask_transaction() as sess:
            users = UserRepository(sess)
            cat = CatalogRepository(sess)
            u = users.get_by_username(username)
            if not u:
                return jsonify({"success": False, "message": "Kullanıcı bulunamadı"}), 404
            user_id = u.id

            ana_bolge_kodlari = ['10', '11', '20', '30']

            if bolge_kodu in ana_bolge_kodlari:
                ilgili_bolgeler = get_related_bolge_kodlari(bolge_kodu)
                eklenen_bolgeler = []
                zaten_var_olanlar = []
                for bolge in ilgili_bolgeler:
                    if not cat.bolge_exists(bolge):
                        continue
                    ins, dup = users.add_user_bolge(user_id, bolge)
                    if ins:
                        eklenen_bolgeler.append(bolge)
                    elif dup:
                        zaten_var_olanlar.append(bolge)
                mesaj = f"Ana bölge '{bolge_kodu}' ve ilgili {len(eklenen_bolgeler)} alt bölge kullanıcı '{username}' için eklendi."
                if zaten_var_olanlar:
                    mesaj += f" ({len(zaten_var_olanlar)} bölge zaten mevcuttu)"
                return jsonify({
                    'success': True,
                    'message': mesaj,
                    'eklenen_bolgeler': eklenen_bolgeler,
                    'zaten_var_olanlar': zaten_var_olanlar
                }), 200

            if not cat.bolge_exists(bolge_kodu):
                return jsonify({"success": False, "message": "Geçersiz bölge kodu"}), 400
            ins, dup = users.add_user_bolge(user_id, bolge_kodu)
            if not ins and dup:
                return jsonify({"success": False, "message": "Bu bölge kodu zaten eklenmiş"}), 409
            return jsonify({
                'success': True,
                'message': f"Bölge kodu '{bolge_kodu}' kullanıcı '{username}' için eklendi."
            }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/users/<username>/bolge/<bolge_kodu>', methods=['DELETE'])
def remove_user_bolge(username, bolge_kodu):
    """Kullanıcıdan bölge kodu kaldır"""
    try:
        with flask_transaction() as sess:
            users = UserRepository(sess)
            u = users.get_by_username(username)
            if not u:
                return jsonify({"success": False, "message": "Kullanıcı bulunamadı"}), 404
            n = users.remove_user_bolge(u.id, bolge_kodu)
            if n > 0:
                return jsonify({
                    'success': True,
                    'message': f"Bölge kodu '{bolge_kodu}' kullanıcı '{username}' için kaldırıldı."
                }), 200
            return jsonify({"success": False, "message": "Bölge kodu bulunamadı"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/users/<username>', methods=['GET'])
def get_user_info(username):
    """Kullanıcı bilgilerini getir"""
    try:
        sess = get_flask_session()
        info = UserRepository(sess).user_info_dict(username)
        if not info:
            return jsonify({"success": False, "message": "Kullanıcı bulunamadı"}), 404
        return jsonify({
            'success': True,
            'username': info['username'],
            'role': info['role'] or 'normal',
            'default_bolge_kodu': info['default_bolge_kodu'],
            'bolge_kodlari': info['bolge_kodlari']
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/users', methods=['GET'])
def list_all_users():
    """Tüm kullanıcıları listele"""
    try:
        sess = get_flask_session()
        users = UserRepository(sess).list_users_with_bolgeler()
        return jsonify({
            'success': True,
            'data': users
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    print("🔄 Veritabanı migration kontrolü yapılıyor...")
    migrate_db()
    print("✅ Migration kontrolü tamamlandı!")

    print("🔄 Admin kullanıcısı kontrol ediliyor...")
    try:
        with session_scope() as admin_sess:
            admin_username = get_admin_username()
            ur = UserRepository(admin_sess)
            if not ur.get_by_username(admin_username):
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
                    ur.create(admin_username, generate_password_hash(pwd), 'admin')
                    if not generated:
                        print(f"✅ Admin kullanıcısı oluşturuldu: {admin_username}")
            else:
                print("✅ Admin kullanıcısı zaten mevcut")
    except Exception as e:
        print(f"❌ Admin kullanıcısı oluşturulurken hata: {e}")
        import traceback
        traceback.print_exc()

    print("🚀 Flask sunucusu başlatılıyor...")
    print(f"📁 SQLite veritabanı: {DATABASE_PATH}")
    app.run(debug=False, host=get_flask_host(), port=get_flask_port())
