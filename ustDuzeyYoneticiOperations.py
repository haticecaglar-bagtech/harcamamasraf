from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QGroupBox, QGridLayout,
                             QTabWidget, QFrame, QScrollArea, QDesktopWidget, QSizePolicy,
                             QFileDialog)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
import requests
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import xlsxwriter
import os
from config import get_api_root


class UstDuzeyYoneticiTab(QWidget):
    def __init__(self, api_client, user_id, role, bolge_kodlari):
        super().__init__()
        self.api_client = api_client
        self.user_id = user_id
        self.role = role
        self.bolge_kodlari = bolge_kodlari
        
        # Ekran boyutunu algıla
        self.screen = QDesktopWidget().screenGeometry()
        self.is_mobile = self.screen.width() < 768
        self.is_tablet = 768 <= self.screen.width() < 1024
        
        self.setup_ui()
        self.load_data()
    
    def get_responsive_font_size(self, base_size, mobile_ratio=0.7, tablet_ratio=0.85):
        """Responsive font boyutu hesapla"""
        if self.is_mobile:
            return int(base_size * mobile_ratio)
        elif self.is_tablet:
            return int(base_size * tablet_ratio)
        return base_size
    
    def get_responsive_padding(self, base_padding, mobile_ratio=0.6, tablet_ratio=0.8):
        """Responsive padding hesapla"""
        if self.is_mobile:
            return int(base_padding * mobile_ratio)
        elif self.is_tablet:
            return int(base_padding * tablet_ratio)
        return base_padding
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Kurumsal başlık - Profesyonel Mavi Tonları
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e0e7ff, stop:0.5 #c7d2fe, stop:1 #3b82f6);
                border-radius: 16px;
                padding: 30px;
                border: 2px solid #3b82f6;
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
            }
        """)
        title_layout = QVBoxLayout(title_frame)
        title_layout.setSpacing(8)
        
        # Ana başlık - Responsive font boyutu
        title = QLabel("📊 YÖNETİCİ ANALİZ VE MALİYET PANELİ")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet("""
            font-size: clamp(20px, 4vw, 36px); 
            font-weight: 700; 
            color: #1e293b;
            padding: 10px;
            letter-spacing: 1px;
            text-transform: uppercase;
        """)
        
        # Alt başlık - Responsive font boyutu
        subtitle = QLabel("Detaylı Finansal Analiz ve Stratejik Raporlama Sistemi")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("""
            font-size: clamp(14px, 2vw, 18px); 
            color: #334155;
            padding: 5px;
            font-weight: 500;
            letter-spacing: 0.5px;
        """)
        
        # Tarih bilgisi
        date_label = QLabel(f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        date_label.setAlignment(Qt.AlignCenter)
        date_label.setStyleSheet("""
            font-size: 14px; 
            color: #475569;
            padding: 5px;
            font-weight: 400;
        """)
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_layout.addWidget(date_label)
        layout.addWidget(title_frame)
        
        # Kurumsal filtreler - Daha profesyonel görünüm
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border-radius: 16px;
                border: 2px solid #e2e8f0;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }
        """)
        filter_group = QGroupBox("🔍 FİLTRELEME VE ARAMA")
        filter_group.setStyleSheet("""
            QGroupBox {
                font-size: 20px;
                font-weight: 700;
                color: #2563eb;
                border: none;
                margin-top: 15px;
                letter-spacing: 0.5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background: #ffffff;
            }
        """)
        # Responsive filtre layout - Mobilde dikey, desktop'ta yatay
        if self.is_mobile:
            filter_layout = QVBoxLayout()
            filter_layout.setSpacing(10)
        else:
            filter_layout = QHBoxLayout()
            filter_layout.setSpacing(15)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        
        # Bölge seçimi - Responsive
        bolge_label = QLabel("🌍 Bölge:")
        font_size = self.get_responsive_font_size(15)
        bolge_label.setStyleSheet(f"font-weight: 600; color: #1e293b; font-size: {font_size}px;")
        filter_layout.addWidget(bolge_label)
        self.bolge_combo = QComboBox()
        padding = self.get_responsive_padding(10)
        self.bolge_combo.setStyleSheet(f"""
            QComboBox {{
                padding: {padding}px {int(padding*1.8)}px;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                background: #ffffff;
                font-size: {font_size}px;
                font-weight: 500;
                min-width: {'100px' if self.is_mobile else '150px'};
                max-width: {'100%' if self.is_mobile else '300px'};
                color: #212529;
            }}
            QComboBox:hover {{
                border-color: #3b82f6;
                background: #ffffff;
            }}
            QComboBox:focus {{
                border-color: #2563eb;
                background: #ffffff;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 35px;
                background: #f1f5f9;
                border-left: 1px solid #e2e8f0;
            }}
            QComboBox::drop-down:hover {{
                background: #e2e8f0;
            }}
        """)
        self.bolge_combo.addItem("Tümü", None)
        
        # Tüm bölgeleri yükle
        try:
            response = requests.get(f"{get_api_root()}/bolge_kodlari")
            if response.status_code == 200:
                bolge_kodlari_dict = response.json()
                for kod, ad in bolge_kodlari_dict.items():
                    self.bolge_combo.addItem(f"{ad} ({kod})", kod)
        except Exception as e:
            print(f"Bölge kodları yüklenirken hata: {e}")
        
        filter_layout.addWidget(self.bolge_combo)
        
        # Stage seçimi
        stage_label = QLabel("⚙️ Stage:")
        stage_label.setStyleSheet(f"font-weight: 600; color: #1e293b; font-size: {font_size}px;")
        filter_layout.addWidget(stage_label)
        self.stage_combo = QComboBox()
        self.stage_combo.setStyleSheet(self.bolge_combo.styleSheet())
        self.stage_combo.addItem("Tümü", None)
        filter_layout.addWidget(self.stage_combo)
        
        # Safha seçimi
        safha_label = QLabel("📋 Safha:")
        safha_label.setStyleSheet(f"font-weight: 600; color: #1e293b; font-size: {font_size}px;")
        filter_layout.addWidget(safha_label)
        self.safha_combo = QComboBox()
        self.safha_combo.setStyleSheet(self.bolge_combo.styleSheet())
        self.safha_combo.addItem("Tümü", None)
        filter_layout.addWidget(self.safha_combo)
        
        # Tarih aralığı
        tarih_label = QLabel("📅 Tarih:")
        tarih_label.setStyleSheet(f"font-weight: 600; color: #1e293b; font-size: {font_size}px;")
        filter_layout.addWidget(tarih_label)
        self.tarih_combo = QComboBox()
        self.tarih_combo.setStyleSheet(self.bolge_combo.styleSheet())
        self.tarih_combo.addItem("Tümü", None)
        self.tarih_combo.addItem("Son 7 Gün", 7)
        self.tarih_combo.addItem("Son 30 Gün", 30)
        self.tarih_combo.addItem("Son 90 Gün", 90)
        self.tarih_combo.addItem("Bu Ay", "this_month")
        self.tarih_combo.addItem("Geçen Ay", "last_month")
        filter_layout.addWidget(self.tarih_combo)
        
        if not self.is_mobile:
            filter_layout.addStretch()
        
        # Filtrele butonu - Responsive
        filter_btn = QPushButton("🔍 FİLTRELE")
        btn_font_size = self.get_responsive_font_size(15)
        btn_padding = self.get_responsive_padding(12)
        filter_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                padding: {btn_padding}px {int(btn_padding*2.5)}px;
                border-radius: 10px;
                font-weight: 700;
                font-size: {btn_font_size}px;
                min-width: {'100%' if self.is_mobile else '140px'};
                letter-spacing: 0.5px;
                border: 2px solid #2563eb;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 #1d4ed8);
                border-color: #1d4ed8;
                box-shadow: 0 4px 8px rgba(37, 99, 235, 0.3);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1d4ed8, stop:1 #1e40af);
                border-color: #1e40af;
            }}
        """)
        filter_btn.clicked.connect(self.apply_filters)
        filter_layout.addWidget(filter_btn)
        
        # Yenile butonu - Responsive
        refresh_btn = QPushButton("🔄 YENİLE")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #60a5fa, stop:1 #3b82f6);
                color: white;
                padding: {btn_padding}px {int(btn_padding*2.5)}px;
                border-radius: 10px;
                font-weight: 700;
                font-size: {btn_font_size}px;
                min-width: {'100%' if self.is_mobile else '140px'};
                letter-spacing: 0.5px;
                border: 2px solid #3b82f6;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #2563eb);
                border-color: #2563eb;
                box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 #1d4ed8);
                border-color: #1d4ed8;
            }}
        """)
        refresh_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(refresh_btn)
        
        filter_group.setLayout(filter_layout)
        filter_frame_layout = QVBoxLayout(filter_frame)
        filter_frame_layout.addWidget(filter_group)
        layout.addWidget(filter_frame)
        
        # Kurumsal Tab widget - Responsive
        self.tab_widget = QTabWidget()
        tab_font_size = self.get_responsive_font_size(15)
        tab_padding = self.get_responsive_padding(14)
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid #dee2e6;
                border-radius: 16px;
                background: #ffffff;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }}
            QTabBar::tab {{
                background: #f8f9fa;
                color: #495057;
                padding: {tab_padding}px {int(tab_padding*2)}px;
                margin-right: 4px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-size: {tab_font_size}px;
                font-weight: 600;
                border: 1px solid #dee2e6;
                border-bottom: none;
                letter-spacing: 0.3px;
                {'min-width: 80px;' if self.is_mobile else ''}
            }}
            QTabBar::tab:selected {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: #ffffff;
                border-color: #2563eb;
                font-weight: 700;
            }}
            QTabBar::tab:hover:!selected {{
                background: #e9ecef;
                color: #1e293b;
            }}
        """)
        # Mobilde tab'ları scrollable yap
        if self.is_mobile:
            self.tab_widget.setUsesScrollButtons(True)
        
        # Genel Özet sekmesi (Harcama + Masraf toplam)
        self.genel_ozet_tab = QWidget()
        self.setup_genel_ozet_tab()
        self.tab_widget.addTab(self.genel_ozet_tab, "🏠 Genel Özet")
        
        # Harcama Analizi sekmesi
        self.dashboard_tab = QWidget()
        self.setup_dashboard_tab()
        self.tab_widget.addTab(self.dashboard_tab, "💰 Harcama Analizi")
        
        # Masraf Analizi sekmesi
        self.masraf_tab = QWidget()
        self.setup_masraf_tab()
        self.tab_widget.addTab(self.masraf_tab, "💸 Masraf Analizi")
        
        # Grafikler sekmesi
        self.grafikler_tab = QWidget()
        self.setup_grafikler_tab()
        self.tab_widget.addTab(self.grafikler_tab, "📈 Detaylı Grafikler")
        
        # Maliyet Analizi sekmesi
        self.maliyet_tab = QWidget()
        self.setup_maliyet_tab()
        self.tab_widget.addTab(self.maliyet_tab, "📊 Maliyet Analizi")
        
        # Veri Tablosu sekmesi
        self.veri_tab = QWidget()
        self.setup_veri_tab()
        self.tab_widget.addTab(self.veri_tab, "📋 Veri Tablosu")
        
        layout.addWidget(self.tab_widget)
    
    def setup_genel_ozet_tab(self):
        """Genel özet sekmesi - Harcama ve Masraf toplam"""
        main_layout = QVBoxLayout(self.genel_ozet_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #f9fafb;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: #f9fafb;")
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(25)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Toplam KPI Kartları
        kpi_group = QGroupBox("📊 GENEL TOPLAM GÖSTERGELER")
        kpi_title_font = self.get_responsive_font_size(22)
        kpi_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {kpi_title_font}px;
                font-weight: 700;
                color: #2563eb;
                border: 2px solid #dee2e6;
                border-radius: 16px;
                margin-top: 20px;
                padding-top: 25px;
                background: #ffffff;
                letter-spacing: 0.5px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 15px;
                background: #ffffff;
            }}
        """)
        kpi_layout = QGridLayout()
        kpi_layout.setSpacing(15)
        kpi_layout.setContentsMargins(10, 10, 10, 10)
        
        # Responsive grid
        if self.is_mobile:
            kpi_cols = 1
        elif self.is_tablet:
            kpi_cols = 2
        else:
            kpi_cols = 2
        
        # Toplam Harcama KPI Kartı - Genişletilmiş
        harcama_card = QFrame()
        card_min_h = self.get_responsive_padding(180)  # 120'den 180'e artırıldı
        card_max_h = self.get_responsive_padding(280)  # 200'den 280'e artırıldı
        harcama_card.setMinimumHeight(card_min_h)
        harcama_card.setMaximumHeight(card_max_h)
        card_padding = self.get_responsive_padding(30)  # 20'den 30'a artırıldı
        harcama_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                border-radius: 12px;
                padding: {card_padding}px;
            }}
        """)
        harcama_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        harcama_layout = QVBoxLayout(harcama_card)
        harcama_layout.setSpacing(15)  # Spacing eklendi
        harcama_layout.setContentsMargins(10, 10, 10, 10)  # İç margin eklendi
        harcama_icon = QLabel("💰")
        icon_size = self.get_responsive_font_size(40)  # 32'den 40'a artırıldı
        harcama_icon.setStyleSheet(f"font-size: {icon_size}px; padding-bottom: 5px;")
        harcama_icon.setAlignment(Qt.AlignCenter)
        harcama_layout.addWidget(harcama_icon)
        harcama_title = QLabel("Toplam Harcama")
        title_size = self.get_responsive_font_size(16)  # 14'ten 16'ya artırıldı
        harcama_title.setStyleSheet(f"font-size: {title_size}px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        harcama_title.setAlignment(Qt.AlignCenter)
        harcama_title.setWordWrap(True)
        harcama_layout.addWidget(harcama_title)
        self.genel_harcama_label = QLabel("0 ₺")
        value_size = self.get_responsive_font_size(36)  # 28'den 36'ya artırıldı
        self.genel_harcama_label.setStyleSheet(f"font-size: {value_size}px; font-weight: bold; color: white; padding-top: 10px;")
        self.genel_harcama_label.setAlignment(Qt.AlignCenter)
        self.genel_harcama_label.setWordWrap(True)
        harcama_layout.addWidget(self.genel_harcama_label)
        kpi_layout.addWidget(harcama_card, 0, 0)
        
        # Toplam Masraf KPI Kartı - Genişletilmiş
        masraf_card = QFrame()
        masraf_card.setMinimumHeight(card_min_h)
        masraf_card.setMaximumHeight(card_max_h)
        masraf_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #10b981, stop:1 #059669);
                border-radius: 12px;
                padding: {card_padding}px;
            }}
        """)
        masraf_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        masraf_layout = QVBoxLayout(masraf_card)
        masraf_layout.setSpacing(15)  # Spacing eklendi
        masraf_layout.setContentsMargins(10, 10, 10, 10)  # İç margin eklendi
        masraf_icon = QLabel("💸")
        masraf_icon.setStyleSheet(f"font-size: {icon_size}px; padding-bottom: 5px;")
        masraf_icon.setAlignment(Qt.AlignCenter)
        masraf_layout.addWidget(masraf_icon)
        masraf_title = QLabel("Toplam Masraf")
        masraf_title.setStyleSheet(f"font-size: {title_size}px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        masraf_title.setAlignment(Qt.AlignCenter)
        masraf_title.setWordWrap(True)
        masraf_layout.addWidget(masraf_title)
        self.genel_masraf_label = QLabel("0 ₺")
        self.genel_masraf_label.setStyleSheet(f"font-size: {value_size}px; font-weight: bold; color: white; padding-top: 10px;")
        self.genel_masraf_label.setAlignment(Qt.AlignCenter)
        self.genel_masraf_label.setWordWrap(True)
        masraf_layout.addWidget(self.genel_masraf_label)
        kpi_layout.addWidget(masraf_card, 0, 1 if kpi_cols >= 2 else 0)
        
        kpi_group.setLayout(kpi_layout)
        layout.addWidget(kpi_group)
        
        # Harcama ve Masraf Dağılım Grafiği
        dagilim_group = QGroupBox("📊 HARCAMA VE MASRAF DAĞILIMI")
        dagilim_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {kpi_title_font}px;
                font-weight: 700;
                color: #2563eb;
                border: 2px solid #dee2e6;
                border-radius: 16px;
                margin-top: 20px;
                padding-top: 25px;
                background: #ffffff;
                letter-spacing: 0.5px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 15px;
                background: #ffffff;
            }}
        """)
        dagilim_layout = QVBoxLayout()
        dagilim_layout.setContentsMargins(20, 15, 20, 20)
        dagilim_layout.setSpacing(15)
        
        # Responsive grafik boyutları
        if self.is_mobile:
            fig_width, fig_height = 8, 8
            canvas_min_h, canvas_max_h = 300, 500
        elif self.is_tablet:
            fig_width, fig_height = 10, 10
            canvas_min_h, canvas_max_h = 400, 600
        else:
            fig_width, fig_height = 12, 12
            canvas_min_h, canvas_max_h = 500, 700
        
        self.genel_dagilim_figure = Figure(figsize=(fig_width, fig_height), facecolor='white', dpi=100)
        self.genel_dagilim_canvas = FigureCanvas(self.genel_dagilim_figure)
        self.genel_dagilim_canvas.setMinimumHeight(canvas_min_h)
        self.genel_dagilim_canvas.setMaximumHeight(canvas_max_h)
        self.genel_dagilim_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        dagilim_layout.addWidget(self.genel_dagilim_canvas)
        dagilim_group.setLayout(dagilim_layout)
        layout.addWidget(dagilim_group)
        
        layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
    
    def setup_dashboard_tab(self):
        """Harcama analizi dashboard sekmesi"""
        main_layout = QVBoxLayout(self.dashboard_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #f9fafb;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: #f9fafb;")
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(25)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Kurumsal KPI Kartları - Responsive Grid
        kpi_group = QGroupBox("📊 TEMEL GÖSTERGELER VE KPI'LAR")
        kpi_title_font = self.get_responsive_font_size(22)
        kpi_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {kpi_title_font}px;
                font-weight: 700;
                color: #2563eb;
                border: 2px solid #dee2e6;
                border-radius: 16px;
                margin-top: 20px;
                padding-top: 25px;
                background: #ffffff;
                letter-spacing: 0.5px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 15px;
                background: #ffffff;
            }}
        """)
        kpi_layout = QGridLayout()
        kpi_layout.setSpacing(15)
        kpi_layout.setContentsMargins(10, 10, 10, 10)
        
        # Responsive grid: Mobilde 1 sütun, tablette 2, desktop'ta 3
        if self.is_mobile:
            kpi_cols = 1
        elif self.is_tablet:
            kpi_cols = 2
        else:
            kpi_cols = 3
        
        # Toplam Tutar KPI Kartı - Genişletilmiş
        total_card = QFrame()
        card_min_h = self.get_responsive_padding(180)  # 120'den 180'e artırıldı
        card_max_h = self.get_responsive_padding(280)  # 200'den 280'e artırıldı
        total_card.setMinimumHeight(card_min_h)
        total_card.setMaximumHeight(card_max_h)
        card_padding = self.get_responsive_padding(30)  # 20'den 30'a artırıldı
        total_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #10b981, stop:1 #059669);
                border-radius: 12px;
                padding: {card_padding}px;
            }}
        """)
        total_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        total_layout = QVBoxLayout(total_card)
        total_layout.setSpacing(15)  # Spacing eklendi
        total_layout.setContentsMargins(10, 10, 10, 10)  # İç margin eklendi
        total_icon = QLabel("💰")
        icon_size = self.get_responsive_font_size(40)  # 32'den 40'a artırıldı
        total_icon.setStyleSheet(f"font-size: {icon_size}px; padding-bottom: 5px;")
        total_icon.setAlignment(Qt.AlignCenter)
        total_layout.addWidget(total_icon)
        total_title = QLabel("Toplam Tutar")
        title_size = self.get_responsive_font_size(16)  # 14'ten 16'ya artırıldı
        total_title.setStyleSheet(f"font-size: {title_size}px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        total_title.setAlignment(Qt.AlignCenter)
        total_title.setWordWrap(True)
        total_layout.addWidget(total_title)
        self.total_label = QLabel("0 ₺")
        value_size = self.get_responsive_font_size(36)  # 28'den 36'ya artırıldı
        self.total_label.setStyleSheet(f"font-size: {value_size}px; font-weight: bold; color: white; padding-top: 10px;")
        self.total_label.setAlignment(Qt.AlignCenter)
        self.total_label.setWordWrap(True)
        total_layout.addWidget(self.total_label)
        kpi_layout.addWidget(total_card, 0, 0)
        
        # Toplam Kayıt KPI Kartı - Genişletilmiş
        count_card = QFrame()
        count_card.setMinimumHeight(card_min_h)
        count_card.setMaximumHeight(card_max_h)
        count_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                border-radius: 12px;
                padding: {card_padding}px;
            }}
        """)
        count_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        count_layout = QVBoxLayout(count_card)
        count_layout.setSpacing(15)  # Spacing eklendi
        count_layout.setContentsMargins(10, 10, 10, 10)  # İç margin eklendi
        count_icon = QLabel("📊")
        count_icon.setStyleSheet(f"font-size: {icon_size}px; padding-bottom: 5px;")
        count_icon.setAlignment(Qt.AlignCenter)
        count_layout.addWidget(count_icon)
        count_title = QLabel("Toplam Kayıt")
        count_title.setStyleSheet(f"font-size: {title_size}px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        count_title.setAlignment(Qt.AlignCenter)
        count_title.setWordWrap(True)
        count_layout.addWidget(count_title)
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet(f"font-size: {value_size}px; font-weight: bold; color: white; padding-top: 10px;")
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setWordWrap(True)
        count_layout.addWidget(self.count_label)
        kpi_layout.addWidget(count_card, 0, 1 if kpi_cols >= 2 else 0, 1, 1)
        
        # Ortalama Tutar KPI Kartı - Genişletilmiş
        avg_card = QFrame()
        avg_card.setMinimumHeight(card_min_h)
        avg_card.setMaximumHeight(card_max_h)
        avg_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f59e0b, stop:1 #d97706);
                border-radius: 12px;
                padding: {card_padding}px;
            }}
        """)
        avg_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        avg_layout = QVBoxLayout(avg_card)
        avg_layout.setSpacing(15)  # Spacing eklendi
        avg_layout.setContentsMargins(10, 10, 10, 10)  # İç margin eklendi
        avg_icon = QLabel("📈")
        avg_icon.setStyleSheet(f"font-size: {icon_size}px; padding-bottom: 5px;")
        avg_icon.setAlignment(Qt.AlignCenter)
        avg_layout.addWidget(avg_icon)
        avg_title = QLabel("Ortalama Tutar")
        avg_title.setStyleSheet(f"font-size: {title_size}px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        avg_title.setAlignment(Qt.AlignCenter)
        avg_title.setWordWrap(True)
        avg_layout.addWidget(avg_title)
        self.avg_label = QLabel("0 ₺")
        self.avg_label.setStyleSheet(f"font-size: {value_size}px; font-weight: bold; color: white; padding-top: 10px;")
        self.avg_label.setAlignment(Qt.AlignCenter)
        self.avg_label.setWordWrap(True)
        avg_layout.addWidget(self.avg_label)
        # Responsive grid positioning
        if kpi_cols >= 3:
            kpi_layout.addWidget(avg_card, 0, 2)
        elif kpi_cols == 2:
            kpi_layout.addWidget(avg_card, 1, 0)
        else:
            kpi_layout.addWidget(avg_card, 2, 0)
        
        # Maksimum Tutar KPI Kartı - Genişletilmiş
        max_card = QFrame()
        max_card.setMinimumHeight(card_min_h)
        max_card.setMaximumHeight(card_max_h)
        max_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ec4899, stop:1 #db2777);
                border-radius: 12px;
                padding: {card_padding}px;
            }}
        """)
        max_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        max_layout = QVBoxLayout(max_card)
        max_layout.setSpacing(15)  # Spacing eklendi
        max_layout.setContentsMargins(10, 10, 10, 10)  # İç margin eklendi
        max_icon = QLabel("⬆️")
        max_icon.setStyleSheet(f"font-size: {icon_size}px; padding-bottom: 5px;")
        max_icon.setAlignment(Qt.AlignCenter)
        max_layout.addWidget(max_icon)
        max_title = QLabel("Maksimum Tutar")
        max_title.setStyleSheet(f"font-size: {title_size}px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        max_title.setAlignment(Qt.AlignCenter)
        max_title.setWordWrap(True)
        max_layout.addWidget(max_title)
        self.max_label = QLabel("0 ₺")
        self.max_label.setStyleSheet(f"font-size: {value_size}px; font-weight: bold; color: white; padding-top: 10px;")
        self.max_label.setAlignment(Qt.AlignCenter)
        self.max_label.setWordWrap(True)
        max_layout.addWidget(self.max_label)
        # Responsive grid positioning
        if kpi_cols >= 3:
            kpi_layout.addWidget(max_card, 1, 0)
        elif kpi_cols == 2:
            kpi_layout.addWidget(max_card, 1, 1)
        else:
            kpi_layout.addWidget(max_card, 3, 0)
        
        # Minimum Tutar KPI Kartı - Genişletilmiş
        min_card = QFrame()
        min_card.setMinimumHeight(card_min_h)
        min_card.setMaximumHeight(card_max_h)
        min_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8b5cf6, stop:1 #7c3aed);
                border-radius: 12px;
                padding: {card_padding}px;
            }}
        """)
        min_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        min_layout = QVBoxLayout(min_card)
        min_layout.setSpacing(15)  # Spacing eklendi
        min_layout.setContentsMargins(10, 10, 10, 10)  # İç margin eklendi
        min_icon = QLabel("⬇️")
        min_icon.setStyleSheet(f"font-size: {icon_size}px; padding-bottom: 5px;")
        min_icon.setAlignment(Qt.AlignCenter)
        min_layout.addWidget(min_icon)
        min_title = QLabel("Minimum Tutar")
        min_title.setStyleSheet(f"font-size: {title_size}px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        min_title.setAlignment(Qt.AlignCenter)
        min_title.setWordWrap(True)
        min_layout.addWidget(min_title)
        self.min_label = QLabel("0 ₺")
        self.min_label.setStyleSheet(f"font-size: {value_size}px; font-weight: bold; color: white; padding-top: 10px;")
        self.min_label.setAlignment(Qt.AlignCenter)
        self.min_label.setWordWrap(True)
        min_layout.addWidget(self.min_label)
        # Responsive grid positioning
        if kpi_cols >= 3:
            kpi_layout.addWidget(min_card, 1, 1)
        elif kpi_cols == 2:
            kpi_layout.addWidget(min_card, 2, 0)
        else:
            kpi_layout.addWidget(min_card, 4, 0)
        
        # Standart Sapma KPI Kartı - Genişletilmiş
        std_card = QFrame()
        std_card.setMinimumHeight(card_min_h)
        std_card.setMaximumHeight(card_max_h)
        std_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #06b6d4, stop:1 #0891b2);
                border-radius: 12px;
                padding: {card_padding}px;
            }}
        """)
        std_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        std_layout = QVBoxLayout(std_card)
        std_layout.setSpacing(15)  # Spacing eklendi
        std_layout.setContentsMargins(10, 10, 10, 10)  # İç margin eklendi
        std_icon = QLabel("📉")
        std_icon.setStyleSheet(f"font-size: {icon_size}px; padding-bottom: 5px;")
        std_icon.setAlignment(Qt.AlignCenter)
        std_layout.addWidget(std_icon)
        std_title = QLabel("Standart Sapma")
        std_title.setStyleSheet(f"font-size: {title_size}px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        std_title.setAlignment(Qt.AlignCenter)
        std_title.setWordWrap(True)
        std_layout.addWidget(std_title)
        self.std_label = QLabel("0 ₺")
        self.std_label.setStyleSheet(f"font-size: {value_size}px; font-weight: bold; color: white; padding-top: 10px;")
        self.std_label.setAlignment(Qt.AlignCenter)
        self.std_label.setWordWrap(True)
        std_layout.addWidget(self.std_label)
        # Responsive grid positioning
        if kpi_cols >= 3:
            kpi_layout.addWidget(std_card, 1, 2)
        elif kpi_cols == 2:
            kpi_layout.addWidget(std_card, 2, 1)
        else:
            kpi_layout.addWidget(std_card, 5, 0)
        
        kpi_group.setLayout(kpi_layout)
        layout.addWidget(kpi_group)
        
        # Bölge bazlı özet grafik
        bolge_group = QGroupBox("🌍 Bölge Bazlı Özet")
        bolge_group.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                color: #2563eb;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 25px;
                padding-bottom: 15px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }
        """)
        bolge_layout = QVBoxLayout()
        bolge_layout.setContentsMargins(20, 15, 20, 20)
        bolge_layout.setSpacing(15)
        
        # Bölge bazlı özet için filtre ve Excel butonları
        bolge_filter_layout = QHBoxLayout()
        bolge_filter_layout.setSpacing(10)
        
        bolge_filter_label = QLabel("🔍 Filtre:")
        bolge_filter_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #495057;")
        bolge_filter_layout.addWidget(bolge_filter_label)
        
        self.bolge_dashboard_bolge_combo = QComboBox()
        self.bolge_dashboard_bolge_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
                background: white;
                min-width: 150px;
            }
        """)
        self.bolge_dashboard_bolge_combo.addItem("Tümü", None)
        try:
            response = requests.get(f"{get_api_root()}/bolge_kodlari")
            if response.status_code == 200:
                bolge_kodlari_dict = response.json()
                for kod, ad in bolge_kodlari_dict.items():
                    self.bolge_dashboard_bolge_combo.addItem(f"{ad} ({kod})", kod)
        except Exception as e:
            print(f"Bölge kodları yüklenirken hata: {e}")
        bolge_filter_layout.addWidget(self.bolge_dashboard_bolge_combo)
        
        bolge_filter_layout.addStretch()
        
        # Excel'e aktar butonu
        bolge_excel_button = QPushButton("📊 Excel'e Aktar")
        bolge_excel_button.setStyleSheet("""
            QPushButton {
                background-color: #10b981 !important;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #059669) !important;
                color: #000000 !important;
                border: 2px solid #059669 !important;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #059669 !important;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #047857) !important;
                border-color: #047857 !important;
                color: #000000 !important;
            }
        """)
        bolge_excel_button.clicked.connect(self.export_bolge_dashboard_to_excel)
        bolge_filter_layout.addWidget(bolge_excel_button)
        
        # Filtre uygula butonu
        bolge_filter_button = QPushButton("🔍 Filtrele")
        bolge_filter_button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6 !important;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #2563eb) !important;
                color: #000000 !important;
                border: 2px solid #2563eb !important;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563eb !important;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 #1d4ed8) !important;
                border-color: #1d4ed8 !important;
                color: #000000 !important;
            }
        """)
        bolge_filter_button.clicked.connect(self.apply_bolge_dashboard_filter)
        bolge_filter_layout.addWidget(bolge_filter_button)
        
        bolge_layout.addLayout(bolge_filter_layout)
        # Responsive grafik boyutları
        if self.is_mobile:
            fig_width, fig_height = 8, 5
            canvas_min_h, canvas_max_h = 200, 400
        elif self.is_tablet:
            fig_width, fig_height = 10, 6
            canvas_min_h, canvas_max_h = 250, 500
        else:
            fig_width, fig_height = 14, 7
            canvas_min_h, canvas_max_h = 300, 600
        
        self.bolge_dashboard_figure = Figure(figsize=(fig_width, fig_height), facecolor='white', dpi=100)
        self.bolge_dashboard_canvas = FigureCanvas(self.bolge_dashboard_figure)
        self.bolge_dashboard_canvas.setMinimumHeight(canvas_min_h)
        self.bolge_dashboard_canvas.setMaximumHeight(canvas_max_h)
        self.bolge_dashboard_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bolge_layout.addWidget(self.bolge_dashboard_canvas)
        bolge_group.setLayout(bolge_layout)
        layout.addWidget(bolge_group)
        
        # Stage bazlı özet grafik - Kurumsal stil
        stage_group = QGroupBox("⚙️ STAGE BAZLI ANALİZ VE ÖZET")
        stage_group.setStyleSheet(bolge_group.styleSheet())
        stage_layout = QVBoxLayout()
        stage_layout.setContentsMargins(20, 15, 20, 20)
        stage_layout.setSpacing(15)
        self.stage_dashboard_figure = Figure(figsize=(fig_width, fig_height), facecolor='white', dpi=100)
        self.stage_dashboard_canvas = FigureCanvas(self.stage_dashboard_figure)
        self.stage_dashboard_canvas.setMinimumHeight(canvas_min_h)
        self.stage_dashboard_canvas.setMaximumHeight(canvas_max_h)
        self.stage_dashboard_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        stage_layout.addWidget(self.stage_dashboard_canvas)
        stage_group.setLayout(stage_layout)
        layout.addWidget(stage_group)
        
        layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
    
    def setup_masraf_tab(self):
        """Masraf analizi sekmesi"""
        main_layout = QVBoxLayout(self.masraf_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #f9fafb;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: #f9fafb;")
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(25)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Masraf KPI Kartları
        kpi_group = QGroupBox("📊 MASRAF GÖSTERGELERİ VE KPI'LAR")
        kpi_title_font = self.get_responsive_font_size(22)
        kpi_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {kpi_title_font}px;
                font-weight: 700;
                color: #2563eb;
                border: 2px solid #dee2e6;
                border-radius: 16px;
                margin-top: 20px;
                padding-top: 25px;
                background: #ffffff;
                letter-spacing: 0.5px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 15px;
                background: #ffffff;
            }}
        """)
        kpi_layout = QGridLayout()
        kpi_layout.setSpacing(15)
        kpi_layout.setContentsMargins(10, 10, 10, 10)
        
        # Responsive grid
        if self.is_mobile:
            kpi_cols = 1
        elif self.is_tablet:
            kpi_cols = 2
        else:
            kpi_cols = 3
        
        card_min_h = self.get_responsive_padding(180)  # 120'den 180'e artırıldı
        card_max_h = self.get_responsive_padding(280)  # 200'den 280'e artırıldı
        card_padding = self.get_responsive_padding(30)  # 20'den 30'a artırıldı
        icon_size = self.get_responsive_font_size(40)  # 32'den 40'a artırıldı
        title_size = self.get_responsive_font_size(16)  # 14'ten 16'ya artırıldı
        value_size = self.get_responsive_font_size(36)  # 28'den 36'ya artırıldı
        
        # Toplam Masraf KPI Kartı - Genişletilmiş
        masraf_total_card = QFrame()
        masraf_total_card.setMinimumHeight(card_min_h)
        masraf_total_card.setMaximumHeight(card_max_h)
        masraf_total_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #10b981, stop:1 #059669);
                border-radius: 12px;
                padding: {card_padding}px;
            }}
        """)
        masraf_total_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        masraf_total_layout = QVBoxLayout(masraf_total_card)
        masraf_total_layout.setSpacing(15)  # Spacing eklendi
        masraf_total_layout.setContentsMargins(10, 10, 10, 10)  # İç margin eklendi
        masraf_total_icon = QLabel("💸")
        masraf_total_icon.setStyleSheet(f"font-size: {icon_size}px; padding-bottom: 5px;")
        masraf_total_icon.setAlignment(Qt.AlignCenter)
        masraf_total_layout.addWidget(masraf_total_icon)
        masraf_total_title = QLabel("Toplam Masraf")
        masraf_total_title.setStyleSheet(f"font-size: {title_size}px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        masraf_total_title.setAlignment(Qt.AlignCenter)
        masraf_total_title.setWordWrap(True)
        masraf_total_layout.addWidget(masraf_total_title)
        self.masraf_total_label = QLabel("0 ₺")
        self.masraf_total_label.setStyleSheet(f"font-size: {value_size}px; font-weight: bold; color: white; padding-top: 10px;")
        self.masraf_total_label.setAlignment(Qt.AlignCenter)
        self.masraf_total_label.setWordWrap(True)
        masraf_total_layout.addWidget(self.masraf_total_label)
        kpi_layout.addWidget(masraf_total_card, 0, 0)
        
        # Masraf Kayıt Sayısı KPI Kartı - Genişletilmiş
        masraf_count_card = QFrame()
        masraf_count_card.setMinimumHeight(card_min_h)
        masraf_count_card.setMaximumHeight(card_max_h)
        masraf_count_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                border-radius: 12px;
                padding: {card_padding}px;
            }}
        """)
        masraf_count_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        masraf_count_layout = QVBoxLayout(masraf_count_card)
        masraf_count_layout.setSpacing(15)  # Spacing eklendi
        masraf_count_layout.setContentsMargins(10, 10, 10, 10)  # İç margin eklendi
        masraf_count_icon = QLabel("📊")
        masraf_count_icon.setStyleSheet(f"font-size: {icon_size}px; padding-bottom: 5px;")
        masraf_count_icon.setAlignment(Qt.AlignCenter)
        masraf_count_layout.addWidget(masraf_count_icon)
        masraf_count_title = QLabel("Toplam Kayıt")
        masraf_count_title.setStyleSheet(f"font-size: {title_size}px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        masraf_count_title.setAlignment(Qt.AlignCenter)
        masraf_count_title.setWordWrap(True)
        masraf_count_layout.addWidget(masraf_count_title)
        self.masraf_count_label = QLabel("0")
        self.masraf_count_label.setStyleSheet(f"font-size: {value_size}px; font-weight: bold; color: white; padding-top: 10px;")
        self.masraf_count_label.setAlignment(Qt.AlignCenter)
        self.masraf_count_label.setWordWrap(True)
        masraf_count_layout.addWidget(self.masraf_count_label)
        kpi_layout.addWidget(masraf_count_card, 0, 1 if kpi_cols >= 2 else 0)
        
        # Ortalama Masraf KPI Kartı - Genişletilmiş
        masraf_avg_card = QFrame()
        masraf_avg_card.setMinimumHeight(card_min_h)
        masraf_avg_card.setMaximumHeight(card_max_h)
        masraf_avg_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f59e0b, stop:1 #d97706);
                border-radius: 12px;
                padding: {card_padding}px;
            }}
        """)
        masraf_avg_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        masraf_avg_layout = QVBoxLayout(masraf_avg_card)
        masraf_avg_layout.setSpacing(15)  # Spacing eklendi
        masraf_avg_layout.setContentsMargins(10, 10, 10, 10)  # İç margin eklendi
        masraf_avg_icon = QLabel("📈")
        masraf_avg_icon.setStyleSheet(f"font-size: {icon_size}px; padding-bottom: 5px;")
        masraf_avg_icon.setAlignment(Qt.AlignCenter)
        masraf_avg_layout.addWidget(masraf_avg_icon)
        masraf_avg_title = QLabel("Ortalama Masraf")
        masraf_avg_title.setStyleSheet(f"font-size: {title_size}px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        masraf_avg_title.setAlignment(Qt.AlignCenter)
        masraf_avg_title.setWordWrap(True)
        masraf_avg_layout.addWidget(masraf_avg_title)
        self.masraf_avg_label = QLabel("0 ₺")
        self.masraf_avg_label.setStyleSheet(f"font-size: {value_size}px; font-weight: bold; color: white; padding-top: 10px;")
        self.masraf_avg_label.setAlignment(Qt.AlignCenter)
        self.masraf_avg_label.setWordWrap(True)
        masraf_avg_layout.addWidget(self.masraf_avg_label)
        if kpi_cols >= 3:
            kpi_layout.addWidget(masraf_avg_card, 0, 2)
        elif kpi_cols == 2:
            kpi_layout.addWidget(masraf_avg_card, 1, 0)
        else:
            kpi_layout.addWidget(masraf_avg_card, 2, 0)
        
        kpi_group.setLayout(kpi_layout)
        layout.addWidget(kpi_group)
        
        # Bölge bazlı masraf grafiği
        bolge_masraf_group = QGroupBox("🌍 Bölge Bazlı Masraf Özeti")
        bolge_masraf_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 18px;
                font-weight: bold;
                color: #2563eb;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 25px;
                padding-bottom: 15px;
                background: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }}
        """)
        bolge_masraf_layout = QVBoxLayout()
        bolge_masraf_layout.setContentsMargins(20, 15, 20, 20)
        bolge_masraf_layout.setSpacing(15)
        
        # Responsive grafik boyutları
        if self.is_mobile:
            fig_width, fig_height = 8, 5
            canvas_min_h, canvas_max_h = 200, 400
        elif self.is_tablet:
            fig_width, fig_height = 10, 6
            canvas_min_h, canvas_max_h = 250, 500
        else:
            fig_width, fig_height = 14, 7
            canvas_min_h, canvas_max_h = 300, 600
        
        self.masraf_bolge_figure = Figure(figsize=(fig_width, fig_height), facecolor='white', dpi=100)
        self.masraf_bolge_canvas = FigureCanvas(self.masraf_bolge_figure)
        self.masraf_bolge_canvas.setMinimumHeight(canvas_min_h)
        self.masraf_bolge_canvas.setMaximumHeight(canvas_max_h)
        self.masraf_bolge_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bolge_masraf_layout.addWidget(self.masraf_bolge_canvas)
        bolge_masraf_group.setLayout(bolge_masraf_layout)
        layout.addWidget(bolge_masraf_group)
        
        # Stage bazlı masraf grafiği
        stage_masraf_group = QGroupBox("⚙️ STAGE BAZLI MASRAF ANALİZİ")
        stage_masraf_group.setStyleSheet(bolge_masraf_group.styleSheet())
        stage_masraf_layout = QVBoxLayout()
        stage_masraf_layout.setContentsMargins(20, 15, 20, 20)
        stage_masraf_layout.setSpacing(15)
        self.masraf_stage_figure = Figure(figsize=(fig_width, fig_height), facecolor='white', dpi=100)
        self.masraf_stage_canvas = FigureCanvas(self.masraf_stage_figure)
        self.masraf_stage_canvas.setMinimumHeight(canvas_min_h)
        self.masraf_stage_canvas.setMaximumHeight(canvas_max_h)
        self.masraf_stage_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        stage_masraf_layout.addWidget(self.masraf_stage_canvas)
        stage_masraf_group.setLayout(stage_masraf_layout)
        layout.addWidget(stage_masraf_group)
        
        layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
    
    def setup_grafikler_tab(self):
        """Detaylı grafikler sekmesi"""
        main_layout = QVBoxLayout(self.grafikler_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #f9fafb;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: #f9fafb;")
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(25)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Responsive grafik boyutları
        if self.is_mobile:
            fig_width, fig_height = 8, 5
            canvas_min_h, canvas_max_h = 200, 400
        elif self.is_tablet:
            fig_width, fig_height = 10, 6
            canvas_min_h, canvas_max_h = 250, 500
        else:
            fig_width, fig_height = 12, 7
            canvas_min_h, canvas_max_h = 300, 600
        
        # Grafikler için responsive grid layout
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Responsive grid: Mobilde 1 sütun, tablette 1, desktop'ta 2
        if self.is_mobile:
            graph_cols = 1
        else:
            graph_cols = 2
        
        # Modern grup box stili
        group_style = """
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2563eb;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 25px;
                padding-bottom: 15px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }
        """
        
        # Bölge bazlı toplam tutar grafiği
        bolge_group = QGroupBox("🌍 Bölge Bazlı Toplam Tutar")
        bolge_group.setStyleSheet(group_style)
        bolge_layout = QVBoxLayout()
        bolge_layout.setContentsMargins(20, 15, 20, 20)
        bolge_layout.setSpacing(15)
        self.bolge_figure = Figure(figsize=(fig_width, fig_height), facecolor='white', dpi=100)
        self.bolge_canvas = FigureCanvas(self.bolge_figure)
        self.bolge_canvas.setMinimumHeight(canvas_min_h)
        self.bolge_canvas.setMaximumHeight(canvas_max_h)
        self.bolge_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bolge_layout.addWidget(self.bolge_canvas)
        bolge_group.setLayout(bolge_layout)
        grid_layout.addWidget(bolge_group, 0, 0)
        
        # Stage bazlı toplam tutar grafiği
        stage_group = QGroupBox("⚙️ Stage Bazlı Toplam Tutar")
        stage_group.setStyleSheet(group_style)
        stage_layout = QVBoxLayout()
        stage_layout.setContentsMargins(20, 15, 20, 20)
        stage_layout.setSpacing(15)
        self.stage_figure = Figure(figsize=(fig_width, fig_height), facecolor='white', dpi=100)
        self.stage_canvas = FigureCanvas(self.stage_figure)
        self.stage_canvas.setMinimumHeight(canvas_min_h)
        self.stage_canvas.setMaximumHeight(canvas_max_h)
        self.stage_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        stage_layout.addWidget(self.stage_canvas)
        stage_group.setLayout(stage_layout)
        if graph_cols >= 2:
            grid_layout.addWidget(stage_group, 0, 1)
        else:
            grid_layout.addWidget(stage_group, 1, 0)
        
        # Safha bazlı pasta grafiği
        safha_group = QGroupBox("📊 Safha Bazlı Dağılım")
        safha_group.setStyleSheet(group_style)
        safha_layout = QVBoxLayout()
        safha_layout.setContentsMargins(20, 15, 20, 20)
        safha_layout.setSpacing(15)
        self.safha_figure = Figure(figsize=(fig_width, fig_height), facecolor='white', dpi=100)
        self.safha_canvas = FigureCanvas(self.safha_figure)
        self.safha_canvas.setMinimumHeight(canvas_min_h)
        self.safha_canvas.setMaximumHeight(canvas_max_h)
        self.safha_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        safha_layout.addWidget(self.safha_canvas)
        safha_group.setLayout(safha_layout)
        if graph_cols >= 2:
            grid_layout.addWidget(safha_group, 1, 0)
        else:
            grid_layout.addWidget(safha_group, 2, 0)
        
        # Operasyon bazlı grafik
        operasyon_group = QGroupBox("🔧 Operasyon Bazlı Toplam Tutar (İlk 10)")
        operasyon_group.setStyleSheet(group_style)
        operasyon_layout = QVBoxLayout()
        operasyon_layout.setContentsMargins(20, 15, 20, 20)
        operasyon_layout.setSpacing(15)
        self.operasyon_figure = Figure(figsize=(fig_width, fig_height), facecolor='white', dpi=100)
        self.operasyon_canvas = FigureCanvas(self.operasyon_figure)
        self.operasyon_canvas.setMinimumHeight(canvas_min_h)
        self.operasyon_canvas.setMaximumHeight(canvas_max_h)
        self.operasyon_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        operasyon_layout.addWidget(self.operasyon_canvas)
        operasyon_group.setLayout(operasyon_layout)
        if graph_cols >= 2:
            grid_layout.addWidget(operasyon_group, 1, 1)
        else:
            grid_layout.addWidget(operasyon_group, 3, 0)
        
        # Tarih bazlı trend grafiği
        trend_group = QGroupBox("📅 Tarih Bazlı Trend Analizi")
        trend_group.setStyleSheet(group_style)
        trend_layout = QVBoxLayout()
        trend_layout.setContentsMargins(20, 15, 20, 20)
        trend_layout.setSpacing(15)
        trend_fig_width = 16 if not self.is_mobile else 10
        self.trend_figure = Figure(figsize=(trend_fig_width, fig_height), facecolor='white', dpi=100)
        self.trend_canvas = FigureCanvas(self.trend_figure)
        self.trend_canvas.setMinimumHeight(canvas_min_h)
        self.trend_canvas.setMaximumHeight(canvas_max_h)
        self.trend_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        trend_layout.addWidget(self.trend_canvas)
        trend_group.setLayout(trend_layout)
        if graph_cols >= 2:
            grid_layout.addWidget(trend_group, 2, 0, 1, 2)
        else:
            grid_layout.addWidget(trend_group, 4, 0)
        
        # Kaynak tipi bazlı grafik
        kaynak_group = QGroupBox("💼 Kaynak Tipi Bazlı Dağılım")
        kaynak_group.setStyleSheet(group_style)
        kaynak_layout = QVBoxLayout()
        kaynak_layout.setContentsMargins(20, 15, 20, 20)
        kaynak_layout.setSpacing(15)
        self.kaynak_figure = Figure(figsize=(fig_width, fig_height), facecolor='white', dpi=100)
        self.kaynak_canvas = FigureCanvas(self.kaynak_figure)
        self.kaynak_canvas.setMinimumHeight(canvas_min_h)
        self.kaynak_canvas.setMaximumHeight(canvas_max_h)
        self.kaynak_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        kaynak_layout.addWidget(self.kaynak_canvas)
        kaynak_group.setLayout(kaynak_layout)
        if graph_cols >= 2:
            grid_layout.addWidget(kaynak_group, 3, 0)
        else:
            grid_layout.addWidget(kaynak_group, 5, 0)
        
        # Birim bazlı grafik
        birim_group = QGroupBox("📦 Birim Bazlı Analiz")
        birim_group.setStyleSheet(group_style)
        birim_layout = QVBoxLayout()
        birim_layout.setContentsMargins(20, 15, 20, 20)
        birim_layout.setSpacing(15)
        self.birim_figure = Figure(figsize=(fig_width, fig_height), facecolor='white', dpi=100)
        self.birim_canvas = FigureCanvas(self.birim_figure)
        self.birim_canvas.setMinimumHeight(canvas_min_h)
        self.birim_canvas.setMaximumHeight(canvas_max_h)
        self.birim_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        birim_layout.addWidget(self.birim_canvas)
        birim_group.setLayout(birim_layout)
        if graph_cols >= 2:
            grid_layout.addWidget(birim_group, 3, 1)
        else:
            grid_layout.addWidget(birim_group, 6, 0)
        
        layout.addLayout(grid_layout)
        layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
    
    def setup_maliyet_tab(self):
        """Maliyet analizi sekmesi"""
        main_layout = QVBoxLayout(self.maliyet_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #f9fafb;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: #f9fafb;")
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(25)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Modern Maliyet özeti kartları
        maliyet_ozet_group = QGroupBox("💰 Maliyet Özeti")
        maliyet_ozet_group.setStyleSheet("""
            QGroupBox {
                font-size: 20px;
                font-weight: bold;
                color: #2563eb;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 20px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }
        """)
        maliyet_ozet_layout = QGridLayout()
        maliyet_ozet_layout.setSpacing(15)
        
        # Toplam Maliyet KPI Kartı - Genişletilmiş
        toplam_maliyet_card = QFrame()
        toplam_maliyet_card.setMinimumHeight(self.get_responsive_padding(180))
        toplam_maliyet_card.setMaximumHeight(self.get_responsive_padding(280))
        toplam_maliyet_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #dc2626, stop:1 #b91c1c);
                border-radius: 12px;
                padding: 30px;
            }
        """)
        toplam_maliyet_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toplam_maliyet_layout = QVBoxLayout(toplam_maliyet_card)
        toplam_maliyet_layout.setSpacing(15)
        toplam_maliyet_layout.setContentsMargins(10, 10, 10, 10)
        toplam_maliyet_icon = QLabel("💸")
        toplam_maliyet_icon.setStyleSheet("font-size: 40px; padding-bottom: 5px;")
        toplam_maliyet_icon.setAlignment(Qt.AlignCenter)
        toplam_maliyet_layout.addWidget(toplam_maliyet_icon)
        toplam_maliyet_title = QLabel("Toplam Maliyet")
        toplam_maliyet_title.setStyleSheet("font-size: 16px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        toplam_maliyet_title.setAlignment(Qt.AlignCenter)
        toplam_maliyet_title.setWordWrap(True)
        toplam_maliyet_layout.addWidget(toplam_maliyet_title)
        self.toplam_maliyet_label = QLabel("0 ₺")
        self.toplam_maliyet_label.setStyleSheet("font-size: 36px; font-weight: bold; color: white; padding-top: 10px;")
        self.toplam_maliyet_label.setAlignment(Qt.AlignCenter)
        self.toplam_maliyet_label.setWordWrap(True)
        toplam_maliyet_layout.addWidget(self.toplam_maliyet_label)
        maliyet_ozet_layout.addWidget(toplam_maliyet_card, 0, 0)
        
        # Birim Maliyet KPI Kartı - Genişletilmiş
        birim_maliyet_card = QFrame()
        birim_maliyet_card.setMinimumHeight(self.get_responsive_padding(180))
        birim_maliyet_card.setMaximumHeight(self.get_responsive_padding(280))
        birim_maliyet_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                border-radius: 12px;
                padding: 30px;
            }
        """)
        birim_maliyet_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        birim_maliyet_layout = QVBoxLayout(birim_maliyet_card)
        birim_maliyet_layout.setSpacing(15)
        birim_maliyet_layout.setContentsMargins(10, 10, 10, 10)
        birim_maliyet_icon = QLabel("📊")
        birim_maliyet_icon.setStyleSheet("font-size: 40px; padding-bottom: 5px;")
        birim_maliyet_icon.setAlignment(Qt.AlignCenter)
        birim_maliyet_layout.addWidget(birim_maliyet_icon)
        birim_maliyet_title = QLabel("Birim Başına Ortalama")
        birim_maliyet_title.setStyleSheet("font-size: 16px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        birim_maliyet_title.setAlignment(Qt.AlignCenter)
        birim_maliyet_title.setWordWrap(True)
        birim_maliyet_layout.addWidget(birim_maliyet_title)
        self.birim_maliyet_label = QLabel("0 ₺")
        self.birim_maliyet_label.setStyleSheet("font-size: 36px; font-weight: bold; color: white; padding-top: 10px;")
        self.birim_maliyet_label.setAlignment(Qt.AlignCenter)
        self.birim_maliyet_label.setWordWrap(True)
        birim_maliyet_layout.addWidget(self.birim_maliyet_label)
        maliyet_ozet_layout.addWidget(birim_maliyet_card, 0, 1)
        
        # En Yüksek Maliyet KPI Kartı - Genişletilmiş
        en_yuksek_card = QFrame()
        en_yuksek_card.setMinimumHeight(self.get_responsive_padding(180))
        en_yuksek_card.setMaximumHeight(self.get_responsive_padding(280))
        en_yuksek_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f59e0b, stop:1 #d97706);
                border-radius: 12px;
                padding: 30px;
            }
        """)
        en_yuksek_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        en_yuksek_layout = QVBoxLayout(en_yuksek_card)
        en_yuksek_layout.setSpacing(15)
        en_yuksek_layout.setContentsMargins(10, 10, 10, 10)
        en_yuksek_icon = QLabel("⬆️")
        en_yuksek_icon.setStyleSheet("font-size: 40px; padding-bottom: 5px;")
        en_yuksek_icon.setAlignment(Qt.AlignCenter)
        en_yuksek_layout.addWidget(en_yuksek_icon)
        en_yuksek_title = QLabel("En Yüksek Maliyetli Bölge")
        en_yuksek_title.setStyleSheet("font-size: 16px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        en_yuksek_title.setAlignment(Qt.AlignCenter)
        en_yuksek_title.setWordWrap(True)
        en_yuksek_layout.addWidget(en_yuksek_title)
        self.en_yuksek_maliyet_label = QLabel("-")
        self.en_yuksek_maliyet_label.setStyleSheet("font-size: 32px; font-weight: bold; color: white; padding-top: 10px;")
        self.en_yuksek_maliyet_label.setAlignment(Qt.AlignCenter)
        self.en_yuksek_maliyet_label.setWordWrap(True)
        en_yuksek_layout.addWidget(self.en_yuksek_maliyet_label)
        maliyet_ozet_layout.addWidget(en_yuksek_card, 1, 0)
        
        # En Düşük Maliyet KPI Kartı - Genişletilmiş
        en_dusuk_card = QFrame()
        en_dusuk_card.setMinimumHeight(self.get_responsive_padding(180))
        en_dusuk_card.setMaximumHeight(self.get_responsive_padding(280))
        en_dusuk_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #10b981, stop:1 #059669);
                border-radius: 12px;
                padding: 30px;
            }
        """)
        en_dusuk_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        en_dusuk_layout = QVBoxLayout(en_dusuk_card)
        en_dusuk_layout.setSpacing(15)
        en_dusuk_layout.setContentsMargins(10, 10, 10, 10)
        en_dusuk_icon = QLabel("⬇️")
        en_dusuk_icon.setStyleSheet("font-size: 40px; padding-bottom: 5px;")
        en_dusuk_icon.setAlignment(Qt.AlignCenter)
        en_dusuk_layout.addWidget(en_dusuk_icon)
        en_dusuk_title = QLabel("En Düşük Maliyetli Bölge")
        en_dusuk_title.setStyleSheet("font-size: 16px; color: rgba(255,255,255,0.9); font-weight: normal; padding: 8px 0px;")
        en_dusuk_title.setAlignment(Qt.AlignCenter)
        en_dusuk_title.setWordWrap(True)
        en_dusuk_layout.addWidget(en_dusuk_title)
        self.en_dusuk_maliyet_label = QLabel("-")
        self.en_dusuk_maliyet_label.setStyleSheet("font-size: 32px; font-weight: bold; color: white; padding-top: 10px;")
        self.en_dusuk_maliyet_label.setAlignment(Qt.AlignCenter)
        self.en_dusuk_maliyet_label.setWordWrap(True)
        en_dusuk_layout.addWidget(self.en_dusuk_maliyet_label)
        maliyet_ozet_layout.addWidget(en_dusuk_card, 1, 1)
        
        maliyet_ozet_group.setLayout(maliyet_ozet_layout)
        layout.addWidget(maliyet_ozet_group)
        
        # Modern grup box stili
        maliyet_group_style = """
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                color: #2563eb;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 20px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }
        """
        
        # Modern grup box stili
        maliyet_group_style = """
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                color: #2563eb;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 25px;
                padding-bottom: 15px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }
        """
        
        # Bölge bazlı maliyet karşılaştırması
        bolge_maliyet_group = QGroupBox("🌍 Bölge Bazlı Maliyet Karşılaştırması")
        bolge_maliyet_group.setStyleSheet(maliyet_group_style)
        bolge_maliyet_layout = QVBoxLayout()
        bolge_maliyet_layout.setContentsMargins(20, 15, 20, 20)
        bolge_maliyet_layout.setSpacing(15)
        maliyet_fig_width = 16 if not self.is_mobile else 10
        maliyet_fig_height = 8 if not self.is_mobile else 5
        maliyet_canvas_min_h = 300 if not self.is_mobile else 200
        maliyet_canvas_max_h = 700 if not self.is_mobile else 500
        self.bolge_maliyet_figure = Figure(figsize=(maliyet_fig_width, maliyet_fig_height), facecolor='white', dpi=100)
        self.bolge_maliyet_canvas = FigureCanvas(self.bolge_maliyet_figure)
        self.bolge_maliyet_canvas.setMinimumHeight(maliyet_canvas_min_h)
        self.bolge_maliyet_canvas.setMaximumHeight(maliyet_canvas_max_h)
        self.bolge_maliyet_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bolge_maliyet_layout.addWidget(self.bolge_maliyet_canvas)
        bolge_maliyet_group.setLayout(bolge_maliyet_layout)
        layout.addWidget(bolge_maliyet_group)
        
        # Stage bazlı maliyet analizi
        stage_maliyet_group = QGroupBox("⚙️ Stage Bazlı Maliyet Analizi")
        stage_maliyet_group.setStyleSheet(maliyet_group_style)
        stage_maliyet_layout = QVBoxLayout()
        stage_maliyet_layout.setContentsMargins(20, 15, 20, 20)
        stage_maliyet_layout.setSpacing(15)
        self.stage_maliyet_figure = Figure(figsize=(maliyet_fig_width, maliyet_fig_height), facecolor='white', dpi=100)
        self.stage_maliyet_canvas = FigureCanvas(self.stage_maliyet_figure)
        self.stage_maliyet_canvas.setMinimumHeight(maliyet_canvas_min_h)
        self.stage_maliyet_canvas.setMaximumHeight(maliyet_canvas_max_h)
        self.stage_maliyet_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        stage_maliyet_layout.addWidget(self.stage_maliyet_canvas)
        stage_maliyet_group.setLayout(stage_maliyet_layout)
        layout.addWidget(stage_maliyet_group)
        
        # Operasyon bazlı maliyet analizi
        operasyon_maliyet_group = QGroupBox("🔧 Operasyon Bazlı Maliyet Analizi (Top 15)")
        operasyon_maliyet_group.setStyleSheet(maliyet_group_style)
        operasyon_maliyet_layout = QVBoxLayout()
        operasyon_maliyet_layout.setContentsMargins(20, 15, 20, 20)
        operasyon_maliyet_layout.setSpacing(15)
        operasyon_fig_height = 10 if not self.is_mobile else 6
        operasyon_canvas_max_h = 800 if not self.is_mobile else 500
        self.operasyon_maliyet_figure = Figure(figsize=(maliyet_fig_width, operasyon_fig_height), facecolor='white', dpi=100)
        self.operasyon_maliyet_canvas = FigureCanvas(self.operasyon_maliyet_figure)
        self.operasyon_maliyet_canvas.setMinimumHeight(maliyet_canvas_min_h)
        self.operasyon_maliyet_canvas.setMaximumHeight(operasyon_canvas_max_h)
        self.operasyon_maliyet_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        operasyon_maliyet_layout.addWidget(self.operasyon_maliyet_canvas)
        operasyon_maliyet_group.setLayout(operasyon_maliyet_layout)
        layout.addWidget(operasyon_maliyet_group)
        
        # Tarih bazlı maliyet trendi
        trend_maliyet_group = QGroupBox("📅 Tarih Bazlı Maliyet Trendi")
        trend_maliyet_group.setStyleSheet(maliyet_group_style)
        trend_maliyet_layout = QVBoxLayout()
        trend_maliyet_layout.setContentsMargins(20, 15, 20, 20)
        trend_maliyet_layout.setSpacing(15)
        self.trend_maliyet_figure = Figure(figsize=(maliyet_fig_width, operasyon_fig_height), facecolor='white', dpi=100)
        self.trend_maliyet_canvas = FigureCanvas(self.trend_maliyet_figure)
        self.trend_maliyet_canvas.setMinimumHeight(maliyet_canvas_min_h)
        self.trend_maliyet_canvas.setMaximumHeight(operasyon_canvas_max_h)
        self.trend_maliyet_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        trend_maliyet_layout.addWidget(self.trend_maliyet_canvas)
        trend_maliyet_group.setLayout(trend_maliyet_layout)
        layout.addWidget(trend_maliyet_group)
        
        layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
    
    def setup_veri_tab(self):
        """Veri tablosu sekmesi"""
        main_layout = QVBoxLayout(self.veri_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area ekle
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #f9fafb;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: #f9fafb;")
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Filtre ve Excel butonları
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 2px solid #e5e7eb;
                padding: 15px;
            }
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setSpacing(10)
        
        # Filtre başlığı
        filter_label = QLabel("🔍 Filtreler:")
        filter_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #1e293b;")
        filter_layout.addWidget(filter_label)
        
        # Bölge filtresi
        bolge_label = QLabel("Bölge:")
        bolge_label.setStyleSheet("font-size: 12px; color: #495057;")
        filter_layout.addWidget(bolge_label)
        self.veri_bolge_combo = QComboBox()
        self.veri_bolge_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
                background: white;
                min-width: 150px;
            }
        """)
        self.veri_bolge_combo.addItem("Tümü", None)
        try:
            response = requests.get(f"{get_api_root()}/bolge_kodlari")
            if response.status_code == 200:
                bolge_kodlari_dict = response.json()
                for kod, ad in bolge_kodlari_dict.items():
                    self.veri_bolge_combo.addItem(f"{ad} ({kod})", kod)
        except Exception as e:
            print(f"Bölge kodları yüklenirken hata: {e}")
        filter_layout.addWidget(self.veri_bolge_combo)
        
        # Stage filtresi
        stage_label = QLabel("Stage:")
        stage_label.setStyleSheet("font-size: 12px; color: #495057;")
        filter_layout.addWidget(stage_label)
        self.veri_stage_combo = QComboBox()
        self.veri_stage_combo.setStyleSheet(self.veri_bolge_combo.styleSheet())
        self.veri_stage_combo.addItem("Tümü", None)
        filter_layout.addWidget(self.veri_stage_combo)
        
        # Safha filtresi
        safha_label = QLabel("Safha:")
        safha_label.setStyleSheet("font-size: 12px; color: #495057;")
        filter_layout.addWidget(safha_label)
        self.veri_safha_combo = QComboBox()
        self.veri_safha_combo.setStyleSheet(self.veri_bolge_combo.styleSheet())
        self.veri_safha_combo.addItem("Tümü", None)
        filter_layout.addWidget(self.veri_safha_combo)
        
        filter_layout.addStretch()
        
        # Excel'e aktar butonu
        excel_button = QPushButton("📊 Excel'e Aktar")
        excel_button.setStyleSheet("""
            QPushButton {
                background-color: #10b981 !important;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #059669) !important;
                color: #000000 !important;
                border: 2px solid #059669 !important;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #059669 !important;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #047857) !important;
                border-color: #047857 !important;
                color: #000000 !important;
            }
        """)
        excel_button.clicked.connect(self.export_veri_to_excel)
        filter_layout.addWidget(excel_button)
        
        # Filtre uygula butonu
        filter_button = QPushButton("🔍 Filtrele")
        filter_button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6 !important;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #2563eb) !important;
                color: #000000 !important;
                border: 2px solid #2563eb !important;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563eb !important;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 #1d4ed8) !important;
                border-color: #1d4ed8 !important;
                color: #000000 !important;
            }
        """)
        filter_button.clicked.connect(self.apply_veri_filters)
        filter_layout.addWidget(filter_button)
        
        layout.addWidget(filter_frame)
        
        # Modern özet istatistikler
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 2px solid #e5e7eb;
            }
        """)
        stats_group = QGroupBox("📊 Özet İstatistikler")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                color: #2563eb;
                border: none;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)
        
        # Modern istatistik kartları
        total_card_table = QFrame()
        total_card_table.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #10b981, stop:1 #059669);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        total_layout_table = QVBoxLayout(total_card_table)
        total_title_table = QLabel("Toplam Tutar")
        total_title_table.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.9);")
        total_layout_table.addWidget(total_title_table)
        self.total_label_table = QLabel("0 ₺")
        self.total_label_table.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        total_layout_table.addWidget(self.total_label_table)
        stats_layout.addWidget(total_card_table, 0, 0)
        
        count_card_table = QFrame()
        count_card_table.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #fb923c, stop:1 #f97316);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        count_layout_table = QVBoxLayout(count_card_table)
        count_title_table = QLabel("Toplam Kayıt")
        count_title_table.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.9);")
        count_layout_table.addWidget(count_title_table)
        self.count_label_table = QLabel("0")
        self.count_label_table.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        count_layout_table.addWidget(self.count_label_table)
        stats_layout.addWidget(count_card_table, 0, 1)
        
        avg_card_table = QFrame()
        avg_card_table.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f59e0b, stop:1 #d97706);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        avg_layout_table = QVBoxLayout(avg_card_table)
        avg_title_table = QLabel("Ortalama Tutar")
        avg_title_table.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.9);")
        avg_layout_table.addWidget(avg_title_table)
        self.avg_label_table = QLabel("0 ₺")
        self.avg_label_table.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        avg_layout_table.addWidget(self.avg_label_table)
        stats_layout.addWidget(avg_card_table, 1, 0)
        
        max_card_table = QFrame()
        max_card_table.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ec4899, stop:1 #db2777);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        max_layout_table = QVBoxLayout(max_card_table)
        max_title_table = QLabel("Maksimum Tutar")
        max_title_table.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.9);")
        max_layout_table.addWidget(max_title_table)
        self.max_label_table = QLabel("0 ₺")
        self.max_label_table.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        max_layout_table.addWidget(self.max_label_table)
        stats_layout.addWidget(max_card_table, 1, 1)
        
        stats_group.setLayout(stats_layout)
        stats_frame_layout = QVBoxLayout(stats_frame)
        stats_frame_layout.addWidget(stats_group)
        layout.addWidget(stats_frame)
        
        # Modern veri tablosu
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 2px solid #e5e7eb;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(10, 10, 10, 10)
        table_layout.setSpacing(0)
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(13)
        self.data_table.setHorizontalHeaderLabels([
            "No", "Tarih", "BÖLGE KODU", "KAYNAK TİPİ KODU", "STAGE KODU",
            "STAGE-OPERASYON KODU", "Safha", "Harcama Kalemi", "Birim",
            "Miktar", "Birim ücret", "Toplam", "Açıklama"
        ])
        table_font_size = self.get_responsive_font_size(12)
        self.data_table.setStyleSheet(f"""
            QTableWidget {{
                background: white;
                border: none;
                gridline-color: #e5e7eb;
                font-size: {table_font_size}px;
                min-height: 400px;
            }}
            QTableWidget::item {{
                padding: {self.get_responsive_padding(8)}px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background: #dbeafe;
                color: #2563eb;
            }}
            QHeaderView::section {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                padding: {self.get_responsive_padding(10)}px;
                border: none;
                font-weight: bold;
                font-size: {self.get_responsive_font_size(13)}px;
            }}
        """)
        # Mobilde horizontal scroll, desktop'ta stretch
        if self.is_mobile:
            self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.data_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Sadece görüntüleme
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setMinimumHeight(400)  # Minimum yükseklik ayarla
        self.data_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table_layout.addWidget(self.data_table)
        layout.addWidget(table_frame)
        
        # Stretch kaldırıldı - tablo görünürlüğünü engelleyebilir
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        # Veri tablosu için veri saklama
        self.veri_table_data = []
        # Bölge bazlı özet için veri saklama
        self.bolge_dashboard_data = pd.DataFrame()
    
    def load_data(self):
        """Verileri yükle ve grafikleri güncelle - Hem harcama hem masraf"""
        try:
            # Filtre parametrelerini hazırla
            params = {'user_id': self.user_id}
            
            bolge_kodu = self.bolge_combo.currentData()
            if bolge_kodu:
                params['bolge_kodu'] = bolge_kodu
            
            safha = self.safha_combo.currentData()
            if safha:
                params['safha'] = safha
            
            stage_kodu = self.stage_combo.currentData()
            if stage_kodu:
                params['stage_kodu'] = stage_kodu
            
            # Harcama verilerini yükle
            url_harcama = f"{get_api_root()}/harcama_talep"
            response_harcama = requests.get(url_harcama, params=params)
            
            df_harcama = pd.DataFrame()
            if response_harcama.status_code == 200:
                data = response_harcama.json()
                if data.get('success'):
                    expenses = data.get('data', [])
                    df_harcama = pd.DataFrame(expenses)
                    
                    # Tarih filtresini uygula
                    tarih_filtre = self.tarih_combo.currentData()
                    if tarih_filtre:
                        df_harcama = self.apply_date_filter(df_harcama, tarih_filtre)
                    
                    # Harcama grafiklerini güncelle
                    self.update_charts(df_harcama)
                    
                    # Harcama istatistiklerini güncelle
                    self.update_statistics(df_harcama)
                    
                    # Harcama maliyet analizlerini güncelle
                    self.update_maliyet_analysis(df_harcama)
                    
                    # Filtre seçeneklerini güncelle
                    self.update_filter_options(expenses)
            
            # Masraf verilerini yükle
            url_masraf = f"{get_api_root()}/get_expenses"
            response_masraf = requests.get(url_masraf, params=params)
            
            df_masraf = pd.DataFrame()
            if response_masraf.status_code == 200:
                data_masraf = response_masraf.json()
                if data_masraf.get('success'):
                    expenses_masraf = data_masraf.get('data', []) or data_masraf.get('expenses', [])
                    if expenses_masraf:
                        df_masraf = pd.DataFrame(expenses_masraf)
                        # Masraf için tarih filtresini uygula
                        if 'tarih' in df_masraf.columns and not df_masraf.empty:
                            tarih_filtre = self.tarih_combo.currentData()
                            if tarih_filtre:
                                df_masraf = self.apply_date_filter(df_masraf, tarih_filtre)
                    
                    # Masraf grafiklerini güncelle
                    self.update_masraf_charts(df_masraf)
                    
                    # Masraf istatistiklerini güncelle
                    self.update_masraf_statistics(df_masraf)
            
            # Genel özet grafiğini güncelle
            self.update_genel_ozet(df_harcama, df_masraf)
            
            # Tabloyu güncelle (harcama verileri ile)
            self.update_table(df_harcama)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata oluştu: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def apply_date_filter(self, df, filter_type):
        """Tarih filtresini uygula"""
        if df.empty or 'tarih' not in df.columns:
            return df
        
        try:
            df['tarih'] = pd.to_datetime(df['tarih'])
            today = datetime.now()
            
            if filter_type == 'this_month':
                start_date = today.replace(day=1)
                return df[df['tarih'] >= start_date]
            elif filter_type == 'last_month':
                first_day_this_month = today.replace(day=1)
                last_day_last_month = first_day_this_month - timedelta(days=1)
                start_date = last_day_last_month.replace(day=1)
                end_date = last_day_last_month
                return df[(df['tarih'] >= start_date) & (df['tarih'] <= end_date)]
            elif isinstance(filter_type, int):
                start_date = today - timedelta(days=filter_type)
                return df[df['tarih'] >= start_date]
        except Exception as e:
            print(f"Tarih filtresi uygulanırken hata: {e}")
        
        return df
    
    def update_table(self, df):
        """Veri tablosunu güncelle"""
        # Veriyi sakla (filtreleme ve Excel için)
        self.veri_table_data = df.copy() if not df.empty else pd.DataFrame()
        
        self.data_table.setRowCount(len(df))
        
        for row_idx, (_, row) in enumerate(df.iterrows()):
            self.data_table.setItem(row_idx, 0, QTableWidgetItem(str(row.get('no', ''))))
            self.data_table.setItem(row_idx, 1, QTableWidgetItem(str(row.get('tarih', ''))))
            self.data_table.setItem(row_idx, 2, QTableWidgetItem(str(row.get('bolge_kodu', ''))))
            self.data_table.setItem(row_idx, 3, QTableWidgetItem(str(row.get('kaynak_tipi_kodu', ''))))
            self.data_table.setItem(row_idx, 4, QTableWidgetItem(str(row.get('stage_kodu', ''))))
            self.data_table.setItem(row_idx, 5, QTableWidgetItem(str(row.get('stage_operasyon_kodu', ''))))
            self.data_table.setItem(row_idx, 6, QTableWidgetItem(str(row.get('safha', ''))))
            self.data_table.setItem(row_idx, 7, QTableWidgetItem(str(row.get('harcama_kalemi', ''))))
            self.data_table.setItem(row_idx, 8, QTableWidgetItem(str(row.get('birim', ''))))
            self.data_table.setItem(row_idx, 9, QTableWidgetItem(str(row.get('miktar', ''))))
            self.data_table.setItem(row_idx, 10, QTableWidgetItem(str(row.get('birim_ucret', ''))))
            self.data_table.setItem(row_idx, 11, QTableWidgetItem(str(row.get('toplam', ''))))
            self.data_table.setItem(row_idx, 12, QTableWidgetItem(str(row.get('aciklama', ''))))
    
    def apply_veri_filters(self):
        """Veri tablosu için filtreleri uygula"""
        try:
            params = {'user_id': self.user_id}
            
            bolge_kodu = self.veri_bolge_combo.currentData()
            if bolge_kodu:
                params['bolge_kodu'] = bolge_kodu
            
            safha = self.veri_safha_combo.currentData()
            if safha:
                params['safha'] = safha
            
            stage_kodu = self.veri_stage_combo.currentData()
            if stage_kodu:
                params['stage_kodu'] = stage_kodu
            
            # Harcama verilerini yükle
            url_harcama = f"{get_api_root()}/harcama_talep"
            response_harcama = requests.get(url_harcama, params=params)
            
            df_harcama = pd.DataFrame()
            if response_harcama.status_code == 200:
                data = response_harcama.json()
                if data.get('success'):
                    expenses = data.get('data', [])
                    df_harcama = pd.DataFrame(expenses)
            
            # Tabloyu güncelle
            self.update_table(df_harcama)
            
            # Filtre seçeneklerini güncelle
            if not df_harcama.empty:
                # Stage seçeneklerini güncelle
                self.veri_stage_combo.clear()
                self.veri_stage_combo.addItem("Tümü", None)
                if 'stage_kodu' in df_harcama.columns:
                    stages = df_harcama['stage_kodu'].dropna().unique()
                    for stage in sorted(stages):
                        self.veri_stage_combo.addItem(str(stage), stage)
                
                # Safha seçeneklerini güncelle
                self.veri_safha_combo.clear()
                self.veri_safha_combo.addItem("Tümü", None)
                if 'safha' in df_harcama.columns:
                    safhalar = df_harcama['safha'].dropna().unique()
                    for safha in sorted(safhalar):
                        self.veri_safha_combo.addItem(str(safha), safha)
            
            QMessageBox.information(self, "Başarılı", "Filtreler uygulandı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Filtre uygulanırken hata oluştu: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def export_veri_to_excel(self):
        """Veri tablosunu Excel'e aktar"""
        try:
            if self.veri_table_data.empty:
                QMessageBox.warning(self, "Uyarı", "Aktarılacak veri bulunamadı!")
                return
            
            # Dosya seç
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Excel'e Aktar", "", "Excel Files (*.xlsx)"
            )
            
            if not file_name:
                return
            
            # Excel dosyası oluştur
            workbook = xlsxwriter.Workbook(file_name)
            worksheet = workbook.add_worksheet('Veri Tablosu')
            
            # Başlıklar
            headers = [
                "No", "Tarih", "BÖLGE KODU", "KAYNAK TİPİ KODU", "STAGE KODU",
                "STAGE-OPERASYON KODU", "Safha", "Harcama Kalemi", "Birim",
                "Miktar", "Birim ücret", "Toplam", "Açıklama"
            ]
            
            # Başlık formatı
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#3b82f6',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            # Başlıkları yaz
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
            
            # Veri formatı
            data_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            # Verileri yaz
            for row_idx, (_, row) in enumerate(self.veri_table_data.iterrows(), start=1):
                worksheet.write(row_idx, 0, str(row.get('no', '')), data_format)
                worksheet.write(row_idx, 1, str(row.get('tarih', '')), data_format)
                worksheet.write(row_idx, 2, str(row.get('bolge_kodu', '')), data_format)
                worksheet.write(row_idx, 3, str(row.get('kaynak_tipi_kodu', '')), data_format)
                worksheet.write(row_idx, 4, str(row.get('stage_kodu', '')), data_format)
                worksheet.write(row_idx, 5, str(row.get('stage_operasyon_kodu', '')), data_format)
                worksheet.write(row_idx, 6, str(row.get('safha', '')), data_format)
                worksheet.write(row_idx, 7, str(row.get('harcama_kalemi', '')), data_format)
                worksheet.write(row_idx, 8, str(row.get('birim', '')), data_format)
                worksheet.write(row_idx, 9, str(row.get('miktar', '')), data_format)
                worksheet.write(row_idx, 10, str(row.get('birim_ucret', '')), data_format)
                worksheet.write(row_idx, 11, str(row.get('toplam', '')), data_format)
                worksheet.write(row_idx, 12, str(row.get('aciklama', '')), data_format)
            
            # Kolon genişliklerini ayarla
            worksheet.set_column(0, 0, 10)  # No
            worksheet.set_column(1, 1, 15)  # Tarih
            worksheet.set_column(2, 2, 15)  # Bölge
            worksheet.set_column(3, 3, 20)  # Kaynak
            worksheet.set_column(4, 4, 15)  # Stage
            worksheet.set_column(5, 5, 20)  # Stage-Operasyon
            worksheet.set_column(6, 6, 15)  # Safha
            worksheet.set_column(7, 7, 20)  # Harcama Kalemi
            worksheet.set_column(8, 8, 10)  # Birim
            worksheet.set_column(9, 9, 12)  # Miktar
            worksheet.set_column(10, 10, 15)  # Birim ücret
            worksheet.set_column(11, 11, 15)  # Toplam
            worksheet.set_column(12, 12, 30)  # Açıklama
            
            workbook.close()
            
            QMessageBox.information(self, "Başarılı", f"Veriler {file_name} dosyasına aktarıldı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Excel'e aktarma sırasında hata oluştu: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def apply_bolge_dashboard_filter(self):
        """Bölge bazlı özet için filtre uygula"""
        try:
            params = {'user_id': self.user_id}
            
            bolge_kodu = self.bolge_dashboard_bolge_combo.currentData()
            if bolge_kodu:
                params['bolge_kodu'] = bolge_kodu
            
            # Harcama verilerini yükle
            url_harcama = f"{get_api_root()}/harcama_talep"
            response_harcama = requests.get(url_harcama, params=params)
            
            df_harcama = pd.DataFrame()
            if response_harcama.status_code == 200:
                data = response_harcama.json()
                if data.get('success'):
                    expenses = data.get('data', [])
                    df_harcama = pd.DataFrame(expenses)
            
            # Bölge bazlı grafiği güncelle
            self.create_bolge_dashboard_chart(df_harcama)
            
            QMessageBox.information(self, "Başarılı", "Filtre uygulandı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Filtre uygulanırken hata oluştu: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def export_bolge_dashboard_to_excel(self):
        """Bölge bazlı özet verilerini Excel'e aktar"""
        try:
            if self.bolge_dashboard_data.empty:
                QMessageBox.warning(self, "Uyarı", "Aktarılacak veri bulunamadı!")
                return
            
            # Dosya seç
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Excel'e Aktar", "", "Excel Files (*.xlsx)"
            )
            
            if not file_name:
                return
            
            # Bölge bazlı toplamları hesapla
            df_filtered = self.bolge_dashboard_data[
                self.bolge_dashboard_data['bolge_kodu'].notna() & 
                (self.bolge_dashboard_data['bolge_kodu'] != '') & 
                self.bolge_dashboard_data['toplam'].notna()
            ]
            
            if df_filtered.empty:
                QMessageBox.warning(self, "Uyarı", "Aktarılacak veri bulunamadı!")
                return
            
            bolge_totals = df_filtered.groupby('bolge_kodu')['toplam'].sum().sort_values(ascending=False)
            
            # Excel dosyası oluştur
            workbook = xlsxwriter.Workbook(file_name)
            worksheet = workbook.add_worksheet('Bölge Bazlı Özet')
            
            # Başlık formatı
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#3b82f6',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            # Veri formatı
            data_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            # Sayı formatı
            number_format = workbook.add_format({
                'border': 1,
                'align': 'right',
                'valign': 'vcenter',
                'num_format': '#,##0.00'
            })
            
            # Başlıkları yaz
            worksheet.write(0, 0, "Bölge Kodu", header_format)
            worksheet.write(0, 1, "Toplam Tutar (₺)", header_format)
            
            # Verileri yaz
            for row_idx, (bolge, toplam) in enumerate(bolge_totals.items(), start=1):
                worksheet.write(row_idx, 0, str(bolge), data_format)
                worksheet.write(row_idx, 1, float(toplam), number_format)
            
            # Toplam satırı
            total_row = len(bolge_totals) + 2
            total_format = workbook.add_format({
                'bold': True,
                'bg_color': '#10b981',
                'font_color': 'white',
                'border': 1,
                'align': 'right',
                'valign': 'vcenter',
                'num_format': '#,##0.00'
            })
            worksheet.write(total_row, 0, "TOPLAM", total_format)
            worksheet.write(total_row, 1, bolge_totals.sum(), total_format)
            
            # Kolon genişliklerini ayarla
            worksheet.set_column(0, 0, 20)
            worksheet.set_column(1, 1, 20)
            
            workbook.close()
            
            QMessageBox.information(self, "Başarılı", f"Veriler {file_name} dosyasına aktarıldı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Excel'e aktarma sırasında hata oluştu: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_charts(self, df):
        """Tüm grafikleri güncelle"""
        if df.empty:
            return
        
        # Dashboard grafikleri
        self.create_bolge_dashboard_chart(df)
        self.create_stage_dashboard_chart(df)
        
        # Detaylı grafikler
        self.create_bolge_chart(df)
        self.create_stage_chart(df)
        self.create_safha_chart(df)
        self.create_operasyon_chart(df)
        self.create_trend_chart(df)
        self.create_kaynak_chart(df)
        self.create_birim_chart(df)
    
    def create_bolge_dashboard_chart(self, df):
        """Dashboard için bölge bazlı grafik"""
        try:
            # Veriyi sakla (Excel için)
            self.bolge_dashboard_data = df.copy() if not df.empty else pd.DataFrame()
            
            self.bolge_dashboard_figure.clear()
            ax = self.bolge_dashboard_figure.add_subplot(111)
            ax.set_facecolor('#fafafa')
            
            # NaN ve boş değerleri filtrele
            df_filtered = df[df['bolge_kodu'].notna() & (df['bolge_kodu'] != '') & df['toplam'].notna()]
            
            if df_filtered.empty:
                ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14)
                self.bolge_dashboard_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
                self.bolge_dashboard_canvas.draw()
                return
            
            bolge_totals = df_filtered.groupby('bolge_kodu')['toplam'].sum().sort_values(ascending=False)
            
            bolgeler = [str(b).strip() if pd.notna(b) else 'Bilinmeyen' for b in bolge_totals.index]
            toplamlar = [float(t) if pd.notna(t) else 0 for t in bolge_totals.values]
            
            # Modern gradient renkler
            colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(bolgeler)))
            bars = ax.bar(bolgeler, toplamlar, color=colors, edgecolor='white', linewidth=1.5)
            
            # En yüksek değeri vurgula
            if toplamlar:
                max_idx = toplamlar.index(max(toplamlar))
                bars[max_idx].set_color('#dc2626')
                bars[max_idx].set_edgecolor('#991b1b')
                bars[max_idx].set_linewidth(2.5)
            
            ax.set_title("Bölge Bazlı Toplam Tutar", fontsize=18, fontweight='bold', pad=30, color='#ea580c')
            ax.set_xlabel("Bölge Kodu", fontsize=13, fontweight='bold', color='#374151', labelpad=15)
            ax.set_ylabel("Tutar (₺)", fontsize=13, fontweight='bold', color='#374151', labelpad=15)
            ax.tick_params(axis='x', rotation=45, labelsize=11)
            ax.tick_params(axis='y', labelsize=11)
            ax.grid(True, alpha=0.3, linestyle='--', axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e5e7eb')
            ax.spines['bottom'].set_color('#e5e7eb')
            
            # Değerleri çubukların üzerine yaz - daha fazla boşluk ile
            for i, v in enumerate(toplamlar):
                ax.text(i, v, f'{v:,.0f} ₺', ha='center', va='bottom', 
                       fontsize=10, fontweight='bold', color='#1f2937', 
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
            
            self.bolge_dashboard_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.bolge_dashboard_canvas.draw()
        except Exception as e:
            print(f"Dashboard bölge grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def create_stage_dashboard_chart(self, df):
        """Dashboard için stage bazlı grafik"""
        try:
            self.stage_dashboard_figure.clear()
            ax = self.stage_dashboard_figure.add_subplot(111)
            ax.set_facecolor('#fafafa')
            
            # NaN ve boş değerleri filtrele
            df_filtered = df[df['stage_kodu'].notna() & (df['stage_kodu'] != '') & df['toplam'].notna()]
            
            if df_filtered.empty:
                ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14)
                self.stage_dashboard_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
                self.stage_dashboard_canvas.draw()
                return
            
            stage_totals = df_filtered.groupby('stage_kodu')['toplam'].sum().sort_values(ascending=False)
            
            stages = [str(s).strip() if pd.notna(s) else 'Bilinmeyen' for s in stage_totals.index]
            toplamlar = [float(t) if pd.notna(t) else 0 for t in stage_totals.values]
            
            # Modern gradient renkler
            colors = plt.cm.plasma(np.linspace(0.2, 0.8, len(stages)))
            bars = ax.bar(stages, toplamlar, color=colors, edgecolor='white', linewidth=1.5)
            
            # En yüksek değeri vurgula
            if toplamlar:
                max_idx = toplamlar.index(max(toplamlar))
                bars[max_idx].set_color('#dc2626')
                bars[max_idx].set_edgecolor('#991b1b')
                bars[max_idx].set_linewidth(2.5)
            
            ax.set_title("Stage Bazlı Toplam Tutar", fontsize=18, fontweight='bold', pad=30, color='#ea580c')
            ax.set_xlabel("Stage Kodu", fontsize=13, fontweight='bold', color='#374151', labelpad=15)
            ax.set_ylabel("Tutar (₺)", fontsize=13, fontweight='bold', color='#374151', labelpad=15)
            ax.tick_params(axis='x', rotation=45, labelsize=11)
            ax.tick_params(axis='y', labelsize=11)
            ax.grid(True, alpha=0.3, linestyle='--', axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e5e7eb')
            ax.spines['bottom'].set_color('#e5e7eb')
            
            # Değerleri çubukların üzerine yaz - daha fazla boşluk ile
            for i, v in enumerate(toplamlar):
                ax.text(i, v, f'{v:,.0f} ₺', ha='center', va='bottom', 
                       fontsize=10, fontweight='bold', color='#1f2937', 
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
            
            self.stage_dashboard_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.stage_dashboard_canvas.draw()
        except Exception as e:
            print(f"Dashboard stage grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def create_bolge_chart(self, df):
        """Bölge bazlı toplam tutar grafiği"""
        try:
            self.bolge_figure.clear()
            ax = self.bolge_figure.add_subplot(111)
            ax.set_facecolor('#fafafa')
            
            # NaN ve boş değerleri filtrele
            df_filtered = df[df['bolge_kodu'].notna() & (df['bolge_kodu'] != '') & df['toplam'].notna()]
            
            if df_filtered.empty:
                ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14)
                self.bolge_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
                self.bolge_canvas.draw()
                return
            
            bolge_totals = df_filtered.groupby('bolge_kodu')['toplam'].sum().sort_values(ascending=False)
            
            bolgeler = [str(b).strip() if pd.notna(b) else 'Bilinmeyen' for b in bolge_totals.index]
            toplamlar = [float(t) if pd.notna(t) else 0 for t in bolge_totals.values]
            
            # Modern gradient renkler
            colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(bolgeler)))
            bars = ax.bar(bolgeler, toplamlar, color=colors, edgecolor='white', linewidth=1.5)
            
            # En yüksek değeri vurgula
            if toplamlar:
                max_idx = toplamlar.index(max(toplamlar))
                bars[max_idx].set_color('#dc2626')
                bars[max_idx].set_edgecolor('#991b1b')
                bars[max_idx].set_linewidth(2.5)
            
            ax.set_title("Bölge Bazlı Toplam Tutar", fontsize=16, fontweight='bold', pad=25, color='#ea580c')
            ax.set_xlabel("Bölge Kodu", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax.set_ylabel("Tutar (₺)", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax.tick_params(axis='x', rotation=45, labelsize=10)
            ax.tick_params(axis='y', labelsize=10)
            ax.grid(True, alpha=0.3, linestyle='--', axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e5e7eb')
            ax.spines['bottom'].set_color('#e5e7eb')
            
            for i, v in enumerate(toplamlar):
                ax.text(i, v, f'{v:,.0f} ₺', ha='center', va='bottom', 
                       fontsize=9, fontweight='bold', color='#1f2937',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
            
            self.bolge_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.bolge_canvas.draw()
        except Exception as e:
            print(f"Bölge grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def create_stage_chart(self, df):
        """Stage bazlı toplam tutar grafiği"""
        try:
            self.stage_figure.clear()
            ax = self.stage_figure.add_subplot(111)
            ax.set_facecolor('#fafafa')
            
            # NaN ve boş değerleri filtrele
            df_filtered = df[df['stage_kodu'].notna() & (df['stage_kodu'] != '') & df['toplam'].notna()]
            
            if df_filtered.empty:
                ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14)
                self.stage_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
                self.stage_canvas.draw()
                return
            
            stage_totals = df_filtered.groupby('stage_kodu')['toplam'].sum().sort_values(ascending=False)
            
            stages = [str(s).strip() if pd.notna(s) else 'Bilinmeyen' for s in stage_totals.index]
            toplamlar = [float(t) if pd.notna(t) else 0 for t in stage_totals.values]
            
            # Modern gradient renkler
            colors = plt.cm.Purples(np.linspace(0.4, 0.9, len(stages)))
            bars = ax.bar(stages, toplamlar, color=colors, edgecolor='white', linewidth=1.5)
            
            # En yüksek değeri vurgula
            if toplamlar:
                max_idx = toplamlar.index(max(toplamlar))
                bars[max_idx].set_color('#dc2626')
                bars[max_idx].set_edgecolor('#991b1b')
                bars[max_idx].set_linewidth(2.5)
            
            ax.set_title("Stage Bazlı Toplam Tutar", fontsize=16, fontweight='bold', pad=25, color='#ea580c')
            ax.set_xlabel("Stage Kodu", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax.set_ylabel("Tutar (₺)", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax.tick_params(axis='x', rotation=45, labelsize=10)
            ax.tick_params(axis='y', labelsize=10)
            ax.grid(True, alpha=0.3, linestyle='--', axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e5e7eb')
            ax.spines['bottom'].set_color('#e5e7eb')
            
            for i, v in enumerate(toplamlar):
                ax.text(i, v, f'{v:,.0f} ₺', ha='center', va='bottom', 
                       fontsize=9, fontweight='bold', color='#1f2937',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
            
            self.stage_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.stage_canvas.draw()
        except Exception as e:
            print(f"Stage grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def create_safha_chart(self, df):
        """Safha bazlı pasta grafiği"""
        try:
            self.safha_figure.clear()
            ax = self.safha_figure.add_subplot(111)
            ax.set_facecolor('#fafafa')
            
            # NaN ve boş değerleri filtrele
            df_filtered = df[df['safha'].notna() & (df['safha'] != '') & df['toplam'].notna()]
            
            if df_filtered.empty:
                ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14)
                self.safha_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
                self.safha_canvas.draw()
                return
            
            safha_totals = df_filtered.groupby('safha')['toplam'].sum()
            
            # Sadece pozitif değerleri al
            safhalar = [str(s).strip() if pd.notna(s) else 'Bilinmeyen' 
                       for s in safha_totals.index 
                       if pd.notna(safha_totals[s]) and safha_totals[s] > 0]
            toplamlar = [float(safha_totals[s]) 
                        for s in safha_totals.index 
                        if pd.notna(safha_totals[s]) and safha_totals[s] > 0]
            
            if safhalar and toplamlar:
                # Modern renk paleti
                colors = plt.cm.Set3(np.linspace(0, 1, len(safhalar)))
                wedges, texts, autotexts = ax.pie(toplamlar, labels=safhalar, autopct='%1.1f%%', 
                                                  startangle=90, colors=colors,
                                                  textprops={'fontsize': 10, 'fontweight': 'bold'},
                                                  explode=[0.05] * len(safhalar))
                ax.set_title("Safha Bazlı Dağılım", fontsize=16, fontweight='bold', pad=25, color='#ea580c')
                
                # Yüzde değerlerini kalın yap
                for autotext in autotexts:
                    autotext.set_color('#1f2937')
                    autotext.set_fontweight('bold')
                    autotext.set_fontsize(11)
                
                # Etiketleri daha okunabilir yap
                for text in texts:
                    text.set_fontsize(10)
                    text.set_fontweight('bold')
                    text.set_color('#374151')
            
            self.safha_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.safha_canvas.draw()
        except Exception as e:
            print(f"Safha grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def create_operasyon_chart(self, df):
        """Operasyon bazlı grafik"""
        try:
            self.operasyon_figure.clear()
            ax = self.operasyon_figure.add_subplot(111)
            ax.set_facecolor('#fafafa')
            
            # NaN ve boş değerleri filtrele
            df_filtered = df[df['stage_operasyon_kodu'].notna() & (df['stage_operasyon_kodu'] != '') & df['toplam'].notna()]
            
            if df_filtered.empty:
                ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14)
                self.operasyon_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
                self.operasyon_canvas.draw()
                return
            
            operasyon_totals = df_filtered.groupby('stage_operasyon_kodu')['toplam'].sum().sort_values(ascending=False).head(10)
            
            operasyonlar = [str(o).strip() if pd.notna(o) else 'Bilinmeyen' for o in operasyon_totals.index]
            toplamlar = [float(t) if pd.notna(t) else 0 for t in operasyon_totals.values]
            
            # Modern gradient renkler
            colors = plt.cm.Greens(np.linspace(0.4, 0.9, len(operasyonlar)))
            bars = ax.barh(operasyonlar, toplamlar, color=colors, edgecolor='white', linewidth=1.5)
            
            # En yüksek değeri vurgula
            if toplamlar:
                max_idx = toplamlar.index(max(toplamlar))
                bars[max_idx].set_color('#dc2626')
                bars[max_idx].set_edgecolor('#991b1b')
                bars[max_idx].set_linewidth(2.5)
            
            ax.set_title("Operasyon Bazlı Toplam Tutar (İlk 10)", fontsize=16, fontweight='bold', pad=25, color='#ea580c')
            ax.set_xlabel("Tutar (₺)", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax.set_ylabel("Operasyon Kodu", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax.tick_params(axis='x', labelsize=10)
            ax.tick_params(axis='y', labelsize=10)
            ax.grid(True, alpha=0.3, linestyle='--', axis='x')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e5e7eb')
            ax.spines['bottom'].set_color('#e5e7eb')
            
            for i, v in enumerate(toplamlar):
                ax.text(v, i, f' {v:,.0f} ₺', va='center', fontsize=9, fontweight='bold', color='#1f2937',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
            
            self.operasyon_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.operasyon_canvas.draw()
        except Exception as e:
            print(f"Operasyon grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def create_trend_chart(self, df):
        """Tarih bazlı trend grafiği"""
        try:
            self.trend_figure.clear()
            ax = self.trend_figure.add_subplot(111)
            ax.set_facecolor('#fafafa')
            
            if 'tarih' in df.columns and not df.empty:
                df['tarih'] = pd.to_datetime(df['tarih'])
                df_trend = df.groupby(df['tarih'].dt.date)['toplam'].sum().sort_index()
                
                dates = [str(d) for d in df_trend.index]
                toplamlar = [float(t) if pd.notna(t) else 0 for t in df_trend.values]
                
                # Modern gradient çizgi
                ax.plot(dates, toplamlar, marker='o', linewidth=3, markersize=8, 
                       color='#fb923c', markerfacecolor='white', markeredgewidth=2, 
                       markeredgecolor='#fb923c', label='Toplam Tutar')
                ax.fill_between(dates, toplamlar, alpha=0.2, color='#fb923c')
                
                # Maksimum ve minimum noktaları vurgula
                if toplamlar:
                    max_idx = toplamlar.index(max(toplamlar))
                    min_idx = toplamlar.index(min(toplamlar))
                    ax.plot(dates[max_idx], toplamlar[max_idx], 'ro', markersize=12, label='Maksimum')
                    ax.plot(dates[min_idx], toplamlar[min_idx], 'go', markersize=12, label='Minimum')
                
                ax.set_title("Tarih Bazlı Trend Analizi", fontsize=18, fontweight='bold', pad=30, color='#ea580c')
                ax.set_xlabel("Tarih", fontsize=13, fontweight='bold', color='#374151', labelpad=15)
                ax.set_ylabel("Tutar (₺)", fontsize=13, fontweight='bold', color='#374151', labelpad=15)
                ax.tick_params(axis='x', rotation=45, labelsize=10)
                ax.tick_params(axis='y', labelsize=10)
                ax.grid(True, alpha=0.3, linestyle='--')
                ax.legend(loc='best', fontsize=11)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('#e5e7eb')
                ax.spines['bottom'].set_color('#e5e7eb')
            
            self.trend_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.trend_canvas.draw()
        except Exception as e:
            print(f"Trend grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def create_kaynak_chart(self, df):
        """Kaynak tipi bazlı grafik"""
        try:
            self.kaynak_figure.clear()
            ax = self.kaynak_figure.add_subplot(111)
            ax.set_facecolor('#fafafa')
            
            # NaN ve boş değerleri filtrele
            df_filtered = df[df['kaynak_tipi_kodu'].notna() & (df['kaynak_tipi_kodu'] != '') & df['toplam'].notna()]
            
            if df_filtered.empty:
                ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14)
                self.kaynak_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
                self.kaynak_canvas.draw()
                return
            
            kaynak_totals = df_filtered.groupby('kaynak_tipi_kodu')['toplam'].sum().sort_values(ascending=False)
            
            kaynaklar = [str(k).strip() if pd.notna(k) else 'Bilinmeyen' for k in kaynak_totals.index]
            toplamlar = [float(t) if pd.notna(t) else 0 for t in kaynak_totals.values]
            
            # Modern gradient renkler
            colors = plt.cm.Oranges(np.linspace(0.4, 0.9, len(kaynaklar)))
            bars = ax.bar(kaynaklar, toplamlar, color=colors, edgecolor='white', linewidth=1.5)
            
            # En yüksek değeri vurgula
            if toplamlar:
                max_idx = toplamlar.index(max(toplamlar))
                bars[max_idx].set_color('#dc2626')
                bars[max_idx].set_edgecolor('#991b1b')
                bars[max_idx].set_linewidth(2.5)
            
            ax.set_title("Kaynak Tipi Bazlı Dağılım", fontsize=16, fontweight='bold', pad=25, color='#ea580c')
            ax.set_xlabel("Kaynak Tipi Kodu", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax.set_ylabel("Tutar (₺)", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax.tick_params(axis='x', labelsize=10)
            ax.tick_params(axis='y', labelsize=10)
            ax.grid(True, alpha=0.3, linestyle='--', axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e5e7eb')
            ax.spines['bottom'].set_color('#e5e7eb')
            
            for i, v in enumerate(toplamlar):
                ax.text(i, v, f'{v:,.0f} ₺', ha='center', va='bottom', 
                       fontsize=9, fontweight='bold', color='#1f2937',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
            
            self.kaynak_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.kaynak_canvas.draw()
        except Exception as e:
            print(f"Kaynak grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def create_birim_chart(self, df):
        """Birim bazlı grafik"""
        try:
            self.birim_figure.clear()
            ax = self.birim_figure.add_subplot(111)
            ax.set_facecolor('#fafafa')
            
            # NaN ve boş değerleri filtrele
            df_filtered = df[df['birim'].notna() & (df['birim'] != '') & df['toplam'].notna()]
            
            if df_filtered.empty:
                ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14)
                self.birim_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
                self.birim_canvas.draw()
                return
            
            birim_totals = df_filtered.groupby('birim')['toplam'].sum().sort_values(ascending=False).head(10)
            
            birimler = [str(b).strip() if pd.notna(b) else 'Bilinmeyen' for b in birim_totals.index]
            toplamlar = [float(birim_totals[b]) if pd.notna(birim_totals[b]) else 0 for b in birim_totals.index]
            
            if birimler and toplamlar:
                # Modern gradient renkler
                colors = plt.cm.Reds(np.linspace(0.4, 0.9, len(birimler)))
                bars = ax.bar(birimler, toplamlar, color=colors, edgecolor='white', linewidth=1.5)
                
                # En yüksek değeri vurgula
                if toplamlar:
                    max_idx = toplamlar.index(max(toplamlar))
                    bars[max_idx].set_color('#dc2626')
                    bars[max_idx].set_edgecolor('#991b1b')
                    bars[max_idx].set_linewidth(2.5)
                
                ax.set_title("Birim Bazlı Analiz (İlk 10)", fontsize=16, fontweight='bold', pad=25, color='#ea580c')
                ax.set_xlabel("Birim", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
                ax.set_ylabel("Tutar (₺)", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
                ax.tick_params(axis='x', rotation=45, labelsize=10)
                ax.tick_params(axis='y', labelsize=10)
                ax.grid(True, alpha=0.3, linestyle='--', axis='y')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('#e5e7eb')
                ax.spines['bottom'].set_color('#e5e7eb')
                
                for i, v in enumerate(toplamlar):
                    ax.text(i, v, f'{v:,.0f} ₺', ha='center', va='bottom', 
                           fontsize=9, fontweight='bold', color='#1f2937')
            
            self.birim_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.birim_canvas.draw()
        except Exception as e:
            print(f"Birim grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def update_maliyet_analysis(self, df):
        """Maliyet analizlerini güncelle"""
        if df.empty:
            return
        
        try:
            # Toplam maliyet
            total_maliyet = df['toplam'].sum() if 'toplam' in df.columns else 0
            
            # Birim başına ortalama maliyet
            if 'miktar' in df.columns and df['miktar'].sum() > 0:
                birim_maliyet = total_maliyet / df['miktar'].sum()
            else:
                birim_maliyet = 0
            
            # En yüksek/düşük maliyetli bölgeler
            bolge_totals = df.groupby('bolge_kodu')['toplam'].sum()
            if not bolge_totals.empty:
                en_yuksek_bolge = bolge_totals.idxmax()
                en_dusuk_bolge = bolge_totals.idxmin()
                en_yuksek_tutar = bolge_totals.max()
                en_dusuk_tutar = bolge_totals.min()
            else:
                en_yuksek_bolge = "-"
                en_dusuk_bolge = "-"
                en_yuksek_tutar = 0
                en_dusuk_tutar = 0
            
            # Etiketleri güncelle (sadece değerler)
            self.toplam_maliyet_label.setText(f"{total_maliyet:,.0f} ₺")
            self.birim_maliyet_label.setText(f"{birim_maliyet:,.0f} ₺")
            self.en_yuksek_maliyet_label.setText(f"{en_yuksek_bolge}\n{en_yuksek_tutar:,.0f} ₺")
            self.en_dusuk_maliyet_label.setText(f"{en_dusuk_bolge}\n{en_dusuk_tutar:,.0f} ₺")
            
            # Maliyet grafiklerini oluştur
            self.create_bolge_maliyet_chart(df)
            self.create_stage_maliyet_chart(df)
            self.create_operasyon_maliyet_chart(df)
            self.create_trend_maliyet_chart(df)
            
        except Exception as e:
            print(f"Maliyet analizi hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def create_bolge_maliyet_chart(self, df):
        """Bölge bazlı maliyet karşılaştırması"""
        try:
            self.bolge_maliyet_figure.clear()
            fig = self.bolge_maliyet_figure
            fig.clear()
            fig.patch.set_facecolor('white')
            
            # NaN ve boş değerleri filtrele
            df_filtered = df[df['bolge_kodu'].notna() & (df['bolge_kodu'] != '') & df['toplam'].notna()]
            
            if df_filtered.empty:
                ax = fig.add_subplot(111)
                ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14)
                fig.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
                self.bolge_maliyet_canvas.draw()
                return
            
            # İki alt grafik: toplam tutar ve kayıt sayısı
            ax1 = fig.add_subplot(121)
            ax1.set_facecolor('#fafafa')
            ax2 = fig.add_subplot(122)
            ax2.set_facecolor('#fafafa')
            
            bolge_stats = df_filtered.groupby('bolge_kodu').agg({
                'toplam': 'sum',
                'no': 'count'
            }).sort_values('toplam', ascending=False)
            
            bolgeler = [str(b).strip() if pd.notna(b) else 'Bilinmeyen' for b in bolge_stats.index]
            toplamlar = [float(t) if pd.notna(t) else 0 for t in bolge_stats['toplam']]
            sayilar = [int(s) if pd.notna(s) else 0 for s in bolge_stats['no']]
            
            # Toplam tutar grafiği - modern gradient
            colors1 = plt.cm.Reds(np.linspace(0.4, 0.9, len(bolgeler)))
            bars1 = ax1.bar(bolgeler, toplamlar, color=colors1, edgecolor='white', linewidth=1.5)
            if toplamlar:
                max_idx = toplamlar.index(max(toplamlar))
                bars1[max_idx].set_color('#dc2626')
                bars1[max_idx].set_edgecolor('#991b1b')
                bars1[max_idx].set_linewidth(2.5)
            ax1.set_title("Bölge Bazlı Toplam Maliyet", fontsize=15, fontweight='bold', pad=25, color='#ea580c')
            ax1.set_xlabel("Bölge Kodu", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax1.set_ylabel("Tutar (₺)", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax1.tick_params(axis='x', rotation=45, labelsize=10)
            ax1.tick_params(axis='y', labelsize=10)
            ax1.grid(True, alpha=0.3, linestyle='--', axis='y')
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax1.spines['left'].set_color('#e5e7eb')
            ax1.spines['bottom'].set_color('#e5e7eb')
            
            for i, v in enumerate(toplamlar):
                ax1.text(i, v, f'{v:,.0f} ₺', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1f2937',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
            
            # Kayıt sayısı grafiği - modern gradient
            colors2 = plt.cm.Blues(np.linspace(0.4, 0.9, len(bolgeler)))
            bars2 = ax2.bar(bolgeler, sayilar, color=colors2, edgecolor='white', linewidth=1.5)
            if sayilar:
                max_idx = sayilar.index(max(sayilar))
                bars2[max_idx].set_color('#fb923c')
                bars2[max_idx].set_edgecolor('#ea580c')
                bars2[max_idx].set_linewidth(2.5)
            ax2.set_title("Bölge Bazlı Kayıt Sayısı", fontsize=15, fontweight='bold', pad=25, color='#ea580c')
            ax2.set_xlabel("Bölge Kodu", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax2.set_ylabel("Kayıt Sayısı", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax2.tick_params(axis='x', rotation=45, labelsize=10)
            ax2.tick_params(axis='y', labelsize=10)
            ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_color('#e5e7eb')
            ax2.spines['bottom'].set_color('#e5e7eb')
            
            for i, v in enumerate(sayilar):
                ax2.text(i, v, f'{v}', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1f2937',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
            
            fig.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.bolge_maliyet_canvas.draw()
        except Exception as e:
            print(f"Bölge maliyet grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def create_stage_maliyet_chart(self, df):
        """Stage bazlı maliyet analizi"""
        try:
            self.stage_maliyet_figure.clear()
            fig = self.stage_maliyet_figure
            fig.clear()
            fig.patch.set_facecolor('white')
            
            # NaN ve boş değerleri filtrele
            df_filtered = df[df['stage_kodu'].notna() & (df['stage_kodu'] != '') & df['toplam'].notna()]
            
            if df_filtered.empty:
                ax = fig.add_subplot(111)
                ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14)
                fig.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
                self.stage_maliyet_canvas.draw()
                return
            
            ax1 = fig.add_subplot(121)
            ax1.set_facecolor('#fafafa')
            ax2 = fig.add_subplot(122)
            ax2.set_facecolor('#fafafa')
            
            stage_stats = df_filtered.groupby('stage_kodu').agg({
                'toplam': 'sum',
                'no': 'count'
            }).sort_values('toplam', ascending=False)
            
            stages = [str(s).strip() if pd.notna(s) else 'Bilinmeyen' for s in stage_stats.index]
            toplamlar = [float(t) if pd.notna(t) else 0 for t in stage_stats['toplam']]
            sayilar = [int(s) if pd.notna(s) else 0 for s in stage_stats['no']]
            
            # Toplam tutar - modern gradient
            colors1 = plt.cm.Purples(np.linspace(0.4, 0.9, len(stages)))
            bars1 = ax1.bar(stages, toplamlar, color=colors1, edgecolor='white', linewidth=1.5)
            if toplamlar:
                max_idx = toplamlar.index(max(toplamlar))
                bars1[max_idx].set_color('#dc2626')
                bars1[max_idx].set_edgecolor('#991b1b')
                bars1[max_idx].set_linewidth(2.5)
            ax1.set_title("Stage Bazlı Toplam Maliyet", fontsize=15, fontweight='bold', pad=25, color='#ea580c')
            ax1.set_xlabel("Stage Kodu", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax1.set_ylabel("Tutar (₺)", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax1.tick_params(axis='x', rotation=45, labelsize=10)
            ax1.tick_params(axis='y', labelsize=10)
            ax1.grid(True, alpha=0.3, linestyle='--', axis='y')
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax1.spines['left'].set_color('#e5e7eb')
            ax1.spines['bottom'].set_color('#e5e7eb')
            
            for i, v in enumerate(toplamlar):
                ax1.text(i, v, f'{v:,.0f} ₺', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1f2937',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
            
            # Kayıt sayısı - modern gradient
            colors2 = plt.cm.Blues(np.linspace(0.4, 0.9, len(stages)))
            bars2 = ax2.bar(stages, sayilar, color=colors2, edgecolor='white', linewidth=1.5)
            if sayilar:
                max_idx = sayilar.index(max(sayilar))
                bars2[max_idx].set_color('#fb923c')
                bars2[max_idx].set_edgecolor('#ea580c')
                bars2[max_idx].set_linewidth(2.5)
            ax2.set_title("Stage Bazlı Kayıt Sayısı", fontsize=15, fontweight='bold', pad=25, color='#ea580c')
            ax2.set_xlabel("Stage Kodu", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax2.set_ylabel("Kayıt Sayısı", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax2.tick_params(axis='x', rotation=45, labelsize=10)
            ax2.tick_params(axis='y', labelsize=10)
            ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_color('#e5e7eb')
            ax2.spines['bottom'].set_color('#e5e7eb')
            
            for i, v in enumerate(sayilar):
                ax2.text(i, v, f'{v}', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1f2937',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
            
            fig.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.stage_maliyet_canvas.draw()
        except Exception as e:
            print(f"Stage maliyet grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def create_operasyon_maliyet_chart(self, df):
        """Operasyon bazlı maliyet analizi"""
        try:
            self.operasyon_maliyet_figure.clear()
            ax = self.operasyon_maliyet_figure.add_subplot(111)
            ax.set_facecolor('#fafafa')
            
            # NaN ve boş değerleri filtrele
            df_filtered = df[df['stage_operasyon_kodu'].notna() & (df['stage_operasyon_kodu'] != '') & df['toplam'].notna()]
            
            if df_filtered.empty:
                ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14)
                self.operasyon_maliyet_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
                self.operasyon_maliyet_canvas.draw()
                return
            
            operasyon_stats = df_filtered.groupby('stage_operasyon_kodu').agg({
                'toplam': 'sum',
                'no': 'count'
            }).sort_values('toplam', ascending=False).head(15)
            
            operasyonlar = [str(o).strip() if pd.notna(o) else 'Bilinmeyen' for o in operasyon_stats.index]
            toplamlar = [float(t) if pd.notna(t) else 0 for t in operasyon_stats['toplam']]
            sayilar = [int(s) if pd.notna(s) else 0 for s in operasyon_stats['no']]
            
            x = np.arange(len(operasyonlar))
            width = 0.35
            
            bars1 = ax.barh(x - width/2, toplamlar, width, label='Toplam Tutar (₺)', 
                           color='#dc2626', edgecolor='white', linewidth=1.5)
            bars2 = ax.barh(x + width/2, sayilar, width, label='Kayıt Sayısı', 
                           color='#fb923c', edgecolor='white', linewidth=1.5)
            
            ax.set_yticks(x)
            ax.set_yticklabels(operasyonlar, fontsize=10)
            ax.set_xlabel("Değer", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax.set_ylabel("Operasyon Kodu", fontsize=12, fontweight='bold', color='#374151', labelpad=12)
            ax.set_title("Operasyon Bazlı Maliyet Analizi (Top 15)", fontsize=16, fontweight='bold', pad=25, color='#ea580c')
            ax.legend(loc='lower right', fontsize=11, framealpha=0.9)
            ax.grid(True, alpha=0.3, linestyle='--', axis='x')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e5e7eb')
            ax.spines['bottom'].set_color('#e5e7eb')
            ax.tick_params(axis='x', labelsize=10)
            
            # Değerleri çubukların üzerine yaz
            for i, (v1, v2) in enumerate(zip(toplamlar, sayilar)):
                if v1 > 0:
                    ax.text(v1, i - width/2, f' {v1:,.0f} ₺', va='center', fontsize=8, fontweight='bold', color='white')
                if v2 > 0:
                    ax.text(v2, i + width/2, f' {v2}', va='center', fontsize=8, fontweight='bold', color='white')
            
            self.operasyon_maliyet_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.operasyon_maliyet_canvas.draw()
        except Exception as e:
            print(f"Operasyon maliyet grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def create_trend_maliyet_chart(self, df):
        """Tarih bazlı maliyet trendi"""
        try:
            self.trend_maliyet_figure.clear()
            fig = self.trend_maliyet_figure
            fig.clear()
            fig.patch.set_facecolor('white')
            
            if 'tarih' in df.columns and not df.empty:
                df['tarih'] = pd.to_datetime(df['tarih'])
                df_trend = df.groupby(df['tarih'].dt.date)['toplam'].sum().sort_index()
                
                dates = [str(d) for d in df_trend.index]
                toplamlar = [float(t) if pd.notna(t) else 0 for t in df_trend.values]
                
                ax1 = fig.add_subplot(111)
                ax1.set_facecolor('#fafafa')
                
                # Toplam tutar trendi - modern stil
                ax1.plot(dates, toplamlar, marker='o', linewidth=3, markersize=8, 
                        color='#dc2626', markerfacecolor='white', markeredgewidth=2, 
                        markeredgecolor='#dc2626', label='Toplam Tutar')
                ax1.fill_between(dates, toplamlar, alpha=0.2, color='#dc2626')
                if toplamlar:
                    max_idx = toplamlar.index(max(toplamlar))
                    min_idx = toplamlar.index(min(toplamlar))
                    ax1.plot(dates[max_idx], toplamlar[max_idx], 'ro', markersize=12, label='Maksimum')
                    ax1.plot(dates[min_idx], toplamlar[min_idx], 'go', markersize=12, label='Minimum')
                ax1.set_title("Tarih Bazlı Toplam Maliyet Trendi", fontsize=18, fontweight='bold', pad=30, color='#ea580c')
                ax1.set_xlabel("Tarih", fontsize=13, fontweight='bold', color='#374151', labelpad=15)
                ax1.set_ylabel("Tutar (₺)", fontsize=13, fontweight='bold', color='#374151', labelpad=15)
                ax1.tick_params(axis='x', rotation=45, labelsize=10)
                ax1.tick_params(axis='y', labelsize=10)
                ax1.grid(True, alpha=0.3, linestyle='--')
                ax1.legend(loc='best', fontsize=11)
                ax1.spines['top'].set_visible(False)
                ax1.spines['right'].set_visible(False)
                ax1.spines['left'].set_color('#e5e7eb')
                ax1.spines['bottom'].set_color('#e5e7eb')
            
            fig.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.trend_maliyet_canvas.draw()
        except Exception as e:
            print(f"Trend maliyet grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def update_statistics(self, df):
        """İstatistikleri güncelle"""
        if df.empty:
            self.total_label.setText("0 ₺")
            self.count_label.setText("0")
            self.avg_label.setText("0 ₺")
            self.max_label.setText("0 ₺")
            self.min_label.setText("0 ₺")
            self.std_label.setText("0 ₺")
            
            self.total_label_table.setText("Toplam Tutar: 0 ₺")
            self.count_label_table.setText("Toplam Kayıt: 0")
            self.avg_label_table.setText("Ortalama Tutar: 0 ₺")
            self.max_label_table.setText("Maksimum Tutar: 0 ₺")
            return
        
        try:
            total = df['toplam'].sum() if 'toplam' in df.columns else 0
            count = len(df)
            avg = total / count if count > 0 else 0
            max_val = df['toplam'].max() if 'toplam' in df.columns else 0
            min_val = df['toplam'].min() if 'toplam' in df.columns else 0
            std_val = df['toplam'].std() if 'toplam' in df.columns and count > 1 else 0
            
            # KPI kartları için sadece değerleri göster
            self.total_label.setText(f"{total:,.0f} ₺")
            self.count_label.setText(f"{count:,}")
            self.avg_label.setText(f"{avg:,.0f} ₺")
            self.max_label.setText(f"{max_val:,.0f} ₺")
            self.min_label.setText(f"{min_val:,.0f} ₺")
            self.std_label.setText(f"{std_val:,.0f} ₺")
            
            # Tablo sekmesi için tam metin
            self.total_label_table.setText(f"Toplam Tutar: {total:,.2f} ₺")
            self.count_label_table.setText(f"Toplam Kayıt: {count:,}")
            self.avg_label_table.setText(f"Ortalama Tutar: {avg:,.2f} ₺")
            self.max_label_table.setText(f"Maksimum Tutar: {max_val:,.2f} ₺")
        except Exception as e:
            print(f"İstatistik güncelleme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def update_filter_options(self, expenses):
        """Filtre seçeneklerini güncelle"""
        try:
            safhalar = set()
            stage_kodlari = set()
            
            for expense in expenses:
                if expense.get('safha'):
                    safhalar.add(expense.get('safha'))
                if expense.get('stage_kodu'):
                    stage_kodlari.add(expense.get('stage_kodu'))
            
            # Safha combo box'ını güncelle
            self.safha_combo.clear()
            self.safha_combo.addItem("Tümü", None)
            for safha in sorted(safhalar):
                self.safha_combo.addItem(safha, safha)
            
            # Stage combo box'ını güncelle
            self.stage_combo.clear()
            self.stage_combo.addItem("Tümü", None)
            for stage in sorted(stage_kodlari):
                self.stage_combo.addItem(stage, stage)
        except Exception as e:
            print(f"Filtre seçenekleri yüklenirken hata: {e}")
    
    def apply_filters(self):
        """Filtreleri uygula"""
        self.load_data()
    
    def update_genel_ozet(self, df_harcama, df_masraf):
        """Genel özet grafiğini güncelle - Harcama ve Masraf toplam"""
        try:
            # Toplamları hesapla
            harcama_toplam = df_harcama['toplam'].sum() if not df_harcama.empty and 'toplam' in df_harcama.columns else 0
            masraf_toplam = df_masraf['tutar'].sum() if not df_masraf.empty and 'tutar' in df_masraf.columns else 0
            
            # Label'ları güncelle
            self.genel_harcama_label.setText(f"{harcama_toplam:,.0f} ₺")
            self.genel_masraf_label.setText(f"{masraf_toplam:,.0f} ₺")
            
            # Daire grafiğini oluştur
            self.genel_dagilim_figure.clear()
            ax = self.genel_dagilim_figure.add_subplot(111)
            ax.set_facecolor('#fafafa')
            
            if harcama_toplam > 0 or masraf_toplam > 0:
                labels = ['Harcama', 'Masraf']
                sizes = [harcama_toplam, masraf_toplam]
                colors = ['#3b82f6', '#10b981']
                explode = (0.05, 0.05)
                
                wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                                  startangle=90, colors=colors, explode=explode,
                                                  textprops={'fontsize': 14, 'fontweight': 'bold'})
                
                ax.set_title("Harcama ve Masraf Dağılımı", fontsize=20, fontweight='bold', pad=30, color='#1e293b')
                
                # Yüzde değerlerini kalın yap
                for autotext in autotexts:
                    autotext.set_color('#1f2937')
                    autotext.set_fontweight('bold')
                    autotext.set_fontsize(16)
                
                # Etiketleri daha okunabilir yap
                for text in texts:
                    text.set_fontsize(14)
                    text.set_fontweight('bold')
                    text.set_color('#374151')
                
                # Legend ekle
                ax.legend(labels, loc='upper right', fontsize=12, framealpha=0.9)
            else:
                ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14)
            
            self.genel_dagilim_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.genel_dagilim_canvas.draw()
        except Exception as e:
            print(f"Genel özet grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def update_masraf_statistics(self, df):
        """Masraf istatistiklerini güncelle"""
        if df.empty:
            self.masraf_total_label.setText("0 ₺")
            self.masraf_count_label.setText("0")
            self.masraf_avg_label.setText("0 ₺")
            return
        
        try:
            if 'tutar' in df.columns:
                total = df['tutar'].sum()
                count = len(df)
                avg = total / count if count > 0 else 0
                
                self.masraf_total_label.setText(f"{total:,.0f} ₺")
                self.masraf_count_label.setText(f"{count:,}")
                self.masraf_avg_label.setText(f"{avg:,.0f} ₺")
        except Exception as e:
            print(f"Masraf istatistik güncelleme hatası: {e}")
    
    def update_masraf_charts(self, df):
        """Masraf grafiklerini güncelle"""
        if df.empty:
            return
        
        self.create_masraf_bolge_chart(df)
        self.create_masraf_stage_chart(df)
    
    def create_masraf_bolge_chart(self, df):
        """Masraf bölge bazlı grafik"""
        try:
            self.masraf_bolge_figure.clear()
            ax = self.masraf_bolge_figure.add_subplot(111)
            ax.set_facecolor('#fafafa')
            
            # NaN ve boş değerleri filtrele
            df_filtered = df[df['bolge_kodu'].notna() & (df['bolge_kodu'] != '') & df['tutar'].notna()]
            
            if df_filtered.empty:
                ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14)
                self.masraf_bolge_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
                self.masraf_bolge_canvas.draw()
                return
            
            bolge_totals = df_filtered.groupby('bolge_kodu')['tutar'].sum().sort_values(ascending=False)
            
            bolgeler = [str(b).strip() if pd.notna(b) else 'Bilinmeyen' for b in bolge_totals.index]
            toplamlar = [float(t) if pd.notna(t) else 0 for t in bolge_totals.values]
            
            # Modern gradient renkler
            colors = plt.cm.Greens(np.linspace(0.4, 0.9, len(bolgeler)))
            bars = ax.bar(bolgeler, toplamlar, color=colors, edgecolor='white', linewidth=1.5)
            
            # En yüksek değeri vurgula
            if toplamlar:
                max_idx = toplamlar.index(max(toplamlar))
                bars[max_idx].set_color('#10b981')
                bars[max_idx].set_edgecolor('#059669')
                bars[max_idx].set_linewidth(2.5)
            
            ax.set_title("Bölge Bazlı Toplam Masraf", fontsize=18, fontweight='bold', pad=30, color='#10b981')
            ax.set_xlabel("Bölge Kodu", fontsize=13, fontweight='bold', color='#374151', labelpad=15)
            ax.set_ylabel("Tutar (₺)", fontsize=13, fontweight='bold', color='#374151', labelpad=15)
            ax.tick_params(axis='x', rotation=45, labelsize=11)
            ax.tick_params(axis='y', labelsize=11)
            ax.grid(True, alpha=0.3, linestyle='--', axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e5e7eb')
            ax.spines['bottom'].set_color('#e5e7eb')
            
            # Değerleri çubukların üzerine yaz - daha fazla boşluk ile
            for i, v in enumerate(toplamlar):
                ax.text(i, v, f'{v:,.0f} ₺', ha='center', va='bottom', 
                       fontsize=10, fontweight='bold', color='#1f2937', 
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
            
            self.masraf_bolge_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.masraf_bolge_canvas.draw()
        except Exception as e:
            print(f"Masraf bölge grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def create_masraf_stage_chart(self, df):
        """Masraf stage bazlı grafik"""
        try:
            self.masraf_stage_figure.clear()
            ax = self.masraf_stage_figure.add_subplot(111)
            ax.set_facecolor('#fafafa')
            
            # NaN ve boş değerleri filtrele
            df_filtered = df[df['stage'].notna() & (df['stage'] != '') & df['tutar'].notna()]
            
            if df_filtered.empty:
                ax.text(0.5, 0.5, 'Veri bulunamadı', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=14)
                self.masraf_stage_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
                self.masraf_stage_canvas.draw()
                return
            
            stage_totals = df_filtered.groupby('stage')['tutar'].sum().sort_values(ascending=False)
            
            stages = [str(s).strip() if pd.notna(s) else 'Bilinmeyen' for s in stage_totals.index]
            toplamlar = [float(t) if pd.notna(t) else 0 for t in stage_totals.values]
            
            # Modern gradient renkler
            colors = plt.cm.Greens(np.linspace(0.4, 0.9, len(stages)))
            bars = ax.bar(stages, toplamlar, color=colors, edgecolor='white', linewidth=1.5)
            
            # En yüksek değeri vurgula
            if toplamlar:
                max_idx = toplamlar.index(max(toplamlar))
                bars[max_idx].set_color('#10b981')
                bars[max_idx].set_edgecolor('#059669')
                bars[max_idx].set_linewidth(2.5)
            
            ax.set_title("Stage Bazlı Toplam Masraf", fontsize=18, fontweight='bold', pad=30, color='#10b981')
            ax.set_xlabel("Stage Kodu", fontsize=13, fontweight='bold', color='#374151', labelpad=15)
            ax.set_ylabel("Tutar (₺)", fontsize=13, fontweight='bold', color='#374151', labelpad=15)
            ax.tick_params(axis='x', rotation=45, labelsize=11)
            ax.tick_params(axis='y', labelsize=11)
            ax.grid(True, alpha=0.3, linestyle='--', axis='y')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e5e7eb')
            ax.spines['bottom'].set_color('#e5e7eb')
            
            # Değerleri çubukların üzerine yaz - daha fazla boşluk ile
            for i, v in enumerate(toplamlar):
                ax.text(i, v, f'{v:,.0f} ₺', ha='center', va='bottom', 
                       fontsize=10, fontweight='bold', color='#1f2937', 
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
            
            self.masraf_stage_figure.tight_layout(pad=5.0, h_pad=3.0, w_pad=3.0)
            self.masraf_stage_canvas.draw()
        except Exception as e:
            print(f"Masraf stage grafiği hatası: {e}")
            import traceback
            traceback.print_exc()
