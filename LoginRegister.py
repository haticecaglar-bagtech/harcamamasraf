from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QSizePolicy, QFrame, QDesktopWidget,
    QGraphicsDropShadowEffect, QWidget
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter, QBrush, QLinearGradient, QColor, QPainterPath
import os
import sys

from config import api_url


def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def resource_path(relative_path):
    """PyInstaller ile çalışırken doğru dosya yolunu verir"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)  # PyInstaller'ın geçici klasörü
    return os.path.join(os.path.abspath("."), relative_path)
class ModernLineEdit(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(50)

        # Glow effect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(10)
        glow.setColor(QColor(59, 130, 246, 100))
        glow.setOffset(0, 0)

        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #dee2e6;
                border-radius: 12px;
                padding: 15px 20px;
                background: #ffffff;
                color: #212529;
                font-size: 14px;
                font-weight: 400;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
                background: #ffffff;
                box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
            }
            QLineEdit::placeholder {
                color: #6c757d;
            }
        """)

    def focusInEvent(self, event):
        # Focus'ta glow efekti ekle
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(59, 130, 246, 150))
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        # Focus çıkışında glow efekti azalt
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(5)
        glow.setColor(QColor(59, 130, 246, 50))
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)
        super().focusOutEvent(event)


class ModernButton(QPushButton):
    def __init__(self, text, primary=True, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(50)
        self.primary = primary

        if primary:
            self.setStyleSheet("""
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
                }
                QPushButton:hover {
                    background-color: #2563eb !important;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #2563eb, stop:0.5 #1d4ed8, stop:1 #1e40af) !important;
                    border-color: #1d4ed8 !important;
                    color: #000000 !important;
                    transform: translateY(-2px);
                }
                QPushButton:pressed {
                    background-color: #1d4ed8 !important;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #1d4ed8, stop:0.5 #1e40af, stop:1 #1e3a8a) !important;
                    border-color: #1e40af !important;
                    color: #000000 !important;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #10b981 !important;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #10b981, stop:1 #059669) !important;
                    border: 2px solid #059669 !important;
                    border-radius: 12px;
                    padding: 15px 30px;
                    color: #000000 !important;
                    font-weight: 600;
                    font-size: 14px;
                    letter-spacing: 0.5px;
                }
                QPushButton:hover {
                    background-color: #059669 !important;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #059669, stop:1 #047857) !important;
                    border-color: #047857 !important;
                    color: #000000 !important;
                }
                QPushButton:pressed {
                    background-color: #047857 !important;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #047857, stop:1 #065f46) !important;
                    border-color: #065f46 !important;
                    color: #000000 !important;
                }
            """)

        # Drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)


class LoginRegister(QDialog):
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.setWindowTitle("Kullanıcı Girişi / Kayıt")

        # İkon
        icon_path = resource_path("icons/a.png")
        self.setWindowIcon(QIcon(icon_path))

        self.resize(750, 500)
        self.center_window()

        # Kurumsal ve profesyonel tema
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:0.5 #ffffff, stop:1 #f1f3f5);
                border: 1px solid #dee2e6;
                border-radius: 20px;
            }
        """)

        self.init_ui()
        self.setup_animations()

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def create_circular_pixmap(self,pixmap, size):
        """Pixmap'i yuvarlak olarak keser"""
        # Kare boyutunda yeni bir pixmap oluştur
        output = QPixmap(size, size)
        output.fill(Qt.transparent)

        # QPainter ile yuvarlak maske oluştur
        painter = QPainter(output)
        painter.setRenderHint(QPainter.Antialiasing)

        # Yuvarlak path oluştur
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)

        # Clipping path'i ayarla
        painter.setClipPath(path)

        # Orijinal pixmap'i yuvarlak alana çiz
        source_rect = pixmap.rect()
        target_rect = QRect(0, 0, size, size)
        painter.drawPixmap(target_rect, pixmap, source_rect)

        painter.end()
        return output

    def init_ui(self):
        # Ana layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setAlignment(Qt.AlignCenter)

        # Form container - glassmorphism effect
        form_frame = QFrame()
        form_frame.setFixedWidth(400)
        form_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        form_frame.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 20px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            }
        """)

        # Drop shadow for form
        form_shadow = QGraphicsDropShadowEffect()
        form_shadow.setBlurRadius(30)
        form_shadow.setColor(QColor(0, 0, 0, 80))
        form_shadow.setOffset(0, 10)
        form_frame.setGraphicsEffect(form_shadow)

        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(40, 40, 40, 40)
        form_layout.setSpacing(25)

        # Header section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(15)

        # Logo container
        logo_container = QWidget()
        logo_container.setFixedSize(100, 100)
        logo_container.setStyleSheet("""
            QWidget {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.8,
                    stop:0 rgba(59, 130, 246, 0.15), 
                    stop:0.7 rgba(59, 130, 246, 0.08),
                    stop:1 transparent);
                border-radius: 50px;
                border: 2px solid rgba(59, 130, 246, 0.2);
            }
        """)

        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(5, 5, 5, 5)  # İç boşlukları azalttık
        logo_layout.setAlignment(Qt.AlignCenter)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedSize(90, 90)  # Logo label boyutunu ayarladık
        logo_label.setStyleSheet("""
            QLabel {
                color: #6366f1;
                font-size: 36px;
                font-weight: 700;
                background: transparent;
                border: none;
                border-radius: 45px;
            }
        """)

        # Logo dosyası yükleme ve yuvarlak kesme
        try:
            # PyInstaller uyumlu path
            logo_path = resource_path("logo.jpeg")
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                # Logo'yu yuvarlak kes ve boyutlandır
                circular_pixmap = self.create_circular_pixmap(pixmap, 90)
                logo_label.setPixmap(circular_pixmap)
            else:
                # Logo yüklenemezse placeholder kullan
                logo_label.setText("Ö")
                logo_label.setStyleSheet("""
                    QLabel {
                        color: #2563eb;
                        font-size: 36px;
                        font-weight: 700;
                        background: transparent;
                        border: none;
                        border-radius: 45px;
                    }
                """)
        except Exception as e:
            print(f"Logo yükleme hatası: {e}")
            # Hata durumunda placeholder kullan
            logo_label.setText("Ö")
            logo_label.setStyleSheet("""
                QLabel {
                    color: #6366f1;
                    font-size: 36px;
                    font-weight: 700;
                    background: transparent;
                    border: none;
                    border-radius: 45px;
                }
            """)

        logo_layout.addWidget(logo_label)

        # Logo container'ı merkeze yerleştir
        logo_center_layout = QHBoxLayout()
        logo_center_layout.addStretch()
        logo_center_layout.addWidget(logo_container)
        logo_center_layout.addStretch()

        # Başlık ve alt başlık
        self.label_info = QLabel("Hoş Geldiniz")
        self.label_info.setAlignment(Qt.AlignCenter)
        self.label_info.setStyleSheet("""
            QLabel {
                color: #1e293b;
                font-size: 28px;
                font-weight: 600;
                background: transparent;
                border: none;
                margin-bottom: 5px;
            }
        """)

        subtitle_label = QLabel("Lütfen giriş bilgilerinizi giriniz")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 14px;
                font-weight: 300;
                background: transparent;
                border: none;
                margin-bottom: 10px;
            }
        """)

        header_layout.addLayout(logo_center_layout)
        header_layout.addWidget(self.label_info)
        header_layout.addWidget(subtitle_label)

        # Input fields
        input_layout = QVBoxLayout()
        input_layout.setSpacing(20)

        self.username_input = ModernLineEdit("👤 Kullanıcı Adı")
        self.password_input = ModernLineEdit("🔒 Şifre")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        input_layout.addWidget(self.username_input)
        input_layout.addWidget(self.password_input)

        # Buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(15)

        self.login_btn = ModernButton("Giriş Yap", primary=True)
        self.login_btn.clicked.connect(self.login)

        # Kayıt ol butonu kaldırıldı - sadece admin kullanıcı ekleyebilir
        # self.register_btn = ModernButton("Kayıt Ol", primary=False)
        # self.register_btn.clicked.connect(self.register)

        button_layout.addWidget(self.login_btn)
        # button_layout.addWidget(self.register_btn)

        # Footer
        footer_label = QLabel("Özege - Güvenli Giriş")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("""
            QLabel {
                color: #4c566a;
                font-size: 12px;
                background: transparent;
                border: none;
                margin-top: 20px;
            }
        """)

        # Add all sections to form
        form_layout.addLayout(header_layout)
        form_layout.addLayout(input_layout)
        form_layout.addLayout(button_layout)
        form_layout.addWidget(footer_label)

        main_layout.addWidget(form_frame)
        self.setLayout(main_layout)
    def setup_animations(self):
        # Form slide-in animation
        self.form_animation = QPropertyAnimation(self.layout().itemAt(0).widget(), b"geometry")
        self.form_animation.setDuration(800)
        self.form_animation.setEasingCurve(QEasingCurve.OutCubic)

        # Start animation after a short delay
        QTimer.singleShot(100, self.animate_form)

    def animate_form(self):
        form_widget = self.layout().itemAt(0).widget()
        current_geometry = form_widget.geometry()
        start_geometry = QRect(current_geometry.x(), current_geometry.y() + 50,
                               current_geometry.width(), current_geometry.height())

        self.form_animation.setStartValue(start_geometry)
        self.form_animation.setEndValue(current_geometry)
        self.form_animation.start()

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self.show_message("Hata", "Kullanıcı adı ve şifre boş olamaz!", "error")
            return

        # API'ye POST isteği gönder
        try:
            import requests

            url = api_url("login")
            data = {
                'username': username,
                'password': password
            }

            response = requests.post(url, json=data)
            response_data = response.json()

            if response.status_code == 200 and 'message' in response_data:
                # Kullanıcı bilgilerini sakla
                self.user_info = {
                    'user_id': response_data.get('user_id'),
                    'username': response_data.get('username'),
                    'role': response_data.get('role', 'normal'),
                    'bolge_kodlari': response_data.get('bolge_kodlari', []),
                    'default_bolge_kodu': response_data.get('default_bolge_kodu')
                }
                self.show_message("Başarılı", response_data['message'], "success")
                self.accept()  # Dialog'u kapat
            elif 'error' in response_data:
                self.show_message("Hata", response_data['error'], "error")
            else:
                self.show_message("Hata", "Bilinmeyen bir hata oluştu.", "error")

        except requests.exceptions.ConnectionError:
            self.show_message("Hata", "Sunucuya bağlanılamadı. Sunucunun çalıştığından emin olun.", "error")
        except requests.exceptions.RequestException as e:
            self.show_message("Hata", f"İstek hatası: {str(e)}", "error")
        except Exception as e:
            self.show_message("Hata", f"Beklenmeyen hata: {str(e)}", "error")

    def register(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self.show_message("Hata", "Kullanıcı adı ve şifre boş olamaz!", "error")
            return

        response = self.api_client.register(username, password)
        if 'message' in response:
            self.show_message("Başarılı", response['message'], "success")
        elif 'error' in response:
            self.show_message("Hata", response['error'], "error")
        else:
            self.show_message("Hata", "Bilinmeyen bir hata oluştu.", "error")

    def show_message(self, title, message, msg_type="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)

        # Kurumsal açık tema message box styling
        if msg_type == "success":
            msg.setStyleSheet("""
                QMessageBox {
                    background: #ffffff;
                    color: #1e293b;
                    border: 2px solid #10b981;
                    border-radius: 16px;
                    padding: 20px;
                }
                QMessageBox QLabel {
                    color: #1e293b;
                    font-size: 14px;
                    font-weight: 500;
                    background: transparent;
                }
                QMessageBox QPushButton {
                    background-color: #10b981 !important;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #10b981, stop:1 #059669) !important;
                    color: #000000 !important;
                    border: 2px solid #059669 !important;
                    border-radius: 10px;
                    padding: 12px 24px;
                    font-weight: 600;
                    font-size: 14px;
                    min-width: 100px;
                    min-height: 35px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #059669 !important;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #059669, stop:1 #047857) !important;
                    border-color: #047857 !important;
                    color: #000000 !important;
                    box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3);
                }
                QMessageBox QPushButton:pressed {
                    background-color: #047857 !important;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #047857, stop:1 #065f46) !important;
                    border-color: #065f46 !important;
                    color: #000000 !important;
                }
            """)
        elif msg_type == "error":
            msg.setStyleSheet("""
                QMessageBox {
                    background: #ffffff;
                    color: #1e293b;
                    border: 2px solid #ef4444;
                    border-radius: 16px;
                    padding: 20px;
                }
                QMessageBox QLabel {
                    color: #1e293b;
                    font-size: 14px;
                    font-weight: 500;
                    background: transparent;
                }
                QMessageBox QPushButton {
                    background-color: #ef4444 !important;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ef4444, stop:1 #dc2626) !important;
                    color: #000000 !important;
                    border: 2px solid #dc2626 !important;
                    border-radius: 10px;
                    padding: 12px 24px;
                    font-weight: 600;
                    font-size: 14px;
                    min-width: 100px;
                    min-height: 35px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #dc2626 !important;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #dc2626, stop:1 #b91c1c) !important;
                    border-color: #b91c1c !important;
                    color: #000000 !important;
                    box-shadow: 0 4px 8px rgba(239, 68, 68, 0.3);
                }
                QMessageBox QPushButton:pressed {
                    background-color: #b91c1c !important;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #b91c1c, stop:1 #991b1b) !important;
                    border-color: #991b1b !important;
                    color: #000000 !important;
                }
            """)
        else:
            msg.setStyleSheet("""
                QMessageBox {
                    background: #ffffff;
                    color: #1e293b;
                    border: 2px solid #3b82f6;
                    border-radius: 16px;
                    padding: 20px;
                }
                QMessageBox QLabel {
                    color: #1e293b;
                    font-size: 14px;
                    font-weight: 500;
                    background: transparent;
                }
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
            """)

        msg.exec()