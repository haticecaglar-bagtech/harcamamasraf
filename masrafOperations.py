import os
import pandas as pd
from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QFormLayout, QLabel, QLineEdit, QComboBox, QDateEdit, QDialogButtonBox,
                             QDoubleSpinBox, QTableWidget, QTableWidgetItem,QDialog,
                             QHeaderView, QFileDialog, QMessageBox, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

# Try to import xlsxwriter, handle if not available
try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class MasrafTab(QWidget):
    def __init__(self, data, api_client, user_id, role='normal', bolge_kodlari=None):
        super().__init__()
        try:
            self.data = data
            self.api_client = api_client
            self.user_id = user_id
            self.role = role or 'normal'
            self.bolge_kodlari = bolge_kodlari or []
            self.original_expenses = []  # Store original expenses for filtering

            # Initialize combo boxes before calling any methods that might use them
            self.bolge_kodu_combo = QComboBox()
            self.kaynak_tipi_combo = QComboBox()
            self.stage_combo = QComboBox()
            self.operasyon_combo = QComboBox()
            self.stage_operasyon_edit = QLineEdit()
            # Now set up the tab
            self.setup_masraf_tab()
            # Load saved expenses - masraf listesi boş olsa bile devam et
            try:
                self.load_saved_expenses()
            except Exception as e:
                print(f"DEBUG - MasrafTab load_saved_expenses hatası: {str(e)}")
                import traceback
                print(f"DEBUG - Traceback: {traceback.format_exc()}")
                # Masraf listesi yüklenemese bile devam et
        except Exception as e:
            print(f"DEBUG - MasrafTab __init__ hatası: {str(e)}")
            import traceback
            print(f"DEBUG - Traceback: {traceback.format_exc()}")
            raise  # Hatayı yukarı fırlat

    def update_data(self, new_data):
        """Veri yapılarını güncelle"""
        self.data = new_data
        # Arayüz bileşenlerini güncelle
        self.update_combos()

    def update_combos(self):
        """Combo box'ları güncelle"""
        # Bölge Kodu - Kullanıcıya göre filtrele
        self.bolge_kodu_combo.clear()
        
        # Normal kullanıcı ise sadece kendi bölgelerini göster
        if self.role == 'normal' and self.bolge_kodlari:
            bolge_kodlari_dict = {}
            for kod in self.bolge_kodlari:
                if kod in self.data.get('bolge_kodlari', {}):
                    bolge_kodlari_dict[kod] = self.data['bolge_kodlari'][kod]
        else:
            # Admin ve üst düzey yönetici için tüm bölgeler
            bolge_kodlari_dict = self.data.get('bolge_kodlari', {})
        
        for code, name in bolge_kodlari_dict.items():
            self.bolge_kodu_combo.addItem(f"{name} ({code})", code)

        # Kaynak Tipi
        self.kaynak_tipi_combo.clear()
        for code, name in self.data.get('kaynak_tipleri', {}).items():
            self.kaynak_tipi_combo.addItem(f"{name} ({code})", code)

        # Stage Kodu
        self.stage_combo.clear()
        for code, name in self.data.get('stages', {}).items():
            self.stage_combo.addItem(f"{name} ({code})", code)

        # Operasyon Combo'yu da güncelle
        self.update_operasyon_combo()

    def update_operasyon_combo(self):
        """Stage seçimine göre operasyon combo box'ını güncelle"""
        self.operasyon_combo.clear()
        stage_kodu = self.stage_combo.currentData()

        if stage_kodu and stage_kodu in self.data.get('operasyonlar', {}):
            for code, name in self.data['operasyonlar'][stage_kodu].items():
                self.operasyon_combo.addItem(f"{name} ({code})", code)

        self.update_stage_operasyon()

    def update_stage_operasyon(self):
        """Stage ve operasyon kodlarını birleştirerek stage_operasyon kodunu oluştur"""
        stage_kodu = self.stage_combo.currentData() or ""
        operasyon_kodu = self.operasyon_combo.currentData() or ""

        if stage_kodu and operasyon_kodu:
            stage_operasyon_kodu = f"{stage_kodu}{operasyon_kodu}"
            self.stage_operasyon_edit.setText(stage_operasyon_kodu)
        else:
            self.stage_operasyon_edit.clear()

    def setup_masraf_tab(self):
        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)  # Bileşenler arası boşluk
        self.setStyleSheet("background-color: #f9fafb;") # Kurumsal açık gri background

        # Tablo oluştur
        self.masraf_table = QTableWidget(0, 10)
        self.masraf_table.setHorizontalHeaderLabels([
            "TARİHİ", "BÖLGE KODU", "KAYNAK TİPİ", "STAGE", "STAGE-OPR.",
            "NO.SU", "KİMDEN ALINDIĞI", "AÇIKLAMA", "TUTARI", "SİL"
        ])

        # Tablo stilini ayarla - Kurumsal tema
        self.masraf_table.setStyleSheet("""
            QTableWidget {
                border: 2px solid #e5e7eb;
                gridline-color: #e5e7eb;
                background-color: #ffffff;
                color: #1e293b;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #dbeafe;
                color: #2563eb;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }
        """)

        # Tablo sütun genişliklerini ayarla
        header = self.masraf_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setStretchLastSection(True)

        # Tablo yüksekliğini ayarla
        self.masraf_table.setMinimumHeight(300)
        self.masraf_table.verticalHeader().setVisible(False)  # Satır numaralarını gizle

        # Üst kısım için scroll area
        top_scroll = QScrollArea()
        top_scroll.setWidgetResizable(True)
        top_scroll.setFrameShape(QFrame.NoFrame)  # Çerçeveyi kaldır
        
        # Üst kısım widget'ı
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setSpacing(15)
        top_widget.setStyleSheet("background-color: #f9fafb;")

        # Stil için yardımcı fonksiyon
        def apply_input_style(widget):
            widget.setStyleSheet("""
                QLineEdit, QComboBox, QDateEdit {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    padding: 5px;
                    color: #1e293b;
                }
                QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                    border: 1px solid #3b82f6;
                    background: #ffffff;
                }
                QComboBox::drop-down {
                    border-left: 1px solid rgba(255, 255, 255, 0.1);
                }
                QComboBox::down-arrow {
                    image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAhklEQVR42mP4//8/AxIAAt4/mYQyGgD03g+qgQ/B8B+Yt4OZA0w2gP13w+9C/E8gI0g/gNnBIM4AYJ/kY/B/IIMYAM0h1eB4IMgMlgMNAJIgC4gDMQDSAzTBygAZQLZgbgB1IBAyAANtAAOQDZgbgC8zC8IAzK8gMgADAFo/i101sS3+AAAAAElFTkSuQmCC);
                }
            """)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #e5e7eb; border: none; height: 1px;")
        top_layout.addWidget(separator)

        # Form layout for expense details
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Tarih
        self.masraf_date = QDateEdit()
        self.masraf_date.setDate(QDate.currentDate())
        self.masraf_date.setCalendarPopup(True)
        self.masraf_date.setMinimumHeight(30)
        apply_input_style(self.masraf_date)
        form_layout.addRow("TARİHİ:", self.masraf_date)

        # Bölge Kodu
        self.bolge_kodu_combo.setMinimumHeight(30)
        apply_input_style(self.bolge_kodu_combo)
        form_layout.addRow("BÖLGE KODU:", self.bolge_kodu_combo)
        # Populate from data - Kullanıcıya göre filtrele
        if self.role == 'normal' and self.bolge_kodlari:
            bolge_kodlari_dict = {}
            for kod in self.bolge_kodlari:
                if kod in self.data.get('bolge_kodlari', {}):
                    bolge_kodlari_dict[kod] = self.data['bolge_kodlari'][kod]
        else:
            bolge_kodlari_dict = self.data.get('bolge_kodlari', {})
        
        for code, name in bolge_kodlari_dict.items():
            self.bolge_kodu_combo.addItem(f"{name} ({code})", code)

        # Kaynak Tipi
        self.kaynak_tipi_combo.setMinimumHeight(30)
        apply_input_style(self.kaynak_tipi_combo)
        form_layout.addRow("KAYNAK TİPİ KODU:", self.kaynak_tipi_combo)
        # Populate from data
        for code, name in self.data.get('kaynak_tipleri', {}).items():
            self.kaynak_tipi_combo.addItem(f"{name} ({code})", code)

        # Stage Kodu
        self.stage_combo.setMinimumHeight(30)
        apply_input_style(self.stage_combo)
        self.stage_combo.currentIndexChanged.connect(self.update_operasyon_combo)
        form_layout.addRow("STAGE KODU:", self.stage_combo)
        # Populate from data
        for code, name in self.data.get('stages', {}).items():
            self.stage_combo.addItem(f"{name} ({code})", code)

        # Operasyon Kodu
        self.operasyon_combo.setMinimumHeight(30)
        apply_input_style(self.operasyon_combo)
        self.operasyon_combo.currentIndexChanged.connect(self.update_stage_operasyon)
        form_layout.addRow("OPERASYON KODU:", self.operasyon_combo)

        # Stage-Operasyon Kodu
        self.stage_operasyon_edit.setReadOnly(True)
        self.stage_operasyon_edit.setMinimumHeight(30)
        apply_input_style(self.stage_operasyon_edit)
        form_layout.addRow("STAGE-OPERASYON KODU:", self.stage_operasyon_edit)

        # No.Su
        self.no_su_edit = QLineEdit()
        self.no_su_edit.setMinimumHeight(30)
        apply_input_style(self.no_su_edit)
        form_layout.addRow("NO.SU:", self.no_su_edit)

        # Kimden Alındığı
        self.who_edit = QLineEdit()
        self.who_edit.setMinimumHeight(30)
        apply_input_style(self.who_edit)
        form_layout.addRow("KİMDEN ALINDIĞI:", self.who_edit)

        # Açıklama
        self.aciklama_edit = QLineEdit()
        self.aciklama_edit.setMinimumHeight(30)
        apply_input_style(self.aciklama_edit)
        form_layout.addRow("AÇIKLAMA:", self.aciklama_edit)

        # Tutar
        self.tutar_edit = QLineEdit()
        self.tutar_edit.setMinimumHeight(30)
        apply_input_style(self.tutar_edit)
        form_layout.addRow("TUTARI:", self.tutar_edit)

        top_layout.addLayout(form_layout)

        # Butonlar
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.masraf_save_btn = QPushButton("Masraf Kaydet")
        self.masraf_save_btn.setMinimumHeight(40)
        self.masraf_save_btn.clicked.connect(self.save_masraf)
        self.masraf_save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:0.5 #2563eb, stop:1 #1d4ed8);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:0.5 #1d4ed8, stop:1 #1e40af);
            }
        """)

        self.excel_export_btn = QPushButton("Excel'e Aktar")
        self.excel_export_btn.setMinimumHeight(40)
        self.excel_export_btn.clicked.connect(self.export_to_excel)
        self.excel_export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:0.5 #2563eb, stop:1 #1d4ed8);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:0.5 #1d4ed8, stop:1 #1e40af);
            }
        """)

        self.clear_form_btn = QPushButton("Formu Temizle")
        self.clear_form_btn.setMinimumHeight(40)
        self.clear_form_btn.clicked.connect(self.clear_masraf_form)
        self.clear_form_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:0.5 #2563eb, stop:1 #1d4ed8);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:0.5 #1d4ed8, stop:1 #1e40af);
            }
        """)

        buttons_layout.addWidget(self.masraf_save_btn)
        buttons_layout.addWidget(self.excel_export_btn)
        buttons_layout.addWidget(self.clear_form_btn)
        top_layout.addLayout(buttons_layout)

        # Üst kısmı scroll area'ya ekle
        top_scroll.setWidget(top_widget)
        main_layout.addWidget(top_scroll)

        # Alt kısım için scroll area
        bottom_scroll = QScrollArea()
        bottom_scroll.setWidgetResizable(True)
        bottom_scroll.setFrameShape(QFrame.NoFrame)

        # Alt kısım widget'ı
        bottom_widget = QWidget()
        bottom_widget.setStyleSheet("background-color: #f9fafb;")
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setSpacing(15)

        # Filtre kontrolleri için widget
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setSpacing(10)

        # Bölge kodu filtresi - Kullanıcıya göre filtrele
        self.filter_bolge_combo = QComboBox()
        self.filter_bolge_combo.addItem("Tüm Bölgeler", None)
        
        if self.role == 'normal' and self.bolge_kodlari:
            bolge_kodlari_dict = {}
            for kod in self.bolge_kodlari:
                if kod in self.data.get('bolge_kodlari', {}):
                    bolge_kodlari_dict[kod] = self.data['bolge_kodlari'][kod]
        else:
            bolge_kodlari_dict = self.data.get('bolge_kodlari', {})
        
        for code, name in bolge_kodlari_dict.items():
            self.filter_bolge_combo.addItem(f"{name} ({code})", code)
        self.filter_bolge_combo.setMinimumHeight(30)
        apply_input_style(self.filter_bolge_combo)
        bolge_label = QLabel("Bölge Kodu:")
        bolge_label.setStyleSheet("color: #1e293b; font-weight: 600; font-size: 14px;")
        filter_layout.addWidget(bolge_label)
        filter_layout.addWidget(self.filter_bolge_combo)

        # Başlangıç tarihi
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setMinimumHeight(30)
        apply_input_style(self.start_date)
        start_label = QLabel("Başlangıç:")
        start_label.setStyleSheet("color: #1e293b; font-weight: 600; font-size: 14px;")
        filter_layout.addWidget(start_label)
        filter_layout.addWidget(self.start_date)

        # Bitiş tarihi
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setMinimumHeight(30)
        apply_input_style(self.end_date)
        end_label = QLabel("Bitiş:")
        end_label.setStyleSheet("color: #1e293b; font-weight: 600; font-size: 14px;")
        filter_layout.addWidget(end_label)
        filter_layout.addWidget(self.end_date)

        # Filtre butonu
        self.filter_btn = QPushButton("Filtrele")
        self.filter_btn.setMinimumHeight(30)
        self.filter_btn.clicked.connect(self.apply_filters)
        self.filter_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:0.5 #2563eb, stop:1 #1d4ed8);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:0.5 #1d4ed8, stop:1 #1e40af);
            }
        """)
        filter_layout.addWidget(self.filter_btn)

        # Filtreyi temizle butonu
        self.clear_filter_btn = QPushButton("Filtreyi Temizle")
        self.clear_filter_btn.setMinimumHeight(30)
        self.clear_filter_btn.clicked.connect(self.clear_filters)
        self.clear_filter_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:0.5 #2563eb, stop:1 #1d4ed8);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:0.5 #1d4ed8, stop:1 #1e40af);
            }
        """)
        filter_layout.addWidget(self.clear_filter_btn)

        filter_layout.addStretch()
        bottom_layout.addWidget(filter_widget)

        # Harcama tablosu başlığı
        table_title = QLabel("Kaydedilen Masraflar")
        table_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        table_title.setStyleSheet("color: #2563eb; margin-bottom: 10px; font-size: 16px;")
        bottom_layout.addWidget(table_title)

        # Tabloyu alt kısma ekle
        bottom_layout.addWidget(self.masraf_table)

        # Alt kısmı scroll area'ya ekle
        bottom_scroll.setWidget(bottom_widget)
        main_layout.addWidget(bottom_scroll)

        # İlk combo box değişimini tetikle
        self.update_operasyon_combo()

        # Verileri yükle
        self.load_saved_expenses()

    def apply_filters(self):
        """Apply filters to the table"""
        if not self.original_expenses:
            return

        # Get filter values
        selected_bolge = self.filter_bolge_combo.currentData()
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")

        # Filter expenses
        filtered_expenses = []
        for expense in self.original_expenses:
            # Check date range
            expense_date = expense.get('tarih', '')
            if not (start_date <= expense_date <= end_date):
                continue

            # Check region code
            if selected_bolge and expense.get('bolge_kodu') != selected_bolge:
                continue

            filtered_expenses.append(expense)

        # Update table with filtered data
        self.update_table_with_expenses(filtered_expenses)

    def clear_filters(self):
        """Clear all filters and show all expenses"""
        self.filter_bolge_combo.setCurrentIndex(0)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date.setDate(QDate.currentDate())
        self.update_table_with_expenses(self.original_expenses)

    def update_table_with_expenses(self, expenses):
        """Update table with given expenses"""
        self.masraf_table.setRowCount(0)
        self.masraf_table.setSortingEnabled(False)

        for row_idx, expense in enumerate(expenses):
            self.masraf_table.insertRow(row_idx)
            
            # Convert date format
            tarih = expense.get('tarih', '')
            if tarih:
                try:
                    tarih = QDate.fromString(tarih, "yyyy-MM-dd").toString("dd.MM.yyyy")
                except:
                    pass

            # Format currency
            tutar = expense.get('tutar', 0)
            try:
                tutar = f"₺ {float(tutar):.2f}"
            except ValueError:
                tutar = str(tutar)

            # Set items in table
            self.masraf_table.setItem(row_idx, 0, QTableWidgetItem(str(tarih)))
            self.masraf_table.setItem(row_idx, 1, QTableWidgetItem(str(expense.get('bolge_kodu', ''))))
            self.masraf_table.setItem(row_idx, 2, QTableWidgetItem(str(expense.get('kaynak_tipi', ''))))
            self.masraf_table.setItem(row_idx, 3, QTableWidgetItem(str(expense.get('stage', ''))))
            self.masraf_table.setItem(row_idx, 4, QTableWidgetItem(str(expense.get('stage_operasyon', ''))))
            self.masraf_table.setItem(row_idx, 5, QTableWidgetItem(str(expense.get('no_su', ''))))
            self.masraf_table.setItem(row_idx, 6, QTableWidgetItem(str(expense.get('kimden_alindigi', ''))))
            self.masraf_table.setItem(row_idx, 7, QTableWidgetItem(str(expense.get('aciklama', ''))))
            self.masraf_table.setItem(row_idx, 8, QTableWidgetItem(str(tutar)))

            # Delete button
            delete_button = QPushButton("🗑")
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444 !important;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ef4444, stop:1 #dc2626) !important;
                    color: #000000 !important;
                    border: 2px solid #dc2626 !important;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: 600;
                    padding: 8px 12px;
                    min-width: 40px;
                    min-height: 30px;
                }
                QPushButton:hover {
                    background-color: #dc2626 !important;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #dc2626, stop:1 #b91c1c) !important;
                    border-color: #b91c1c !important;
                    color: #000000 !important;
                }
                QPushButton:pressed {
                    background-color: #b91c1c !important;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #b91c1c, stop:1 #991b1b) !important;
                    border-color: #991b1b !important;
                    color: #000000 !important;
                }
            """)
            delete_button.setCursor(Qt.PointingHandCursor)
            delete_button.clicked.connect(lambda _, eid=expense["id"]: self.delete_expense_row(eid))
            self.masraf_table.setCellWidget(row_idx, 9, delete_button)

        self.masraf_table.setSortingEnabled(True)

    def load_saved_expenses(self):
        """Load saved expenses from the database with better error handling"""
        try:
            # Ensure table exists
            if not hasattr(self, 'masraf_table'):
                print("Table not initialized yet")
                return

            # Show loading state
            self.masraf_table.setRowCount(0)
            self.masraf_table.setSortingEnabled(False)  # Disable sorting while loading

            # Make API request
            response = self.api_client.get_expenses()
            print(f"API Response: {response}")  # Debug print

            # None kontrolü - boş liste geçerli bir yanıttır
            if response is None:
                print("No response from API")  # Debug print
                QMessageBox.warning(self, "Uyarı", "API yanıt vermedi")
                return

            # Handle case where response is a list directly
            if isinstance(response, list):
                expenses = response
            # Handle case where response is a dict with 'expenses' key
            elif isinstance(response, dict) and 'expenses' in response:
                expenses = response['expenses']
            else:
                print("Unexpected response format")  # Debug print
                QMessageBox.warning(self, "Uyarı", "Beklenmeyen API yanıt formatı")
                return

            print(f"Found {len(expenses)} expenses")

            # Boş liste geçerli bir yanıttır, sadece log yazdır
            if not expenses:
                print("No expenses found in response - masraf listesi boş")  # Debug print
                # Boş liste durumunda original_expenses'i boş liste olarak ayarla
                self.original_expenses = []
                return

            # Store original expenses for filtering
            self.original_expenses = expenses

            # Update table with all expenses
            self.update_table_with_expenses(expenses)

            print("Expenses loaded successfully")  # Debug print

        except Exception as e:
            error_msg = f"Masraflar yüklenirken beklenmeyen hata: {str(e)}"
            print(error_msg)  # Debug print
            QMessageBox.critical(self, "Hata", error_msg)

    def delete_expense_row(self, expense_id):
        """Belirli masrafı sil"""
        confirm = QMessageBox.question(self, "Sil", "Bu masrafı silmek istediğinizden emin misiniz?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            result = self.api_client.delete_expenses(expense_id)
            if result.get("success"):
                QMessageBox.information(self, "Başarılı", "Masraf başarıyla silindi.")
                self.load_saved_expenses()
            else:
                QMessageBox.warning(self, "Hata", "Masraf silinemedi.")

    def save_masraf(self):
        """Masraf kaydetme işlemi"""
        try:
            # Form verilerini al
            date = self.masraf_date.date().toString("yyyy-MM-dd")
            date_display = self.masraf_date.date().toString("dd.MM.yyyy")
            bolge_kodu = self.bolge_kodu_combo.currentData()
            kaynak_tipi_kodu = self.kaynak_tipi_combo.currentData()
            stage_kodu = self.stage_combo.currentData()
            stage_operasyon_kodu = self.stage_operasyon_edit.text()
            no_su = self.no_su_edit.text()
            kimden_alindigi = self.who_edit.text()
            aciklama = self.aciklama_edit.text()
            tutar_text = self.tutar_edit.text()

            # Zorunlu alanları kontrol et
            if not all([bolge_kodu, kaynak_tipi_kodu, stage_kodu, tutar_text]):
                QMessageBox.warning(self, "Uyarı", "Lütfen tüm zorunlu alanları doldurunuz.")
                return

            # Tutar kontrolü
            try:
                tutar_clean = tutar_text.replace("₺", "").replace(",", ".").strip()
                float_tutar = float(tutar_clean)
                if float_tutar <= 0:
                    QMessageBox.warning(self, "Uyarı", "Tutar sıfırdan büyük olmalıdır.")
                    return
                formatted_tutar = f"₺ {float_tutar:.2f}"
            except ValueError:
                QMessageBox.warning(self, "Uyarı", "Lütfen geçerli bir tutar giriniz.")
                return

            # API için veri hazırla
            expense_data = {
                'tarih': date,
                'bolge_kodu': bolge_kodu,
                'kaynak_tipi': kaynak_tipi_kodu,
                'stage': stage_kodu,
                'stage_operasyon': stage_operasyon_kodu,
                'no_su': no_su,
                'kimden_alindigi': kimden_alindigi,
                'aciklama': aciklama,
                'tutar': float_tutar
            }

            # API'ye gönder
            response = self.api_client.save_expense(self.user_id, expense_data)
            print(f"API yanıtı: {response}")

            # API yanıtını kontrol et
            if response :
                QMessageBox.information(self, "Bilgi", "Masraf başarıyla kaydedildi.")
                self.load_saved_expenses()  # Tabloyu yeniden yükleyerek güncelle

                # Formu temizle
                self.no_su_edit.clear()
                self.who_edit.clear()
                self.aciklama_edit.clear()
                self.tutar_edit.clear()
            else:
                error_message = response.get('message', 'Bilinmeyen bir hata oluştu') if response else 'API yanıt vermedi'
                QMessageBox.warning(self, "Uyarı", f"Masraf kaydedilemedi: {error_message}")

        except Exception as e:
            print(f"save_masraf hatası: {str(e)}")
            QMessageBox.critical(self, "Hata", f"Beklenmeyen hata oluştu: {str(e)}")

    def clear_masraf_form(self):
        """Clear the form and table (GUI only, not database)"""
        reply = QMessageBox.question(
            self,
            'Onay',
            'Formu temizlemek istediğinize emin misiniz? Bu işlem sadece ekrandaki formu ve tabloyu temizleyecektir.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Clear form fields
                self.masraf_date.setDate(QDate.currentDate())
                self.bolge_kodu_combo.setCurrentIndex(0)
                self.kaynak_tipi_combo.setCurrentIndex(0)
                self.stage_combo.setCurrentIndex(0)
                self.operasyon_combo.setCurrentIndex(0)
                self.no_su_edit.clear()
                self.who_edit.clear()
                self.aciklama_edit.clear()
                self.tutar_edit.clear()

                # Clear table (GUI only)
                self.masraf_table.setRowCount(0)

                QMessageBox.information(self, "Bilgi", "Form ve tablo başarıyla temizlendi.")

            except Exception as e:
                QMessageBox.warning(self, "Uyarı", f"Form temizlenirken bir hata oluştu: {str(e)}")

    def export_to_excel(self):
        # Kullanıcıdan zorunlu bilgileri almak için dialog oluştur
        dialog = QDialog(self)
        dialog.setWindowTitle("Excel'e Aktarım Bilgileri")

        layout = QVBoxLayout(dialog)

        form_layout = QFormLayout()

        hazirlayan_edit = QLineEdit()
        bolumu_edit = QLineEdit()
        sarf_yeri_edit = QLineEdit()
        urun_yili_edit = QLineEdit()
        tarih_edit = QDateEdit()
        tarih_edit.setDisplayFormat("dd.MM.yyyy")
        tarih_edit.setDate(QDate.currentDate())

        form_layout.addRow("Hazırlayan:", hazirlayan_edit)
        form_layout.addRow("Bölümü:", bolumu_edit)
        form_layout.addRow("Sarf Yeri:", sarf_yeri_edit)
        form_layout.addRow("Ürün Yılı:", urun_yili_edit)
        form_layout.addRow("Tarih:", tarih_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec_() != QDialog.Accepted:
            return  # Kullanıcı vazgeçti

        # Zorunlu alanlar kontrolü
        required = [
            (hazirlayan_edit.text().strip(), "HAZIRLAYAN"),
            (bolumu_edit.text().strip(), "BÖLÜMÜ"),
            (sarf_yeri_edit.text().strip(), "SARF YERİ"),
            (urun_yili_edit.text().strip(), "ÜRÜN YILI"),
        ]
        eksikler = [isim for deger, isim in required if not deger]

        if eksikler:
            QMessageBox.warning(self, "Eksik Bilgi", "Zorunlu alanlar boş:\n" + "\n".join(f"• {x}" for x in eksikler))
            return

        # Masraf tablosunda veri olup olmadığını kontrol et
        if self.masraf_table.rowCount() == 0:
            QMessageBox.warning(self, "Uyarı", "Excel'e aktarılacak masraf kaydı bulunamadı!")
            return

        # Kullanıcıya onay sor
        reply = QMessageBox.question(
            self,
            "Onay",
            "Masraf listesini Excel'e aktarmak istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # Check if xlsxwriter is installed
        if xlsxwriter is None:
            QMessageBox.critical(self, "Hata", "Excel işlemleri için 'xlsxwriter' modülü gerekli. Lütfen yükleyin.")
            return

        try:
            # Excel dosyasını aç
            file_name, _ = QFileDialog.getSaveFileName(self, "Excel'e Aktar", "", "Excel Files (*.xlsx)")
            if not file_name:
                return

            # Eğer dosya uzantısı belirtilmemişse .xlsx ekle
            if not file_name.endswith('.xlsx'):
                file_name += '.xlsx'

            # Excel dosyasını oluştur
            workbook = xlsxwriter.Workbook(file_name)
            worksheet = workbook.add_worksheet("Masraf Listesi")

            # Tüm sayfanın arka planını beyaz yap ve grid çizgilerini kaldır
            options = {'color': '#FFFFFF'}
            white_format = workbook.add_format({'bg_color': '#FFFFFF'})  # Beyaz arka plan formatı

            # Örneğin, A1'den Z100'e kadar tüm hücreleri beyaz yap
            for row in range(100):  # 100 satır
                for col in range(9):  # 26 sütun (A-Z)
                    worksheet.write_blank(row, col, None, white_format)

            worksheet.set_paper(9)  # A4 paper
            worksheet.set_margins(left=0.7, right=0.7, top=0.75, bottom=0.75)

            # Formatları tanımla - hepsi beyaz arka planlı
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'align': 'center',
                'valign': 'vcenter'
            })

            label_format = workbook.add_format({
                'bold': True,
                'font_size': 11,
                'align': 'left',
                'valign': 'vcenter'
            })

            header_info_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })

            header_format = workbook.add_format({
                'bold': True,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })

            cell_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })

            # Hücre yüksekliklerini ayarla
            worksheet.set_row(0, 30)  # Logo için daha yüksek satır
            worksheet.set_row(8, 30)  # "BELGENİN" başlığı için
            worksheet.set_row(9, 30)  # Tablo başlıkları için

            # Logo ekle - C sütununa kadar uzanan bir logo
            try:
                image_path = get_resource_path("logo.png")
                worksheet.insert_image('A1', image_path,
                                       {'x_scale': 0.5, 'y_scale': 0.5, 'x_offset': 10, 'y_offset': 10})
            except Exception as e:
                print(f"Logo eklenirken hata: {e}")
                # Continue without the logo

            # Masraf listesi başlığı - sağ tarafta
            worksheet.merge_range('H3:I3', 'MASRAF LİSTESİ', title_format)

            # Sol taraftaki bilgi etiketleri
            # ...

            # Sol taraftaki bilgi etiketleri
            worksheet.write('A4', 'HAZIRLAYAN', label_format)
            worksheet.write('B4', hazirlayan_edit.text(), header_info_format)

            worksheet.write('A5', 'BÖLÜMÜ', label_format)
            worksheet.write('B5', bolumu_edit.text(), header_info_format)

            worksheet.write('A6', 'SARF YERİ', label_format)
            worksheet.write('B6', sarf_yeri_edit.text(), header_info_format)

            worksheet.write('A7', 'ÜRÜN YILI', label_format)
            worksheet.write('B7', urun_yili_edit.text(), header_info_format)

            worksheet.write('A8', 'TARİH', label_format)
            worksheet.write('B8', tarih_edit.date().toString("dd.MM.yyyy"), header_info_format)

            # BELGENİN başlığı
            worksheet.merge_range('A9:I9', 'B E L G E N İ N', header_format)

            # Tablo başlıkları
            headers = ["TARİHİ", "BÖLGE KODU", "KAYNAK TİPİ", "STAGE", "Stage-OPR.",
                       "NO.SU", "KİMDEN ALINDIĞI", "AÇIKLAMA", "TUTARI"]

            for col, header in enumerate(headers):
                worksheet.write(9, col, header, header_format)

            # Tablodan verileri al ve Excel'e aktar
            for row in range(self.masraf_table.rowCount()):
                # Satır yüksekliğini ayarla
                worksheet.set_row(row + 10, 25)  # Veri satırları için yükseklik

                for col in range(self.masraf_table.columnCount()):
                    item = self.masraf_table.item(row, col)
                    if item:
                        worksheet.write(row + 10, col, item.text(), cell_format)
                    else:
                        worksheet.write(row + 10, col, "", cell_format)

            # 10 boş satır daha ekle (görseldeki gibi)
            for row in range(self.masraf_table.rowCount(), self.masraf_table.rowCount() + 10):
                worksheet.set_row(row + 10, 25)
                for col in range(9):
                    worksheet.write(row + 10, col, "", cell_format)
            
            # I sütununun en altına toplam formülü ekle (BOLD)
            last_row = self.masraf_table.rowCount() + 10 + 10  # Son veri satırı + 10 boş satır
            first_data_row = 10  # İlk veri satırı (0-indexed: 9, Excel'de 10. satır)
            last_data_row = self.masraf_table.rowCount() + 9  # Son veri satırı (0-indexed)
            
            # I sütunundaki tüm değerlerin toplamı için formül: =SUM(I10:I{last_data_row})
            sum_formula = f'=SUM(I{first_data_row + 1}:I{last_data_row + 1})'  # Excel 1-indexed
            
            alt_toplam_format = workbook.add_format({
                'bold': True,
                'border': 1,
                'align': 'right',
                'valign': 'vcenter',
                'font_size': 11,
                'num_format': '#,##0.00" ₺"'
            })
            worksheet.write_formula(last_row, 8, sum_formula, alt_toplam_format)  # I sütunu = col 8

            # Sütun genişliklerini ayarla
            worksheet.set_column('A:A', 12)  # TARİHİ
            worksheet.set_column('B:B', 12)  # BÖLGE KODU
            worksheet.set_column('C:C', 12)  # KAYNAK TİPİ
            worksheet.set_column('D:D', 8)  # STAGE
            worksheet.set_column('E:E', 15)  # Stage-OPR. - Biraz daha geniş
            worksheet.set_column('F:F', 8)  # NO.SU
            worksheet.set_column('G:G', 20)  # KİMDEN ALINDIĞI
            worksheet.set_column('H:H', 30)  # AÇIKLAMA
            worksheet.set_column('I:I', 12)  # TUTARI

            # Siyah border çizgisini de kaldır
            worksheet.set_column('J:J', 2, None, {'hidden': True})

            workbook.close()
            QMessageBox.information(self, "Bilgi", f"Masraf listesi {file_name} dosyasına başarıyla aktarıldı.")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Excel'e aktarma sırasında bir hata oluştu: {str(e)}")

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)