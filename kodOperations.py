from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
                             QTabWidget, QMessageBox, QHeaderView, QInputDialog, QStyle)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
from PyQt5.QtGui import QIcon
from api_client import ApiClient


class VeriYonetimiTab(QWidget):
    def __init__(self, data, on_data_updated_callback):
        super().__init__()
        self.data = data
        self.on_data_updated_callback = on_data_updated_callback
        self.api_client = ApiClient()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        tab_widget = QTabWidget()

        # Bölge Kodları
        bolge_tab = QWidget()
        self.setup_bolge_tab(bolge_tab)
        tab_widget.addTab(bolge_tab, "Bölge Kodları")

        # Kaynak Tipleri
        kaynak_tab = QWidget()
        self.setup_kaynak_tab(kaynak_tab)
        tab_widget.addTab(kaynak_tab, "Kaynak Tipleri")

        # Stage Kodları
        self.stage_tab = QWidget()
        self.setup_stage_tab(self.stage_tab)
        tab_widget.addTab(self.stage_tab, "Stage Kodları")

        # Operasyon Kodları
        operasyon_tab = QWidget()
        self.setup_operasyon_tab(operasyon_tab)
        tab_widget.addTab(operasyon_tab, "Operasyon Kodları")

        """# Stage-Operasyon Kodları
        stage_operasyon_tab = QWidget()
        self.setup_stage_operasyon_tab(stage_operasyon_tab)
        tab_widget.addTab(stage_operasyon_tab, "Stage-Operasyon Kodları")"""

        # Birim Kodları
        birim_tab = QWidget()
        self.setup_birim_tab(birim_tab)
        tab_widget.addTab(birim_tab, "Birim Kodları")

        layout.addWidget(tab_widget)

    def create_action_button(self, icon_name, tooltip, callback):
        """Create a styled action button with icon or text fallback"""
        button = QPushButton()
        button.setFixedSize(80, 30)  # Daha büyük boyut
        button.setToolTip(tooltip)

        # İkon dosyasını yüklemeyi dene
        try:
            icon = QIcon(f"icons/{icon_name}.png")
            if not icon.isNull():
                button.setIcon(icon)
                button.setIconSize(button.size() * 0.6)  # İkon boyutunu ayarla
            else:
                raise FileNotFoundError
        except:
            # İkon yoksa metin kullan
            if icon_name == "edit":
                button.setText("✏️")  # Düzenle emoji
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50 !important;
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #4CAF50, stop:1 #45a049) !important;
                        color: #000000 !important;
                        border: 2px solid #45a049 !important;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049 !important;
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #45a049, stop:1 #3d8b40) !important;
                        border-color: #3d8b40 !important;
                        color: #000000 !important;
                    }
                    QPushButton:pressed {
                        background-color: #3d8b40 !important;
                        color: #000000 !important;
                    }
                """)
            elif icon_name == "delete":
                button.setText("🗑️")  # Sil emoji
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336 !important;
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #f44336, stop:1 #da190b) !important;
                        color: #000000 !important;
                        border: 2px solid #da190b !important;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #da190b !important;
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #da190b, stop:1 #c1170a) !important;
                        border-color: #c1170a !important;
                        color: #000000 !important;
                    }
                    QPushButton:pressed {
                        background-color: #c1170a !important;
                        color: #000000 !important;
                    }
                """)

        button.clicked.connect(callback)
        return button

    def setup_bolge_tab(self, tab):
        layout = QVBoxLayout(tab)

        # Form kısmı
        form_layout = QHBoxLayout()

        # Bölge kodu giriş alanı
        kod_layout = QVBoxLayout()
        kod_label = QLabel("Bölge Kodu:")
        self.bolge_kod_input = QLineEdit()
        kod_layout.addWidget(kod_label)
        kod_layout.addWidget(self.bolge_kod_input)
        form_layout.addLayout(kod_layout)

        # Bölge adı giriş alanı
        ad_layout = QVBoxLayout()
        ad_label = QLabel("Bölge Adı:")
        self.bolge_ad_input = QLineEdit()
        ad_layout.addWidget(ad_label)
        ad_layout.addWidget(self.bolge_ad_input)
        form_layout.addLayout(ad_layout)

        # Ekle butonu
        add_button = QPushButton("Ekle")
        add_button.clicked.connect(self.add_bolge)
        form_layout.addWidget(add_button)

        layout.addLayout(form_layout)

        # Tablo
        self.bolge_table = QTableWidget(0, 4)
        self.bolge_table.setHorizontalHeaderLabels(["Kod", "Ad", "Güncelle", "Sil"])
        self.bolge_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.bolge_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.bolge_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.bolge_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.bolge_table.setColumnWidth(2, 90)
        self.bolge_table.setColumnWidth(3, 90)

        # Header yüksekliği ve font boyutunu ayarla
        header = self.bolge_table.horizontalHeader()
        header.setMinimumHeight(35)
        header.setStyleSheet("QHeaderView::section { font-size: 12px; font-weight: bold; }")

        layout.addWidget(self.bolge_table)

        # Tabloyu doldur
        self.refresh_bolge_table()

    def add_bolge(self):
        kod = self.bolge_kod_input.text().strip()
        ad = self.bolge_ad_input.text().strip()
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Bölge kodu ve adı boş olamaz!")
            return
        result = self.api_client.add_bolge(kod, ad)
        if result.get("success"):
            self.bolge_kod_input.clear()
            self.bolge_ad_input.clear()
            self.refresh_bolge_table()
            if self.on_data_updated_callback:
                self.on_data_updated_callback()
            QMessageBox.information(self, "Başarılı", "Bölge eklendi.")
        else:
            QMessageBox.warning(self, "Hata", result.get("message", "Bölge eklenemedi."))

    def refresh_bolge_table(self):
        """Refresh the region table with current data"""
        # Clear the table
        self.bolge_table.setRowCount(0)

        try:
            # Get data from API
            bolge_data = self.api_client.get_bolge_kodlari()
            
            # Check if data is in correct format
            if not isinstance(bolge_data, dict):
                print(f"Warning: bolge_data is not a dict, it's {type(bolge_data)}")
                return
                
            # Populate the table
            row = 0
            for kod, ad in bolge_data.items():
                self.bolge_table.insertRow(row)
                self.bolge_table.setItem(row, 0, QTableWidgetItem(kod))
                self.bolge_table.setItem(row, 1, QTableWidgetItem(ad))

                # Add update button
                update_btn = self.create_action_button("edit", "Düzenle",
                                                       lambda checked, k=kod, a=ad: self.edit_bolge(k, a))
                self.bolge_table.setCellWidget(row, 2, update_btn)

                # Add delete button
                delete_btn = self.create_action_button("delete", "Sil", lambda checked, k=kod: self.delete_bolge(k))
                self.bolge_table.setCellWidget(row, 3, delete_btn)

                row += 1
                
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Bölge verileri alınamadı: {str(e)}")
            return

    def edit_bolge(self, kod=None, ad=None):
        if kod is None or ad is None:
            selected_items = self.bolge_table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Uyarı", "Lütfen düzenlenecek bir satır seçin.")
                return
            row = selected_items[0].row()
            kod = self.bolge_table.item(row, 0).text()
            ad = self.bolge_table.item(row, 1).text()

        yeni_kod, yeni_ad = self.show_code_dialog("Bölge Düzenle", kod, ad, True)
        if yeni_kod and yeni_ad:
            result = self.api_client.update_bolge(kod, yeni_kod, yeni_ad)
            if result.get("success"):
                self.refresh_bolge_table()
                if self.on_data_updated_callback:
                    self.on_data_updated_callback()
                QMessageBox.information(self, "Başarılı", "Bölge güncellendi.")
            else:
                QMessageBox.warning(self, "Hata", result.get("message", "Güncellenemedi."))

    def delete_bolge(self, kod):
        result = self.api_client.delete_bolge(kod)
        if result.get("success"):
            self.refresh_bolge_table()
            if self.on_data_updated_callback:
                self.on_data_updated_callback()
            QMessageBox.information(self, "Başarılı", "Bölge silindi.")
        else:
            QMessageBox.warning(self, "Hata", result.get("message", "Silinemedi."))

    def show_code_dialog(self, title, current_kod="", current_ad="", editable_kod=True):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)

        layout = QVBoxLayout(dialog)

        kod_label = QLabel("Bölge Kodu:")
        kod_input = QLineEdit()
        kod_input.setText(current_kod)
        kod_input.setReadOnly(not editable_kod)

        ad_label = QLabel("Bölge Adı:")
        ad_input = QLineEdit()
        ad_input.setText(current_ad)

        layout.addWidget(kod_label)
        layout.addWidget(kod_input)
        layout.addWidget(ad_label)
        layout.addWidget(ad_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addWidget(buttons)

        if dialog.exec_() == QDialog.Accepted:
            return kod_input.text().strip(), ad_input.text().strip()
        else:
            return None, None
#----------------------------------------------------------------------------------------------------------------------------------------------
    def setup_kaynak_tab(self, tab):
        layout = QVBoxLayout(tab)
        # Form
        form_layout = QHBoxLayout()
        kod_label = QLabel("Kaynak Kodu:")
        self.kaynak_kod_input = QLineEdit()
        ad_label = QLabel("Kaynak Adı:")
        self.kaynak_ad_input = QLineEdit()
        add_button = QPushButton("Ekle")
        add_button.clicked.connect(self.add_kaynak_tipi)
        form_layout.addWidget(kod_label)
        form_layout.addWidget(self.kaynak_kod_input)
        form_layout.addWidget(ad_label)
        form_layout.addWidget(self.kaynak_ad_input)
        form_layout.addWidget(add_button)
        layout.addLayout(form_layout)

        # Tablo
        self.kaynak_table = QTableWidget(0, 4)
        self.kaynak_table.setHorizontalHeaderLabels(["Kod", "Ad", "Güncelle", "Sil"])
        self.kaynak_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.kaynak_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.kaynak_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.kaynak_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.kaynak_table.setColumnWidth(2, 90)
        self.kaynak_table.setColumnWidth(3, 90)

        # Header yüksekliği ve font boyutunu ayarla
        header = self.kaynak_table.horizontalHeader()
        header.setMinimumHeight(35)
        header.setStyleSheet("QHeaderView::section { font-size: 12px; font-weight: bold; }")
        layout.addWidget(self.kaynak_table)
        self.refresh_kaynak_table()

    def add_kaynak_tipi(self):
        kod = self.kaynak_kod_input.text().strip()
        ad = self.kaynak_ad_input.text().strip()
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Kaynak kodu ve adı boş olamaz!")
            return
        result = self.api_client.add_kaynak_tipi(kod, ad)
        if result.get("success"):
            self.kaynak_kod_input.clear()
            self.kaynak_ad_input.clear()
            self.refresh_kaynak_table()
            if self.on_data_updated_callback:
                self.on_data_updated_callback()
            QMessageBox.information(self, "Başarılı", "Kaynak tipi eklendi.")
        else:
            QMessageBox.warning(self, "Hata", result.get("message", "Kaynak tipi eklenemedi."))

    def refresh_kaynak_table(self):
        self.kaynak_table.setRowCount(0)
        kaynak_data = self.api_client.get_kaynak_tipleri()
        # API'den hata gelirse boş dict döndür
        if not isinstance(kaynak_data, dict) or 'success' in kaynak_data:
            if isinstance(kaynak_data, dict) and not kaynak_data.get('success', True):
                print(f"API hatası: {kaynak_data.get('message', 'Bilinmeyen hata')}")
                return
            kaynak_data = {}
        if isinstance(kaynak_data, dict):
            for row, (kod, ad) in enumerate(kaynak_data.items()):
                self.kaynak_table.insertRow(row)
                self.kaynak_table.setItem(row, 0, QTableWidgetItem(kod))
                self.kaynak_table.setItem(row, 1, QTableWidgetItem(ad))

                # Add update button
                update_btn = self.create_action_button("edit", "Düzenle",
                                                       lambda checked, k=kod, a=ad: self.update_kaynak_tipi(k, a))
                self.kaynak_table.setCellWidget(row, 2, update_btn)

                # Add delete button
                delete_btn = self.create_action_button("delete", "Sil", lambda checked, k=kod: self.delete_kaynak_tipi(k))
                self.kaynak_table.setCellWidget(row, 3, delete_btn)

    def update_kaynak_tipi(self, kod, eski_ad):
        yeni_kod, yeni_ad = self.show_code_dialog("Kaynak Tipi Düzenle", kod, eski_ad, False)
        if yeni_kod and yeni_ad:
            result = self.api_client.update_kaynak_tipi(kod, yeni_kod, yeni_ad)
            if result.get("success"):
                self.refresh_kaynak_table()
                if self.on_data_updated_callback:
                    self.on_data_updated_callback()
                QMessageBox.information(self, "Başarılı", "Kaynak tipi güncellendi.")
            else:
                QMessageBox.warning(self, "Hata", result.get("message", "Güncellenemedi."))

    def delete_kaynak_tipi(self, kod):
        result = self.api_client.delete_kaynak_tipi(kod)
        if result.get("success"):
            self.refresh_kaynak_table()
            if self.on_data_updated_callback:
                self.on_data_updated_callback()
            QMessageBox.information(self, "Başarılı", "Kaynak tipi silindi.")
        else:
            QMessageBox.warning(self, "Hata", result.get("message", "Silinemedi."))
#-----------------------------------------------------------------------------------------------------------------------
    def setup_stage_tab(self, tab):
        layout = QVBoxLayout(tab)
        form_layout = QHBoxLayout()
        kod_label = QLabel("Stage Kodu:")
        self.stage_kod_input = QLineEdit()
        ad_label = QLabel("Stage Adı:")
        self.stage_ad_input = QLineEdit()
        add_button = QPushButton("Ekle")
        add_button.clicked.connect(self.add_stage)
        form_layout.addWidget(kod_label)
        form_layout.addWidget(self.stage_kod_input)
        form_layout.addWidget(ad_label)
        form_layout.addWidget(self.stage_ad_input)
        form_layout.addWidget(add_button)
        layout.addLayout(form_layout)

        # Tablo
        self.stage_table = QTableWidget(0, 4)
        self.stage_table.setHorizontalHeaderLabels(["Kod", "Ad", "Güncelle", "Sil"])
        self.stage_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.stage_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.stage_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.stage_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.stage_table.setColumnWidth(2, 90)
        self.stage_table.setColumnWidth(3, 90)
        # Header yüksekliği ve font boyutunu ayarla
        header = self.stage_table.horizontalHeader()
        header.setMinimumHeight(35)
        header.setStyleSheet("QHeaderView::section { font-size: 12px; font-weight: bold; }")
        layout.addWidget(self.stage_table)
        self.refresh_stage_table()

    def add_stage(self):
        kod = self.stage_kod_input.text().strip()
        ad = self.stage_ad_input.text().strip()
        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Stage kodu ve adı boş olamaz!")
            return
        result = self.api_client.add_stage(kod, ad)
        if result.get("success"):
            self.stage_kod_input.clear()
            self.stage_ad_input.clear()
            self.refresh_stage_table()
            if self.on_data_updated_callback:
                self.on_data_updated_callback()
            QMessageBox.information(self, "Başarılı", "Stage eklendi.")
        else:
            QMessageBox.warning(self, "Hata", result.get("message", "Stage eklenemedi."))

    def refresh_stage_table(self):
        self.stage_table.setRowCount(0)
        stage_data = self.api_client.get_stages()
        # API'den hata gelirse boş dict döndür
        if not isinstance(stage_data, dict) or 'success' in stage_data:
            if isinstance(stage_data, dict) and not stage_data.get('success', True):
                print(f"API hatası: {stage_data.get('message', 'Bilinmeyen hata')}")
                return
            stage_data = {}
        if isinstance(stage_data, dict):
            for row, (kod, ad) in enumerate(stage_data.items()):
                self.stage_table.insertRow(row)
                self.stage_table.setItem(row, 0, QTableWidgetItem(kod))
                self.stage_table.setItem(row, 1, QTableWidgetItem(ad))

                # Add update button
                update_btn = self.create_action_button("edit", "Düzenle",
                                                       lambda checked, k=kod, a=ad: self.update_stage(k, a))
                self.stage_table.setCellWidget(row, 2, update_btn)

                # Add delete button
                delete_btn = self.create_action_button("delete", "Sil",
                                                       lambda checked, k=kod: self.delete_stage(k))
                self.stage_table.setCellWidget(row, 3, delete_btn)

    def update_stage(self, kod, eski_ad):
        yeni_kod, yeni_ad = self.show_code_dialog("Stage Düzenle", kod, eski_ad, False)
        if yeni_kod and yeni_ad:
            result = self.api_client.update_stage(kod, yeni_kod, yeni_ad)
            if result.get("success"):
                self.refresh_stage_table()
                if self.on_data_updated_callback:
                    self.on_data_updated_callback()
                QMessageBox.information(self, "Başarılı", "Stage güncellendi.")
            else:
                QMessageBox.warning(self, "Hata", result.get("message", "Güncellenemedi."))

    def delete_stage(self, kod):
        result = self.api_client.delete_stage(kod)
        if result.get("success"):
            self.refresh_stage_table()
            if self.on_data_updated_callback:
                self.on_data_updated_callback()
            QMessageBox.information(self, "Başarılı", "Stage silindi.")
        else:
            QMessageBox.warning(self, "Hata", result.get("message", "Silinemedi."))
#-----------------------------------------------------------------------------------------------------------------------
    def setup_operasyon_tab(self, tab):
        layout = QVBoxLayout(tab)
        form_layout = QHBoxLayout()
        stage_kod_label = QLabel("Stage Kodu:")
        self.operasyon_stage_kod_input = QLineEdit()
        op_kod_label = QLabel("Operasyon Kodu:")
        self.operasyon_kod_input = QLineEdit()
        op_ad_label = QLabel("Operasyon Adı:")
        self.operasyon_ad_input = QLineEdit()
        add_button = QPushButton("Ekle")
        add_button.clicked.connect(self.add_operasyon)
        form_layout.addWidget(stage_kod_label)
        form_layout.addWidget(self.operasyon_stage_kod_input)
        form_layout.addWidget(op_kod_label)
        form_layout.addWidget(self.operasyon_kod_input)
        form_layout.addWidget(op_ad_label)
        form_layout.addWidget(self.operasyon_ad_input)
        form_layout.addWidget(add_button)
        layout.addLayout(form_layout)

        # Tablo
        self.operasyon_table = QTableWidget(0, 5)
        self.operasyon_table.setHorizontalHeaderLabels(["Stage Kod", "Operasyon Kod", "Ad", "Güncelle", "Sil"])
        self.operasyon_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.operasyon_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.operasyon_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.operasyon_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.operasyon_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.operasyon_table.setColumnWidth(3, 90)
        self.operasyon_table.setColumnWidth(4, 90)

        # Header yüksekliği ve font boyutunu ayarla
        header = self.operasyon_table.horizontalHeader()
        header.setMinimumHeight(35)
        header.setStyleSheet("QHeaderView::section { font-size: 12px; font-weight: bold; }")

        layout.addWidget(self.operasyon_table)
        self.refresh_operasyon_table()

    def add_operasyon(self):
        stage_kod = self.operasyon_stage_kod_input.text().strip()
        op_kod = self.operasyon_kod_input.text().strip()
        op_ad = self.operasyon_ad_input.text().strip()

        if not stage_kod or not op_kod or not op_ad:
            QMessageBox.warning(self, "Uyarı", "Tüm alanlar dolu olmalı!")
            return

        result = self.api_client.add_operasyon(stage_kod, op_kod, op_ad)

        if result is None:
            QMessageBox.warning(self, "Hata", "API'den yanıt alınamadı. Lütfen sunucunun çalıştığından emin olun.")
            return

        if result.get("success"):
            self.operasyon_stage_kod_input.clear()
            self.operasyon_kod_input.clear()
            self.operasyon_ad_input.clear()
            self.refresh_operasyon_table()
            if self.on_data_updated_callback:
                self.on_data_updated_callback()
            QMessageBox.information(self, "Başarılı", "Operasyon eklendi.")
        else:
            # Eğer özel redirect mesajı geldiyse
            if result.get("redirect") == "stages_tab":
                reply = QMessageBox.warning(
                    self,
                    "Eksik Stage Kodu",
                    result.get("message", "Belirtilen stage kodu bulunamadı."),
                    QMessageBox.Ok
                )
                if reply == QMessageBox.Ok:
                    self.setup_stage_tab(self.stage_tab)
            else:
                QMessageBox.warning(self, "Hata", result.get("message", "Operasyon eklenemedi."))

    def refresh_operasyon_table(self):
        self.operasyon_table.setRowCount(0)
        operasyon_data = self.api_client.get_operasyonlar()
        # API'den hata gelirse boş dict döndür
        if not isinstance(operasyon_data, dict) or 'success' in operasyon_data:
            if isinstance(operasyon_data, dict) and not operasyon_data.get('success', True):
                print(f"API hatası: {operasyon_data.get('message', 'Bilinmeyen hata')}")
                return
            operasyon_data = {}
        if isinstance(operasyon_data, dict):
            row = 0
            for stage_kod, ops in operasyon_data.items():
                if not isinstance(ops, dict):
                    continue
                for op_kod, op_ad in ops.items():
                    self.operasyon_table.insertRow(row)
                    self.operasyon_table.setItem(row, 0, QTableWidgetItem(stage_kod))
                    self.operasyon_table.setItem(row, 1, QTableWidgetItem(op_kod))
                    self.operasyon_table.setItem(row, 2, QTableWidgetItem(op_ad))

                    # Add update button
                    update_btn = self.create_action_button("edit", "Düzenle",
                                                           lambda checked,s=stage_kod, k=op_kod, a=op_ad: self.update_operasyon(s, k, a))
                    self.operasyon_table.setCellWidget(row, 3, update_btn)

                    # Add delete button
                    delete_btn = self.create_action_button("delete", "Sil",
                                                           lambda checked, s=stage_kod, k=op_kod: self.delete_operasyon(s, k))
                    self.operasyon_table.setCellWidget(row, 4, delete_btn)
                    
                    row += 1

    def update_operasyon(self, stage_kod, op_kod, eski_ad):
        dialog = QDialog(self)
        dialog.setWindowTitle("Operasyon Düzenle")
        layout = QVBoxLayout(dialog)

        stage_kod_label = QLabel("Stage Kodu:")
        stage_kod_input = QLineEdit()
        stage_kod_input.setText(stage_kod)
        stage_kod_input.setReadOnly(True)

        op_kod_label = QLabel("Operasyon Kodu:")
        op_kod_input = QLineEdit()
        op_kod_input.setText(op_kod)
        op_kod_input.setReadOnly(True)

        ad_label = QLabel("Operasyon Adı:")
        ad_input = QLineEdit()
        ad_input.setText(eski_ad)

        layout.addWidget(stage_kod_label)
        layout.addWidget(stage_kod_input)
        layout.addWidget(op_kod_label)
        layout.addWidget(op_kod_input)
        layout.addWidget(ad_label)
        layout.addWidget(ad_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec_() == QDialog.Accepted:
            yeni_ad = ad_input.text().strip()
            if yeni_ad:
                result = self.api_client.update_operasyon(stage_kod, op_kod, yeni_ad)
                if result.get("success"):
                    self.refresh_operasyon_table()
                    if self.on_data_updated_callback:
                        self.on_data_updated_callback()
                    QMessageBox.information(self, "Başarılı", "Operasyon güncellendi.")
                else:
                    QMessageBox.warning(self, "Hata", result.get("message", "Güncellenemedi."))

    def delete_operasyon(self, stage_kod, op_kod):
        result = self.api_client.delete_operasyon(stage_kod, op_kod)
        if result.get("success"):
            self.refresh_operasyon_table()
            if self.on_data_updated_callback:
                self.on_data_updated_callback()
            QMessageBox.information(self, "Başarılı", "Operasyon silindi.")
        else:
            QMessageBox.warning(self, "Hata", result.get("message", "Silinemedi."))
#-----------------------------------------------------------------------------------------------------------------------
    def setup_birim_tab(self, tab):
        layout = QVBoxLayout(tab)
        form_layout = QHBoxLayout()
        birim_label = QLabel("Birim:")
        self.birim_input = QLineEdit()
        ucret_label = QLabel("Ücret:")
        self.ucret_input = QLineEdit()
        add_button = QPushButton("Ekle")
        add_button.clicked.connect(self.add_birim)
        form_layout.addWidget(birim_label)
        form_layout.addWidget(self.birim_input)
        form_layout.addWidget(ucret_label)
        form_layout.addWidget(self.ucret_input)
        form_layout.addWidget(add_button)
        layout.addLayout(form_layout)

        # Tablo
        self.birim_table = QTableWidget(0, 4)
        self.birim_table.setHorizontalHeaderLabels(["Birim", "Ücret", "Güncelle", "Sil"])
        self.birim_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.birim_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.birim_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.birim_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.birim_table.setColumnWidth(2, 90)
        self.birim_table.setColumnWidth(3, 90)

        header = self.birim_table.horizontalHeader()
        header.setMinimumHeight(35)
        header.setStyleSheet("QHeaderView::section { font-size: 12px; font-weight: bold; }")
        layout.addWidget(self.birim_table)
        self.refresh_birim_table()

    def add_birim(self):
        birim = self.birim_input.text().strip()
        ucret = self.ucret_input.text().strip()
        if not birim or not ucret:
            QMessageBox.warning(self, "Uyarı", "Birim ve ücret boş olamaz!")
            return
        result = self.api_client.add_birim(birim, ucret)
        if result.get("success"):
            self.birim_input.clear()
            self.ucret_input.clear()
            self.refresh_birim_table()
            if self.on_data_updated_callback:
                self.on_data_updated_callback()
            QMessageBox.information(self, "Başarılı", "Birim eklendi.")
        else:
            QMessageBox.warning(self, "Hata", result.get("message", "Birim eklenemedi."))

    def refresh_birim_table(self):
        self.birim_table.setRowCount(0)
        birim_data = self.api_client.get_birim_ucretler()
        if isinstance(birim_data, list):
            for row, item in enumerate(birim_data):
                birim = item.get("birim", "")
                ucret = item.get("ucret", "")

                self.birim_table.insertRow(row)
                self.birim_table.setItem(row, 0, QTableWidgetItem(birim))
                self.birim_table.setItem(row, 1, QTableWidgetItem(str(ucret)))

                # Güncelle butonu
                update_btn = self.create_action_button("edit", "Düzenle",
                                                       lambda checked, k=birim, a=ucret: self.update_birim(k, a))
                self.birim_table.setCellWidget(row, 2, update_btn)

                # Sil butonu
                delete_btn = self.create_action_button("delete", "Sil",
                                                       lambda checked, k=birim: self.delete_birim(k))
                self.birim_table.setCellWidget(row, 3, delete_btn)

    def update_birim(self, birim, eski_ucret):
        dialog = QDialog(self)
        dialog.setWindowTitle("Birim Düzenle")
        layout = QVBoxLayout(dialog)

        birim_label = QLabel("Birim:")
        birim_input = QLineEdit()
        birim_input.setText(birim)
        birim_input.setReadOnly(True)

        ucret_label = QLabel("Ücret:")
        ucret_input = QLineEdit()
        ucret_input.setText(str(eski_ucret))

        layout.addWidget(birim_label)
        layout.addWidget(birim_input)
        layout.addWidget(ucret_label)
        layout.addWidget(ucret_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec_() == QDialog.Accepted:
            yeni_ucret = ucret_input.text().strip()
            if yeni_ucret:
                result = self.api_client.update_birim(birim, yeni_ucret)
                if result.get("success"):
                    self.refresh_birim_table()
                    if self.on_data_updated_callback:
                        self.on_data_updated_callback()
                    QMessageBox.information(self, "Başarılı", "Birim güncellendi.")
                else:
                    QMessageBox.warning(self, "Hata", result.get("message", "Güncellenemedi."))

    def delete_birim(self, birim):
        result = self.api_client.delete_birim(birim)
        if result.get("success"):
            self.refresh_birim_table()
            if self.on_data_updated_callback:
                self.on_data_updated_callback()
            QMessageBox.information(self, "Başarılı", "Birim silindi.")
        else:
            QMessageBox.warning(self, "Hata", result.get("message", "Silinemedi."))