import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout,
                             QHBoxLayout, QWidget, QTabWidget, QLabel,
                             QMessageBox, QApplication, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from api_client import ApiClient
from harcamaOperations import HarcamaTab
from masrafOperations import MasrafTab
from kodOperations import VeriYonetimiTab
from LoginRegister import LoginRegister
from OdemeOperations import PaymentTab  # Yeni eklenen import
import os

class HarcamaMasrafApp(QMainWindow):
    def __init__(self, api_client, username, user_id, role='normal', bolge_kodlari=None):
        super().__init__()

        # API Client ve kullanıcı bilgilerini sakla
        self.api_client = api_client
        self.current_user = username
        self.current_user_id = user_id
        self.current_role = role or 'normal'
        self.bolge_kodlari = bolge_kodlari or []

        # Uygulama ikonunu ayarla
        try:
            icon_path = get_resource_path("icons/a.png")
            self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"İkon ayarlama hatası: {e}")

        # Ana pencereyi kur
        self.setup_main_window()

    def setup_main_window(self):
        self.setWindowTitle("Özege Tütün - Harcama ve Masraf Takip")
        self.setGeometry(100, 100, 1200, 800)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setAlignment(Qt.AlignCenter)

        # Arka plan rengi - Kurumsal Açık Gri ve Beyaz Tonları
        self.central_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #f8f9fa, stop:0.5 #ffffff, stop:1 #f1f3f5);
        """)

        from PyQt5.QtWidgets import QFrame, QSpacerItem, QSizePolicy
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 20px;
                padding: 32px 48px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);
            }
        """)
        card_layout = QVBoxLayout(self.card)
        card_layout.setAlignment(Qt.AlignCenter)

        logo_label = QLabel()
        logo_label.setText("<span style='font-size:48px; font-weight:bold; color:#2563eb;'>ÖZEGE TÜTÜN</span>")
        logo_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(logo_label)

        welcome_label = QLabel(f"Hoş Geldiniz, <b>{self.current_user}</b>")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("font-size: 24px; color: #1e293b; margin: 16px;")
        card_layout.addWidget(welcome_label)

        desc_label = QLabel(
            "<i>Harcama ve Masraf Takip Uygulamasına giriş yaptınız.<br>İşleminize aşağıdan başlayabilirsiniz.</i>")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("font-size: 16px; color: #495057; margin-bottom: 24px;")
        card_layout.addWidget(desc_label)

        # Butonları 2x2 grid yapısında düzenle
        self.button_grid_layout = QVBoxLayout()
        self.button_grid_layout.setSpacing(16)

        # İlk satır butonları
        first_row_layout = QHBoxLayout()
        first_row_layout.setSpacing(24)

        # Üst düzey yönetici için sadece analiz butonu göster
        if self.current_role != 'ust_duzey_yonetici':
            self.harcama_button = QPushButton("💰 Harcama İşlemi")
            self.harcama_button.setMinimumHeight(60)
            self.harcama_button.clicked.connect(lambda: self.open_tab(0))

            self.masraf_button = QPushButton("📊 Masraf İşlemi")
            self.masraf_button.setMinimumHeight(60)
            self.masraf_button.clicked.connect(lambda: self.open_tab(1))

            first_row_layout.addWidget(self.harcama_button)
            first_row_layout.addWidget(self.masraf_button)

        # İkinci satır butonları
        second_row_layout = QHBoxLayout()
        second_row_layout.setSpacing(24)

        # Üst düzey yönetici için sadece analiz butonu göster
        if self.current_role == 'ust_duzey_yonetici':
            self.analiz_button = QPushButton("📊 Analiz Paneli")
            self.analiz_button.setMinimumHeight(60)
            self.analiz_button.clicked.connect(lambda: self.open_tab(0))
            second_row_layout.addWidget(self.analiz_button)
        else:
            # Bölgelere göre görüntüle butonu (normal kullanıcı ve admin için)
            self.bolge_goruntule_button = QPushButton("📈 Bölgelere Göre Görüntüle")
            self.bolge_goruntule_button.setMinimumHeight(60)
            self.bolge_goruntule_button.clicked.connect(lambda: self.open_tab(2))
            second_row_layout.addWidget(self.bolge_goruntule_button)

            # Kod İşlemleri butonu (sadece admin için)
            if self.current_role == 'admin':
                self.opr_button = QPushButton("⚙️ Kod Ekleme İşlemleri")
                self.opr_button.setMinimumHeight(60)
                self.opr_button.clicked.connect(lambda: self.open_tab(3))
                second_row_layout.addWidget(self.opr_button)

        # Grid layout'a satırları ekle
        self.button_grid_layout.addLayout(first_row_layout)
        self.button_grid_layout.addLayout(second_row_layout)

        # Buton stillerini uygula - sadece mevcut butonlar için
        button_colors = []
        
        # Üst düzey yönetici için sadece analiz butonu - Kurumsal Mavi
        if self.current_role == 'ust_duzey_yonetici':
            button_colors.append((self.analiz_button, '#3b82f6'))
        else:
            # Normal kullanıcı ve admin için butonlar - Kurumsal Mavi tonları
            button_colors.extend([
                (self.harcama_button, '#3b82f6'),
                (self.masraf_button, '#2563eb'),
                (self.bolge_goruntule_button, '#1d4ed8')
            ])
            
            # Admin ise kod işlemleri butonunu da ekle
            if self.current_role == 'admin':
                button_colors.append((self.opr_button, '#1e40af'))

        for btn, color in button_colors:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    font-size: 16px;
                    border-radius: 15px;
                    padding: 20px 40px;
                    min-width: 220px;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                    border: 2px solid transparent;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {color}, stop:1 #2563eb);
                    border: 2px solid rgba(255, 255, 255, 0.3);
                    transform: translateY(-3px);
                }}
                QPushButton:pressed {{
                    background: {color};
                    transform: translateY(0px);
                }}
            """)

        card_layout.addLayout(self.button_grid_layout)

        footer = QLabel("<span style='color:#495057;'>Powered by <b>Özege Tütün</b></span>")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("margin-top: 32px; font-size: 13px;")
        card_layout.addWidget(footer)

        # Store spacers and card as attributes for later removal
        self.top_spacer = QSpacerItem(20, 80, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.bottom_spacer = QSpacerItem(20, 80, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.main_layout.addSpacerItem(self.top_spacer)
        self.main_layout.addWidget(self.card, alignment=Qt.AlignCenter)
        self.main_layout.addSpacerItem(self.bottom_spacer)

        # Tab widget oluştur
        self.tabs = QTabWidget()
        self.tabs.setVisible(False)  # Başlangıçta gizli
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 20px;
                background: #ffffff;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
            }
            QTabBar::tab {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                padding: 12px 24px;
                color: #495057;
                font-weight: 500;
                font-size: 14px;
                margin-right: 2px;
                min-width: 150px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #2563eb;
                border-bottom: 2px solid #3b82f6;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #e9ecef;
                color: #1e293b;
            }
        """)

        # Veri yapılarını paylaşmak için ortak bir veri sözlüğü
        self.data = {
            'bolge_kodlari': {},
            'kaynak_tipleri': {},
            'stages': {},
            'operasyonlar': {},
            'stage_operasyonlar': {}
        }

        # Veri yapılarını yükle
        try:
            self.load_data()
        except Exception as e:
            print(f"DEBUG - Veri yükleme hatası: {str(e)}")
            import traceback
            print(f"DEBUG - Traceback: {traceback.format_exc()}")

        # Sekmeleri oluştur
        # Üst düzey yönetici sadece analiz sayfasını görür
        if self.current_role != 'ust_duzey_yonetici':
            try:
                self.harcama_tab = HarcamaTab(self.api_client, self.current_user_id)
                self.tabs.addTab(self.harcama_tab, "Harcama İşlemi")
            except Exception as e:
                print(f"DEBUG - HarcamaTab oluşturma hatası: {str(e)}")
                import traceback
                print(f"DEBUG - Traceback: {traceback.format_exc()}")
                # Harcama tab'ı oluşturulamazsa boş bir widget ekle
                error_widget = QWidget()
                error_label = QLabel(f"Harcama sekmesi yüklenemedi: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_layout = QVBoxLayout(error_widget)
                error_layout.addWidget(error_label)
                self.tabs.addTab(error_widget, "Harcama İşlemi")

            try:
                self.masraf_tab = MasrafTab(self.data, self.api_client, self.current_user_id, 
                                            self.current_role, self.bolge_kodlari)
                self.tabs.addTab(self.masraf_tab, "Masraf İşlemi")
            except Exception as e:
                print(f"DEBUG - MasrafTab oluşturma hatası: {str(e)}")
                import traceback
                print(f"DEBUG - Traceback: {traceback.format_exc()}")
                # Masraf tab'ı oluşturulamazsa boş bir widget ekle
                error_widget = QWidget()
                error_label = QLabel(f"Masraf sekmesi yüklenemedi: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_layout = QVBoxLayout(error_widget)
                error_layout.addWidget(error_label)
                self.tabs.addTab(error_widget, "Masraf İşlemi")

        # Bölgelere göre görüntüle sekmesi
        # Üst düzey yönetici için özel analiz sayfası
        if self.current_role == 'ust_duzey_yonetici':
            try:
                from ustDuzeyYoneticiOperations import UstDuzeyYoneticiTab
                self.ust_duzey_yonetici_tab = UstDuzeyYoneticiTab(
                    self.api_client,
                    self.current_user_id,
                    self.current_role,
                    self.bolge_kodlari
                )
                self.tabs.addTab(self.ust_duzey_yonetici_tab, "📊 Analiz Paneli")
            except Exception as e:
                print(f"DEBUG - UstDuzeyYoneticiTab oluşturma hatası: {str(e)}")
                import traceback
                print(f"DEBUG - Traceback: {traceback.format_exc()}")
                error_widget = QWidget()
                error_label = QLabel(f"Analiz paneli yüklenemedi: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_layout = QVBoxLayout(error_widget)
                error_layout.addWidget(error_label)
                self.tabs.addTab(error_widget, "📊 Analiz Paneli")
        else:
            # Normal kullanıcı ve admin için normal bölge görüntüle sayfası
            try:
                from bolgeGoruntuleOperations import BolgeGoruntuleTab
                self.bolge_goruntule_tab = BolgeGoruntuleTab(
                    self.api_client, 
                    self.current_user_id, 
                    self.current_role, 
                    self.bolge_kodlari
                )
                self.tabs.addTab(self.bolge_goruntule_tab, "Bölgelere Göre Görüntüle")
            except Exception as e:
                print(f"DEBUG - BolgeGoruntuleTab oluşturma hatası: {str(e)}")
                import traceback
                print(f"DEBUG - Traceback: {traceback.format_exc()}")
                # Bölge görüntüle tab'ı oluşturulamazsa boş bir widget ekle
                error_widget = QWidget()
                error_label = QLabel(f"Bölgelere göre görüntüle sekmesi yüklenemedi: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_layout = QVBoxLayout(error_widget)
                error_layout.addWidget(error_label)
                self.tabs.addTab(error_widget, "Bölgelere Göre Görüntüle")

        # Kod İşlemleri sekmesi (sadece admin için)
        if self.current_role == 'admin':
            try:
                self.veri_yonetimi_tab = VeriYonetimiTab(self.data, self.on_data_updated)
                self.tabs.addTab(self.veri_yonetimi_tab, "Kod Ekleme İşlemleri")
            except Exception as e:
                print(f"DEBUG - VeriYonetimiTab oluşturma hatası: {str(e)}")
                import traceback
                print(f"DEBUG - Traceback: {traceback.format_exc()}")
                # Veri yönetimi tab'ı oluşturulamazsa boş bir widget ekle
                error_widget = QWidget()
                error_label = QLabel(f"Kod ekleme sekmesi yüklenemedi: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_layout = QVBoxLayout(error_widget)
                error_layout.addWidget(error_label)
                self.tabs.addTab(error_widget, "Kod Ekleme İşlemleri")
            
            # Kullanıcı Yönetimi sekmesi (sadece admin için)
            try:
                from kullaniciYonetimiOperations import KullaniciYonetimiTab
                # Admin şifresini saklamak yerine, kullanıcı eklerken sormak için None gönderiyoruz
                # Şifre gerektiğinde dialog ile sorulacak
                self.kullanici_yonetimi_tab = KullaniciYonetimiTab(
                    self.api_client,
                    self.current_user_id,
                    self.current_user,
                    None  # Şifre gerektiğinde sorulacak
                )
                self.tabs.addTab(self.kullanici_yonetimi_tab, "Kullanıcı Yönetimi")
            except Exception as e:
                print(f"DEBUG - KullaniciYonetimiTab oluşturma hatası: {str(e)}")
                import traceback
                print(f"DEBUG - Traceback: {traceback.format_exc()}")
                # Kullanıcı yönetimi tab'ı oluşturulamazsa boş bir widget ekle
                error_widget = QWidget()
                error_label = QLabel(f"Kullanıcı yönetimi sekmesi yüklenemedi: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_layout = QVBoxLayout(error_widget)
                error_layout.addWidget(error_label)
                self.tabs.addTab(error_widget, "Kullanıcı Yönetimi")

        # Tab widget'ı en alta ekle
        self.main_layout.addWidget(self.tabs)

        self.showMaximized()  # Başlangıçta ekranı kaplayacak kadar büyük açılır
    def open_tab(self, index):
        # Kartı ve spacerları gizle
        self.card.setVisible(False)
        self.tabs.setVisible(True)
        self.main_layout.removeItem(self.top_spacer)
        self.main_layout.removeItem(self.bottom_spacer)
        
        # Admin değilse ve kod işlemleri sekmesi seçilmişse, bir önceki sekmeye git
        if index == 3 and self.current_role != 'admin':
            index = 2  # Bölgelere göre görüntüle sekmesine git
        
        self.tabs.setCurrentIndex(index)

    def load_data(self):
        """Verileri API'den yükle"""
        try:
            # Tüm verileri tek bir API çağrısıyla al
            data = self.api_client.get_all_data()

            if not data:
                QMessageBox.warning(self, "Veri Yükleme Hatası",
                                    "Veritabanından veriler yüklenemedi. API'ye bağlantı kurulamadı veya veri alınamadı.")
                # API'den veri alınamazsa varsayılan verileri yükle
                self._load_default_data()
            else:
                self.data.update(data)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yükleme sırasında hata oluştu: {str(e)}")
            # Hata durumunda varsayılan verileri yükle
            self._load_default_data()
    def _load_default_data(self):
        """Varsayılan verileri kullan (API bağlantısı başarısız olduğunda)"""
        # Kaynak tipi verileri
        self.data['kaynak_tipleri'] = {
            "01": "İşçilik",
            "02": "Malzeme",
            "03": "Hizmet",
            "04": "Enerji",
            "05": "Kiralama"
        }

        # Stage verileri
        self.data['stages'] = {
            "01": "Fidelik",
            "02": "Tarla Hazırlığı",
            "03": "Gübreleme",
            "04": "Dikim",
            "05": "İlaçlama",
            "06": "Sulama",
            "07": "Çapalama",
            "08": "Kırım",
            "09": "Kurutma",
            "10": "Kutulama",
            "11": "Diğer",
            "12": "Nakliye",
            "13": "Supervisor",
            "14": "Kültürel İşlemler"
        }

        # Operasyonlar (her stage için)
        self.data['operasyonlar'] = {
            # Fidelik (01)
            "01": {
                "01": "Fide Yastığı Hazırlama",
                "02": "Tohum Atma",
                "03": "Fidelik Sulama",
                "04": "Fide Çekimi",
                "05": "Gübre Uygulama",
                "06": "Ot Temizleme",
                "07": "Sera Havalandırma - Kapatma",
                "08": "İlaçlama",
                "09": "Fide Kırpma",
                "97": "Malzeme İndirme Yükleme",
                "98": "Malzeme Nakliye",
                "99": "Ekipman Bakım Tamirat"
            },
            # ... (diğer stage'ler)
        }

        # Stage-Operasyon kombinasyonları
        self.data['stage_operasyonlar'] = {
            "0101": "Fidelik_Fide Yastığı Hazırlama",
            "0102": "Fidelik_Tohum Atma",
            # ... (diğer kombinasyonlar)
        }

        # Örnek bölge kodları
        self.data['bolge_kodlari'] = {
            "10.": "ADY",
            "20.": "MNS",
            "30.": "MRD"
        }
    def on_data_updated(self):
        """Veri yapıları güncellendiğinde çağrılır"""
        # Önce API'den verileri tekrar yükle
        self.load_data()

        # Diğer sekmelere güncel verileri yansıt
        self.harcama_tab.update_data(self.data)
        self.masraf_tab.update_data(self.data)

    def closeEvent(self, event):
        """Pencere kapatılırken çağrılır - Login ekranına döner"""
        print("DEBUG - HarcamaMasrafApp closeEvent çağrıldı")
        
        # Thread'lerin çalışıp çalışmadığını kontrol et
        thread_running = False
        if hasattr(self, 'harcama_tab') and self.harcama_tab:
            if hasattr(self.harcama_tab, 'thread') and self.harcama_tab.thread:
                if self.harcama_tab.thread.isRunning():
                    thread_running = True
                    print("DEBUG - Harcama thread'i çalışıyor")
        
        """if hasattr(self, 'masraf_tab') and self.masraf_tab:
            if hasattr(self.masraf_tab, 'thread') and self.masraf_tab.thread:
                if self.masraf_tab.thread.isRunning():
                    thread_running = True
                    print("DEBUG - Masraf thread'i çalışıyor")"""
        
        # Eğer thread çalışıyorsa kapatmayı engelle
        if thread_running:
            print("DEBUG - Thread çalışıyor, kapatma engelleniyor")
            QMessageBox.information(
                self,
                'İşlem Devam Ediyor',
                'Lütfen devam eden işlemin tamamlanmasını bekleyin.'
            )
            event.ignore()
            return
        
        # Kullanıcıya çıkış onayı sor
        reply = QMessageBox.question(
            self, 
            'Çıkış Yap', 
            'Çıkış yapmak istediğinizden emin misiniz?\n\nGiriş ekranına döneceksiniz.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            print("DEBUG - Kullanıcı çıkış yapmayı onayladı")
            
            # Thread'leri temizle
            if hasattr(self, 'harcama_tab') and self.harcama_tab:
                self.harcama_tab.cleanup_thread()
            
            if hasattr(self, 'masraf_tab') and self.masraf_tab:
                # Masraf tab'ında da thread varsa temizle
                if hasattr(self.masraf_tab, 'cleanup_thread'):
                    self.masraf_tab.cleanup_thread()
            
            # Ana pencereyi kapat ve login ekranına dön
            # app.should_return_to_login flag'ini set et
            app = QApplication.instance()
            if app:
                app.should_return_to_login = True
                app.main_window = None
            
            # Pencereyi kapat ve event loop'u sonlandır (login ekranına dönmek için)
            self.hide()  # Pencereyi gizle
            event.accept()  # Event'i kabul et
            print("DEBUG - Ana pencere kapatıldı, login ekranına dönülüyor")
            
            # Event loop'u sonlandır (main.py'de döngüye devam edecek)
            app.quit()
        else:
            print("DEBUG - Kullanıcı çıkış yapmayı iptal etti")
            event.ignore()


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
