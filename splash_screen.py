import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QApplication,
                             QProgressBar, QDesktopWidget, QWidget, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt5.QtGui import QFont, QPainter, QPen, QBrush, QLinearGradient, QColor, QPixmap
import os
import math


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class AnimatedProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(0)
        self.setTextVisible(False)
        self.setFixedHeight(8)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.setBrush(QBrush(QColor(255, 247, 237, 200)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 4, 4)

        # Progress
        if self.value() > 0:
            gradient = QLinearGradient(0, 0, self.width(), 0)
            gradient.setColorAt(0, QColor(59, 130, 246))  # Kurumsal Mavi
            gradient.setColorAt(0.5, QColor(37, 99, 235))  # Mavi
            gradient.setColorAt(1, QColor(29, 78, 216))  # Koyu Mavi

            painter.setBrush(QBrush(gradient))
            progress_width = int(self.width() * self.value() / 100)
            painter.drawRoundedRect(0, 0, progress_width, self.height(), 4, 4)


class LoadingSpinner(QWidget):
    """Kurumsal loading spinner widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_angle)
        self.timer.start(30)  # Smooth animation
        
    def update_angle(self):
        self.angle = (self.angle + 6) % 360
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = QPoint(self.width() // 2, self.height() // 2)
        radius = min(self.width(), self.height()) // 2 - 15
        
        # Dış halka - açık mavi arka plan
        pen = QPen(QColor(226, 232, 240), 10)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawEllipse(center.x() - radius, center.y() - radius, 
                           radius * 2, radius * 2)
        
        # Dönen halka segmentleri - kurumsal mavi gradient
        num_segments = 12
        for i in range(num_segments):
            segment_angle = (self.angle + i * (360 / num_segments)) % 360
            angle_rad = math.radians(segment_angle)
            
            # Alpha değeri - merkezden uzaklaştıkça azalır
            alpha = int(255 * (1 - i * 0.08))
            alpha = max(80, min(255, alpha))
            
            pen = QPen(QColor(59, 130, 246, alpha), 8)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            
            # Arc çizimi
            start_angle = int(segment_angle * 16)
            span_angle = int(30 * 16)  # Her segment 30 derece
            
            painter.drawArc(center.x() - radius, center.y() - radius,
                          radius * 2, radius * 2,
                          start_angle, span_angle)
        
        # İç logo alanı - beyaz daire
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(226, 232, 240), 2))
        inner_radius = radius - 25
        painter.drawEllipse(center.x() - inner_radius, center.y() - inner_radius,
                          inner_radius * 2, inner_radius * 2)
        
        # Logo metni
        painter.setPen(QPen(QColor(37, 99, 235), 1))
        font = QFont("Segoe UI", 18, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "ÖZ")


class GlowLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)

        # Glow effect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(59, 130, 246, 150))
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)


class SplashScreen(QDialog):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_char = 0
        self.full_text = "Özege — Tütünde Doğallığın ve Kalitenin Özünde!"
        self.typing_speed = 60
        self.progress_value = 0

        # Boyut aynı kalacak
        self.resize(750, 500)
        self.center_window()

        self.init_ui()
        self.setup_typing_effect()
        self.setup_progress_bar()
        self.setup_animations()

    def center_window(self):
        """Login screen ile aynı merkezleme fonksiyonu"""
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # Kurumsal ve Profesyonel tema
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:0.5 #ffffff, stop:1 #f1f3f5);
                border: 1px solid #3b82f6;
                border-radius: 20px;
            }
        """)

        # Main container
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        main_layout.setAlignment(Qt.AlignCenter)

        # Header section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(15)

        # Logo/Title with glow effect
        self.title_label = GlowLabel("ÖZEGE")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                font-size: 48px;
                font-weight: 700;
                font-family: 'Segoe UI', sans-serif;
                letter-spacing: 4px;
                background: transparent;
                padding: 20px;
            }
        """)

        # Subtitle
        self.subtitle_label = QLabel("Premium Tobacco Solutions")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 16px;
                font-weight: 300;
                letter-spacing: 2px;
                text-transform: uppercase;
                background: transparent;
            }
        """)

        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.subtitle_label)

        # Center section with loading spinner
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setSpacing(30)

        # Loading spinner container
        spinner_container = QWidget()
        spinner_container.setFixedSize(200, 200)
        spinner_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffffff, 
                    stop:0.5 #f8f9fa,
                    stop:1 #f1f3f5);
                border-radius: 20px;
                border: 2px solid #e5e7eb;
            }
        """)

        spinner_layout = QVBoxLayout(spinner_container)
        spinner_layout.setContentsMargins(40, 40, 40, 40)
        spinner_layout.setAlignment(Qt.AlignCenter)

        self.loading_spinner = LoadingSpinner()
        spinner_layout.addWidget(self.loading_spinner)

        center_layout.addWidget(spinner_container)

        # Status section
        status_layout = QVBoxLayout()
        status_layout.setSpacing(20)

        # Typing text
        self.text_label = QLabel("")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("""
            QLabel {
                color: #212529;
                font-size: 18px;
                font-weight: 400;
                padding: 15px;
                background: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 10px;
            }
        """)

        # Info label - Daha detaylı bilgi gösterimi
        self.info_label = QLabel("Sistem başlatılıyor...")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #2563eb;
                font-size: 15px;
                font-weight: 600;
                padding: 12px 20px;
                background: #eff6ff;
                border: 1px solid #bfdbfe;
                border-radius: 10px;
                min-height: 20px;
            }
        """)
        
        # Detaylı bilgi label'ı
        self.detail_label = QLabel("")
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 12px;
                font-weight: 400;
                padding: 8px;
                background: transparent;
            }
        """)

        # Custom progress bar
        progress_container = QWidget()
        progress_container.setFixedHeight(30)
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_bar = AnimatedProgressBar()

        # Progress percentage
        self.progress_label = QLabel("0%")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #2563eb;
                font-size: 12px;
                font-weight: 500;
                background: transparent;
                margin-top: 5px;
            }
        """)

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)

        status_layout.addWidget(self.text_label)
        status_layout.addWidget(self.info_label)
        status_layout.addWidget(self.detail_label)
        status_layout.addWidget(progress_container)

        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.setAlignment(Qt.AlignCenter)

        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("""
            QLabel {
                color: #2563eb;
                font-size: 12px;
                background: transparent;
                padding: 5px 15px;
                border: 1px solid #3b82f6;
                border-radius: 15px;
            }
        """)

        copyright_label = QLabel("Created by Münire Kutlum 2025")
        copyright_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 12px;
                background: transparent;
            }
        """)

        footer_layout.addWidget(version_label)
        footer_layout.addWidget(copyright_label)

        # Add all sections to main layout
        main_layout.addLayout(header_layout)
        main_layout.addLayout(center_layout)
        main_layout.addLayout(status_layout)
        main_layout.addStretch()
        main_layout.addLayout(footer_layout)

        self.setLayout(main_layout)
        self.show()

    def setup_animations(self):
        # Title fade-in animation
        self.title_animation = QPropertyAnimation(self.title_label, b"geometry")
        self.title_animation.setDuration(1000)
        self.title_animation.setEasingCurve(QEasingCurve.OutCubic)

        # Start title animation
        QTimer.singleShot(100, self.animate_title)

    def animate_title(self):
        current_geometry = self.title_label.geometry()
        start_geometry = QRect(current_geometry.x(), current_geometry.y() - 50,
                               current_geometry.width(), current_geometry.height())

        self.title_animation.setStartValue(start_geometry)
        self.title_animation.setEndValue(current_geometry)
        self.title_animation.start()

    def setup_typing_effect(self):
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.type_next_char)
        # Start typing after a short delay
        QTimer.singleShot(1500, lambda: self.typing_timer.start(self.typing_speed))

    def type_next_char(self):
        if self.current_char < len(self.full_text):
            current_text = self.full_text[:self.current_char + 1]
            display_text = current_text + ("_" if self.current_char % 2 == 0 else "")
            self.text_label.setText(display_text)
            self.current_char += 1
        else:
            self.text_label.setText(self.full_text)
            self.typing_timer.stop()

    def setup_progress_bar(self):
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        # Start progress after typing starts
        QTimer.singleShot(2000, lambda: self.progress_timer.start(40))

    def update_progress(self):
        self.progress_value += 1
        self.progress_bar.setValue(self.progress_value)
        self.progress_label.setText(f"{self.progress_value}%")

        # Update info text based on progress - Türkçe ve detaylı bilgi
        if self.progress_value < 15:
            self.info_label.setText("📦 Temel Modüller Yükleniyor...")
            self.detail_label.setText("Uygulama çekirdek bileşenleri başlatılıyor")
        elif self.progress_value < 30:
            self.info_label.setText("🔧 Sistem Bileşenleri Hazırlanıyor...")
            self.detail_label.setText("Arayüz ve iş mantığı modülleri yükleniyor")
        elif self.progress_value < 45:
            self.info_label.setText("💾 Veritabanı Bağlantısı Kuruluyor...")
            self.detail_label.setText("SQL Server bağlantısı test ediliyor")
        elif self.progress_value < 60:
            self.info_label.setText("🔐 Güvenlik Kontrolleri Yapılıyor...")
            self.detail_label.setText("Kullanıcı yetkilendirme sistemi hazırlanıyor")
        elif self.progress_value < 75:
            self.info_label.setText("📊 Veri Modelleri Yükleniyor...")
            self.detail_label.setText("Harcama ve masraf modülleri başlatılıyor")
        elif self.progress_value < 90:
            self.info_label.setText("🎨 Arayüz Hazırlanıyor...")
            self.detail_label.setText("Kurumsal tema ve stiller uygulanıyor")
        elif self.progress_value < 98:
            self.info_label.setText("✅ Son Kontroller Yapılıyor...")
            self.detail_label.setText("Sistem bütünlüğü kontrol ediliyor")
        else:
            self.info_label.setText("🚀 Hazır! Uygulama Başlatılıyor...")
            self.detail_label.setText("Hoş geldiniz! Sistem kullanıma hazır")

        if self.progress_value >= 100:
            self.progress_timer.stop()
            QTimer.singleShot(500, self.close_splash)

    def close_splash(self):
        self.finished.emit()
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_splash()
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.close_splash()
        super().mousePressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()
    sys.exit(app.exec_())