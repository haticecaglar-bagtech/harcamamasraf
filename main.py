import sys
import threading
import time
from PyQt5.QtWidgets import (QApplication, QDialog, QMessageBox, QMainWindow, 
                              QLabel, QVBoxLayout, QWidget)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from config import get_flask_host, get_flask_port, get_health_check_url
from api_client import ApiClient
from harcama_masraf_app import HarcamaMasrafApp
from LoginRegister import LoginRegister
from RestApi import app as flask_app
from splash_screen import SplashScreen  # Yeni splash screen import3
import sys
import os
from PyQt5.QtGui import QFont, QIcon

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
class BackendLoader(QThread):
    """Backend verilerini yüklemek için ayrı thread"""
    data_loaded = pyqtSignal(dict)  # Veriler yüklendiğinde sinyal gönder
    error_occurred = pyqtSignal(str)  # Hata durumunda sinyal gönder

    def __init__(self, api_client, username):
        super().__init__()
        self.api_client = api_client
        self.username = username

    def run(self):
        """Backend verilerini yükle"""
        try:
            print("DEBUG - BackendLoader başlatılıyor...")
            
            # Kullanıcı ID'sini al
            response = self.api_client.get_user_id(self.username)
            if response and 'user_id' in response:
                user_id = response['user_id']
                print(f"DEBUG - Kullanıcı ID alındı: {user_id}")

                # Diğer gerekli verileri yükle (örnek)
                # user_data = self.api_client.get_user_data(user_id)
                # categories = self.api_client.get_categories()
                # etc...

                # Minimum bekleme süresi (splash screen'i görmek için)
                time.sleep(3)

                self.data_loaded.emit({
                    'user_id': user_id,
                    'username': self.username
                })
                print("DEBUG - BackendLoader başarıyla tamamlandı")
            else:
                error_msg = "Kullanıcı ID'si alınamadı!"
                print(f"DEBUG - BackendLoader hatası: {error_msg}")
                self.error_occurred.emit(error_msg)

        except Exception as e:
            error_msg = f"Backend yükleme hatası: {str(e)}"
            print(f"DEBUG - BackendLoader exception: {error_msg}")
            self.error_occurred.emit(error_msg)


def start_flask_server():
    """Flask sunucusunu ayrı bir thread'de başlat"""
    try:
        print("Flask sunucu başlatılıyor...")
        flask_app.run(
            debug=False,
            host=get_flask_host(),
            port=get_flask_port(),
            use_reloader=False,
        )
    except Exception as e:
        print(f"Flask sunucu hatası: {e}")


def wait_for_flask_server(max_attempts=30):
    """Flask sunucusunun başlamasını bekle"""
    import requests

    for attempt in range(max_attempts):
        try:
            response = requests.get(get_health_check_url(), timeout=2)
            print("Flask sunucu hazır!")
            return True
        except:
            time.sleep(0.5)
            print(f"Flask sunucu bekleniyor... ({attempt + 1}/{max_attempts})")

    print("Flask sunucu başlatılamadı!")
    return False


def main():
    # Flask sunucusunu ayrı thread'de başlat
    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()

    # Flask sunucusunun başlamasını bekle
    if not wait_for_flask_server():
        print("Flask sunucu başlatılamadı, GUI kapatılıyor...")
        return

    app = QApplication(sys.argv)

    # Modern ve minimalist stylesheet - Kurumsal ve Profesyonel Tema
    style = """
    /* Base Theme - Kurumsal Açık Gri ve Beyaz Tonları */
    QWidget {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #f8f9fa, stop:0.5 #ffffff, stop:1 #f1f3f5);
        font-family: 'Segoe UI', sans-serif;
        font-size: 15px;
        color: #212529;
    }

    /* Title Styles */
    QLabel[title="true"] {
        font-size: 20px;
        font-weight: 600;
        color: #1e293b;
        padding-bottom: 12px;
    }

    /* Subtle shadow effect for containers */
    QGroupBox, QFrame[frameShape="1"], QFrame[frameShape="2"] {
        border-radius: 20px;
        background: #ffffff;
        border: 1px solid #dee2e6;
        padding: 16px;
        margin-top: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }

    /* Input Fields with modern styling */
    QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
        border: 2px solid #dee2e6;
        border-radius: 12px;
        padding: 15px 20px;
        background: #ffffff;
        color: #212529;
        min-height: 24px;
        selection-background-color: #3b82f6;
        selection-color: white;
    }

    QLineEdit:focus, QComboBox:focus, QDateEdit:focus,
    QSpinBox:focus, QDoubleSpinBox:focus {
        border-color: #3b82f6;
        background: #ffffff;
    }

    QLineEdit[error="true"] {
        border-color: #ef4444;
        background-color: #fef2f2;
    }

    /* Buttons with modern gradient and hover effects - Kurumsal Mavi - TÜM BUTONLAR RENKLİ */
    QPushButton {
        background-color: #3b82f6 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #3b82f6, stop:0.5 #2563eb, stop:1 #1d4ed8) !important;
        border: 2px solid #2563eb !important;
        border-radius: 12px;
        padding: 15px 30px;
        color: #000000 !important;
        font-weight: 600;
        font-size: 14px;
        letter-spacing: 0.5px;
        min-width: 90px;
    }

    QPushButton:hover {
        background-color: #2563eb !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #2563eb, stop:0.5 #1d4ed8, stop:1 #1e40af) !important;
        border-color: #1d4ed8 !important;
        color: #000000 !important;
    }

    QPushButton:pressed {
        background-color: #1d4ed8 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #1d4ed8, stop:0.5 #1e40af, stop:1 #1e3a8a) !important;
        border-color: #1e40af !important;
        color: #000000 !important;
    }

    QPushButton:disabled {
        background-color: #cbd5e1 !important;
        background: #cbd5e1 !important;
        color: #64748b !important;
        border-color: #94a3b8 !important;
    }

    /* Secondary button style - Artık renkli */
    QPushButton[secondary="true"] {
        background-color: #10b981 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #10b981, stop:1 #059669) !important;
        border: 2px solid #059669 !important;
        color: #000000 !important;
    }

    QPushButton[secondary="true"]:hover {
        background-color: #059669 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #059669, stop:1 #047857) !important;
        border-color: #047857 !important;
        color: #000000 !important;
    }
    
    QPushButton[secondary="true"]:pressed {
        background-color: #047857 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #047857, stop:1 #065f46) !important;
        border-color: #065f46 !important;
        color: #000000 !important;
    }

    /* Tab widget with modern styling - Kurumsal */
    QTabWidget::pane {
        border: 1px solid #dee2e6;
        border-radius: 20px;
        margin-top: 4px;
        background: #ffffff;
    }

    QTabBar::tab {
        padding: 10px 20px;
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-bottom: none;
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
        margin-right: 4px;
        color: #495057;
        font-weight: 500;
    }

    QTabBar::tab:selected {
        background: #ffffff;
        color: #2563eb;
        border-bottom: 2px solid #3b82f6;
        margin-bottom: -1px;
    }

    QTabBar::tab:hover {
        background: #e9ecef;
        color: #1e293b;
    }

    /* Table styles with modern look - Kurumsal */
    QTableView {
        border: 1px solid #dee2e6;
        border-radius: 20px;
        gridline-color: #e9ecef;
        selection-background-color: #3b82f6;
        selection-color: white;
        alternate-background-color: #f8f9fa;
        background: #ffffff;
    }

    QHeaderView::section {
        background-color: #f1f3f5;
        padding: 8px;
        border: none;
        border-bottom: 1px solid #dee2e6;
        font-weight: 600;
        color: #1e293b;
    }

    /* Tooltip with modern appearance */
    QToolTip {
        background-color: #1e293b;
        color: #ffffff;
        border: 1px solid #334155;
        padding: 8px 12px;
        border-radius: 12px;
        font-size: 14px;
    }

    /* Scrollbar with modern thin design */
    QScrollBar:vertical {
        border: none;
        background: #f1f5f9;
        width: 8px;
        margin: 0;
    }

    QScrollBar::handle:vertical {
        background: #cbd5e1;
        min-height: 30px;
        border-radius: 4px;
    }

    QScrollBar::handle:vertical:hover {
        background: #94a3b8;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
        background: none;
    }

    /* Progress bar styling - Kurumsal Mavi */
    QProgressBar {
        border: 1px solid #dee2e6;
        border-radius: 12px;
        text-align: center;
        background: #f8f9fa;
        color: #212529;
    }

    QProgressBar::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #3b82f6, stop:0.5 #2563eb, stop:1 #1d4ed8);
        border-radius: 12px;
    }

    /* Checkbox and radio button styling */
    QCheckBox::indicator, QRadioButton::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #cbd5e1;
        border-radius: 4px;
        background: #ffffff;
    }

    QCheckBox::indicator:checked, QRadioButton::indicator:checked {
        background-color: #3b82f6;
        border-color: #3b82f6;
    }

    QRadioButton::indicator {
        border-radius: 9px;
    }

    /* Menu styling */
    QMenu {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 4px;
        background: #ffffff;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    QMenu::item {
        padding: 8px 24px 8px 16px;
        border-radius: 8px;
        color: #1e293b;
    }

    QMenu::item:selected {
        background-color: #eff6ff;
        color: #2563eb;
    }

    QMenu::separator {
        height: 1px;
        background: #e2e8f0;
        margin: 4px 0;
    }

    /* Status bar styling - Kurumsal */
    QStatusBar {
        background: #f8f9fa;
        border-top: 1px solid #dee2e6;
        padding: 4px;
        color: #495057;
    }

    /* Dialog and message box styling */
    QDialog, QMessageBox {
        background: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 20px;
        padding: 20px;
    }

    QDialog QLabel, QMessageBox QLabel {
        color: #1e293b;
        padding: 8px 0;
        font-size: 14px;
        font-weight: 500;
        background: transparent;
    }

    /* QMessageBox button styling - Kurumsal ve görünür */
    QMessageBox QPushButton {
        background-color: #3b82f6 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #3b82f6, stop:1 #2563eb) !important;
        color: #000000 !important;
        border: 2px solid #2563eb !important;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 14px;
        min-width: 100px;
        min-height: 35px;
    }

    QMessageBox QPushButton:hover {
        background-color: #2563eb !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #2563eb, stop:1 #1d4ed8) !important;
        border-color: #1d4ed8 !important;
        color: #000000 !important;
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
    }

    QMessageBox QPushButton:pressed {
        background-color: #1d4ed8 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #1d4ed8, stop:1 #1e40af) !important;
        border-color: #1e40af !important;
        color: #000000 !important;
    }
    
    /* Yes/No/Cancel butonları için özel stiller */
    QMessageBox QPushButton[text*="Evet"],
    QMessageBox QPushButton[text*="Yes"],
    QMessageBox QPushButton[text*="OK"],
    QMessageBox QPushButton[text*="Tamam"] {
        background-color: #10b981 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #10b981, stop:1 #059669) !important;
        color: #000000 !important;
        border: 2px solid #059669 !important;
    }
    
    QMessageBox QPushButton[text*="Hayır"],
    QMessageBox QPushButton[text*="No"],
    QMessageBox QPushButton[text*="Cancel"],
    QMessageBox QPushButton[text*="İptal"] {
        background-color: #6b7280 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #6b7280, stop:1 #4b5563) !important;
        color: #000000 !important;
        border: 2px solid #4b5563 !important;
    }

    /* QMessageBox icon styling */
    QMessageBox QLabel[icon="true"] {
        background: transparent;
    }
    
    /* QDialogButtonBox button styling - Tüm dialog butonları renkli */
    QDialogButtonBox QPushButton {
        background-color: #3b82f6 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #3b82f6, stop:1 #2563eb) !important;
        color: #000000 !important;
        border: 2px solid #2563eb !important;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 14px;
        min-width: 100px;
        min-height: 35px;
    }
    
    QDialogButtonBox QPushButton:hover {
        background-color: #2563eb !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #2563eb, stop:1 #1d4ed8) !important;
        border-color: #1d4ed8 !important;
        color: #000000 !important;
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
    }
    
    QDialogButtonBox QPushButton:pressed {
        background-color: #1d4ed8 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #1d4ed8, stop:1 #1e40af) !important;
        border-color: #1e40af !important;
        color: #000000 !important;
    }
    
    /* QDialogButtonBox OK butonu - Yeşil */
    QDialogButtonBox QPushButton[text*="OK"],
    QDialogButtonBox QPushButton[text*="Tamam"],
    QDialogButtonBox QPushButton[text*="Kaydet"],
    QDialogButtonBox QPushButton[text*="Ekle"] {
        background-color: #10b981 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #10b981, stop:1 #059669) !important;
        border: 2px solid #059669 !important;
        color: #000000 !important;
    }
    
    QDialogButtonBox QPushButton[text*="OK"]:hover,
    QDialogButtonBox QPushButton[text*="Tamam"]:hover,
    QDialogButtonBox QPushButton[text*="Kaydet"]:hover,
    QDialogButtonBox QPushButton[text*="Ekle"]:hover {
        background-color: #059669 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #059669, stop:1 #047857) !important;
        border-color: #047857 !important;
        color: #000000 !important;
    }
    
    /* QDialogButtonBox Cancel butonu - Gri */
    QDialogButtonBox QPushButton[text*="Cancel"],
    QDialogButtonBox QPushButton[text*="İptal"],
    QDialogButtonBox QPushButton[text*="Kapat"] {
        background-color: #6b7280 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #6b7280, stop:1 #4b5563) !important;
        border: 2px solid #4b5563 !important;
        color: #000000 !important;
    }
    
    QDialogButtonBox QPushButton[text*="Cancel"]:hover,
    QDialogButtonBox QPushButton[text*="İptal"]:hover,
    QDialogButtonBox QPushButton[text*="Kapat"]:hover {
        background-color: #4b5563 !important;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #4b5563, stop:1 #374151) !important;
        border-color: #374151 !important;
        color: #000000 !important;
    }

    /* Modern combo box dropdown */
    QComboBox QAbstractItemView {
        border: 1px solid #dee2e6;
        border-radius: 12px;
        padding: 4px;
        background: #ffffff;
        selection-background-color: #3b82f6;
        selection-color: white;
    }

    /* Slider styling */
    QSlider::groove:horizontal {
        height: 4px;
        background: #dee2e6;
        border-radius: 2px;
    }

    QSlider::handle:horizontal {
        width: 16px;
        height: 16px;
        margin: -6px 0;
        background: #3b82f6;
        border-radius: 8px;
    }
    """

    app.setStyleSheet(style)

    api_client = ApiClient()

    # Ana döngü - çıkış yapınca login ekranına döner
    while True:
        api_client.clear_token()
        # Login ekranını göster
        login_window = LoginRegister(api_client)
        # Login penceresine de ikonu ayarla
        try:
            icon_path = get_resource_path("icons/a.png")
            if os.path.exists(icon_path):
                login_window.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Login penceresi ikonunu ayarlama hatası: {e}")

        # Login iptal edilirse veya pencere kapatılırsa döngüden çık
        if login_window.exec_() != QDialog.Accepted:
            print("DEBUG - Login iptal edildi veya pencere kapatıldı")
            break

        # Login başarılı - ana uygulamayı başlat
        # Kullanıcı bilgilerini al
        user_info = login_window.user_info
        if not user_info:
            # Eğer user_info yoksa eski yöntemle devam et
            username = login_window.username_input.text()
            # user_id'yi API'den al
            response = api_client.get_user_id(username)
            if response and 'user_id' in response:
                user_id = response['user_id']
                user_info = {
                    'user_id': user_id,
                    'username': username,
                    'role': 'normal',
                    'bolge_kodlari': [],
                    'default_bolge_kodu': None
                }
            else:
                QMessageBox.critical(None, "Hata", "Kullanıcı bilgileri alınamadı.")
                return
        
        username = user_info['username']
        user_id = user_info['user_id']
        role = user_info.get('role', 'normal')
        bolge_kodlari = user_info.get('bolge_kodlari', [])

        # Splash screen'i göster
        splash = SplashScreen()

        # Splash screen'e de ikonu ayarla
        try:
            icon_path = get_resource_path("icons/a.png")
            if os.path.exists(icon_path):
                splash.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Splash screen ikonunu ayarlama hatası: {e}")

        splash.show()

        # Backend verilerini yüklemek için thread başlat
        backend_loader = BackendLoader(api_client, username)

        def on_data_loaded(data):
            """Veriler yüklendiğinde ana uygulamayı başlat"""
            try:
                print(f"DEBUG - Ana pencere oluşturuluyor (user_id: {user_id}, username: {username}, role: {role})")
                
                main_window = HarcamaMasrafApp(api_client, username, user_id, role, bolge_kodlari)
                print("DEBUG - Ana pencere oluşturuldu")

                # Ana pencereye de ikonu ayarla
                try:
                    icon_path = get_resource_path("icons/a.png")
                    if os.path.exists(icon_path):
                        main_window.setWindowIcon(QIcon(icon_path))
                except Exception as e:
                    print(f"Ana pencere ikonunu ayarlama hatası: {e}")

                # Ana pencereyi global olarak sakla (garbage collection'dan korumak için)
                app.main_window = main_window
                app.should_return_to_login = False
                
                # pyqtSignal zaten ana thread'e taşır, bu yüzden doğrudan gösterebiliriz
                # Splash'i kapat
                splash.close_splash()
                print("DEBUG - Splash screen kapatıldı")
                
                # Ana pencereyi göster
                main_window.show()
                print("DEBUG - Ana pencere gösterildi")
                
                # Ana pencereyi aktif hale getir
                main_window.raise_()
                main_window.activateWindow()
                
                # Event loop'un çalışması için processEvents çağır
                QApplication.processEvents()
                
                print("DEBUG - Ana pencere başarıyla yüklendi ve gösterildi")
                
            except Exception as e:
                print(f"DEBUG - on_data_loaded hatası: {str(e)}")
                import traceback
                print(f"DEBUG - Traceback: {traceback.format_exc()}")
                
                # Splash'i kapat
                try:
                    splash.close_splash()
                except:
                    pass
                
                # Hata durumunda bile minimal bir pencere oluştur
                try:
                    error_window = QMainWindow()
                    error_window.setWindowTitle("Özege Tütün - Hata")
                    error_window.setGeometry(100, 100, 600, 400)
                    
                    central = QWidget()
                    error_window.setCentralWidget(central)
                    layout = QVBoxLayout(central)
                    
                    error_label = QLabel(
                        f"<h2>Uygulama Yüklenirken Hata Oluştu</h2>"
                        f"<p><b>Hata:</b> {str(e)}</p>"
                        f"<p>Lütfen uygulamayı yeniden başlatın.</p>"
                    )
                    error_label.setWordWrap(True)
                    error_label.setAlignment(Qt.AlignCenter)
                    layout.addWidget(error_label)
                    
                    # Ana pencereyi global olarak sakla
                    app.main_window = error_window
                    
                    # Pencereyi göster
                    error_window.show()
                    error_window.raise_()
                    error_window.activateWindow()
                    
                    print("DEBUG - Hata penceresi gösterildi")
                    
                    # Hata mesajı göster
                    error_dialog = QMessageBox()
                    try:
                        icon_path = get_resource_path("icons/a.png")
                        if os.path.exists(icon_path):
                            error_dialog.setWindowIcon(QIcon(icon_path))
                            error_window.setWindowIcon(QIcon(icon_path))
                    except:
                        pass
                    
                    error_dialog.critical(None, "Hata", 
                        f"Ana pencere yüklenirken bir hata oluştu:\n{str(e)}\n\nLütfen uygulamayı yeniden başlatın.")
                    print("DEBUG - Hata mesajı gösterildi")
                    
                except Exception as e2:
                    print(f"DEBUG - Hata penceresi oluşturulamadı: {str(e2)}")
                    # Son çare olarak sadece hata mesajı göster
                    try:
                        error_dialog = QMessageBox()
                        error_dialog.critical(None, "Kritik Hata", 
                            f"Uygulama yüklenirken kritik bir hata oluştu:\n{str(e)}\n\nUygulama kapatılacak.")
                    except:
                        pass

        def on_error(error_message):
            """Hata durumunda splash'i kapat ve mesaj göster"""
            splash.close_splash()
            error_dialog = QMessageBox()

            # Hata dialoguna da ikonu ayarla
            try:
                icon_path = get_resource_path("icons/a.png")
                if os.path.exists(icon_path):
                    error_dialog.setWindowIcon(QIcon(icon_path))
            except Exception as e:
                print(f"Hata dialog ikonunu ayarlama hatası: {e}")

            error_dialog.critical(None, "Hata", error_message)
            # sys.exit() kaldırıldı - GUI'yi kapatmayacak
            print("DEBUG - Hata durumunda GUI açık kalıyor")

        # Sinyalleri bağla
        backend_loader.data_loaded.connect(on_data_loaded)
        backend_loader.error_occurred.connect(on_error)

        # Backend yüklemeyi başlat
        backend_loader.start()

        # Ana pencereyi global olarak sakla (logout için)
        app.main_window = None
        app.should_return_to_login = False

        # Ana event loop'u başlat
        print("DEBUG - Ana event loop başlatılıyor...")
        
        try:
            # Event loop'u başlat
            print("DEBUG - Event loop başlatılıyor...")
            
            # Event loop'u başlat ve sonucu bekle
            exit_code = app.exec_()
            print("DEBUG - Ana event loop normal şekilde sonlandı (exit_code: {})".format(exit_code))
            
        except Exception as e:
            print(f"DEBUG - Event loop hatası: {str(e)}")
            import traceback
            print(f"DEBUG - Event loop traceback: {traceback.format_exc()}")
            exit_code = 1
        finally:
            print("DEBUG - Event loop tamamen sonlandı")
        
        # Ana pencere kapatıldığında login ekranına dön
        if hasattr(app, 'should_return_to_login') and app.should_return_to_login:
            print("DEBUG - Ana pencere kapatıldı, login ekranına dönülüyor")
            # Ana pencere referansını temizle
            app.main_window = None
            app.should_return_to_login = False
            # Döngüye devam et (login ekranı tekrar açılacak)
            continue
        else:
            # Normal kapanma - döngüden çık
            print("DEBUG - Uygulama normal şekilde kapatılıyor")
            break
    
    # Döngü bittiğinde uygulamayı kapat
    print("DEBUG - Uygulama kapatılıyor")
    return 0


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"DEBUG - Ana fonksiyon hatası: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("DEBUG - Uygulama tamamen sonlandı")