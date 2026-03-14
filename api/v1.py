import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                             QHBoxLayout, QWidget, QTabWidget, QLabel, QLineEdit,QDialog,
                             QFormLayout, QComboBox, QDateEdit, QDoubleSpinBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,QDialogButtonBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QFont
import xlsxwriter
import json

class HarcamaMasrafApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Veri Yapılarını Yükle
        self.load_data()

        # Ana pencere ayarları
        self.setWindowTitle("Harcama ve Masraf Takip Uygulaması")
        self.setGeometry(100, 100, 1200, 800)

        # Ana widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Ana layout
        self.main_layout = QVBoxLayout(self.central_widget)

        # Hoş geldiniz mesajı
        welcome_label = QLabel("Harcama ve Masraf Takip Uygulamasına Hoş Geldiniz")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        self.main_layout.addWidget(welcome_label)

        # İşlem seçme butonları
        self.button_layout = QHBoxLayout()

        self.harcama_button = QPushButton("Harcama İşlemi")
        self.harcama_button.setMinimumHeight(50)
        self.harcama_button.clicked.connect(lambda: self.open_tab(0))

        self.masraf_button = QPushButton("Masraf İşlemi")
        self.masraf_button.setMinimumHeight(50)
        self.masraf_button.clicked.connect(lambda: self.open_tab(1))

        self.opr_button = QPushButton("Kod Ekleme İşlemleri")
        self.opr_button.setMinimumHeight(50)
        self.opr_button.clicked.connect(lambda: self.open_tab(2))

        self.button_layout.addWidget(self.harcama_button)
        self.button_layout.addWidget(self.masraf_button)
        self.button_layout.addWidget(self.opr_button)
        self.main_layout.addLayout(self.button_layout)

        # Tab widget oluştur
        self.tabs = QTabWidget()
        self.tabs.setVisible(False)  # Başlangıçta gizli

        # Harcama sekmesi
        self.harcama_tab = QWidget()
        self.setup_harcama_tab()
        self.tabs.addTab(self.harcama_tab, "Harcama İşlemi")

        # Masraf sekmesi
        self.masraf_tab = QWidget()
        self.setup_masraf_tab()
        self.tabs.addTab(self.masraf_tab, "Masraf İşlemi")

        self.opr_tab = QWidget()
        self.setup_veri_yonetimi_tab()

        self.main_layout.addWidget(self.tabs)
    def open_tab(self, index):
        self.tabs.setVisible(True)
        self.tabs.setCurrentIndex(index)
    def setup_harcama_tab(self):
        self.load_data()

        # Harcama sekmesi içeriği
        layout = QVBoxLayout(self.harcama_tab)

        # Form layout
        form_layout = QFormLayout()

        # No (Otomatik)
        self.harcama_no = QLineEdit()
        self.harcama_no.setReadOnly(True)
        self.harcama_no.setText("1")  # Başlangıç değeri
        form_layout.addRow("No:", self.harcama_no)

        # Tarih
        self.harcama_date = QDateEdit()
        self.harcama_date.setDate(QDate.currentDate())
        self.harcama_date.setCalendarPopup(True)
        form_layout.addRow("TARİH:", self.harcama_date)

        # Stage-Operasyon Kodu
        self.operasyon_combo = QComboBox()
        self.stage_operasyon_edit = QLineEdit()

        # Bölge Kodu
        self.bolge_kodu_combo = QComboBox()
        for code, name in self.bolge_kodlari.items():
            self.bolge_kodu_combo.addItem(f"{name} ({code})", code)
        form_layout.addRow("BÖLGE KODU:", self.bolge_kodu_combo)

        # Kaynak Tipi Kodu
        self.kaynak_tipi_combo = QComboBox()
        for code, name in self.kaynak_tipleri.items():
            self.kaynak_tipi_combo.addItem(f"{name} ({code})", code)
        form_layout.addRow("KAYNAK TİPİ KODU:", self.kaynak_tipi_combo)

        # Stage Kodu
        self.stage_combo = QComboBox()
        self.stage_combo.currentIndexChanged.connect(self.update_operasyon_combo)
        for code, name in self.stages.items():
            self.stage_combo.addItem(f"{name} ({code})", code)
        form_layout.addRow("STAGE KODU:", self.stage_combo)


        self.operasyon_combo.currentIndexChanged.connect(self.update_stage_operasyon)
        form_layout.addRow("OPERASYON KODU:", self.operasyon_combo)

        # Stage-Operasyon Kodu (Otomatik oluşturulan)
        self.stage_operasyon_edit.setReadOnly(True)
        form_layout.addRow("STAGE-OPERASYON KODU:", self.stage_operasyon_edit)

        # Safha
        self.safha_edit = QLineEdit()
        form_layout.addRow("SAFHA:", self.safha_edit)

        # Harcama Kalemi
        self.harcama_kalemi_edit = QLineEdit()
        form_layout.addRow("HARCAMA KALEMİ:", self.harcama_kalemi_edit)

        # Birim
        self.birim_combo = QComboBox()
        self.birim_combo.addItems(["Adet", "Yevmiye", "Dekar"])
        form_layout.addRow("BİRİM:", self.birim_combo)

        # Miktar
        self.miktar_spin = QDoubleSpinBox()
        self.miktar_spin.setRange(0, 10000000)
        self.miktar_spin.setDecimals(2)
        self.miktar_spin.valueChanged.connect(self.calculate_toplam)
        form_layout.addRow("MİKTAR:", self.miktar_spin)

        # Birim Ücret
        self.birim_ucret_spin = QDoubleSpinBox()
        self.birim_ucret_spin.setRange(0, 10000000)
        self.birim_ucret_spin.setPrefix("₺ ")
        self.birim_ucret_spin.setDecimals(2)
        self.birim_ucret_spin.valueChanged.connect(self.calculate_toplam)
        form_layout.addRow("BİRİM ÜCRET:", self.birim_ucret_spin)

        # Toplam (Otomatik hesaplanır)
        self.toplam_edit = QLineEdit()
        self.toplam_edit.setReadOnly(True)
        self.toplam_edit.setText("₺ 0.00")
        form_layout.addRow("TOPLAM:", self.toplam_edit)

        # Açıklama
        self.aciklama_edit = QLineEdit()
        form_layout.addRow("AÇIKLAMA:", self.aciklama_edit)

        layout.addLayout(form_layout)

        # Butonlar
        buttons_layout = QHBoxLayout()

        self.harcama_save_btn = QPushButton("Harcama Kaydet")
        self.harcama_save_btn.clicked.connect(self.save_harcama)

        self.excel_export_btn = QPushButton("Excel'e Aktar")
        self.excel_export_btn.clicked.connect(self.export_to_excel_harcama)

        self.clear_form_btn = QPushButton("Formu Temizle")
        self.clear_form_btn.clicked.connect(self.clear_harcama_form)

        buttons_layout.addWidget(self.harcama_save_btn)
        buttons_layout.addWidget(self.excel_export_btn)
        buttons_layout.addWidget(self.clear_form_btn)

        layout.addLayout(buttons_layout)

        # Harcama tablosu
        table_title = QLabel("Kaydedilen Harcamalar")
        table_title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(table_title)

        self.harcama_table = QTableWidget(0, 13)
        self.harcama_table.setHorizontalHeaderLabels([
            "NO", "TARİH", "BÖLGE KODU", "KAYNAK TİPİ KODU", "STAGE KODU",
            "STAGE-OPERASYON KODU", "SAFHA", "HARCAMA KALEMİ", "BİRİM",
            "MİKTAR", "BİRİM ÜCRET", "TOPLAM", "AÇIKLAMA"
        ])

        # Tablo sütun genişliklerini ayarla
        self.harcama_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.harcama_table)

        # İlk combo box değişimini tetikle
        self.update_operasyon_combo()
    def update_operasyon_combo(self):
        self.operasyon_combo.clear()

        current_stage_code = self.stage_combo.currentData()
        if current_stage_code in self.operasyonlar:
            for code, name in self.operasyonlar[current_stage_code].items():
                self.operasyon_combo.addItem(f"{name} ({code})", code)

        self.update_stage_operasyon()
    def update_stage_operasyon(self):
        stage_code = self.stage_combo.currentData()
        operasyon_code = self.operasyon_combo.currentData()

        if stage_code and operasyon_code:
            combined_code = f"{stage_code}{operasyon_code}"

            # Stage_Operasyon kodunu ve adını güncelle
            if combined_code in self.stage_operasyonlar:
                self.stage_operasyon_edit.setText(f"{self.stage_operasyonlar[combined_code]} ({combined_code})")
            else:
                self.stage_operasyon_edit.setText(combined_code)
    def calculate_toplam(self):
        miktar = self.miktar_spin.value()
        birim_ucret = self.birim_ucret_spin.value()
        toplam = miktar * birim_ucret
        self.toplam_edit.setText(f"₺ {toplam:.2f}")
    def save_harcama(self):
        # Formdaki değerleri al
        no = self.harcama_no.text()
        tarih = self.harcama_date.date().toString("dd.MM.yyyy")
        bolge_kodu = self.bolge_kodu_combo.currentData()
        kaynak_tipi_kodu = self.kaynak_tipi_combo.currentData()
        stage_kodu = self.stage_combo.currentData()
        stage_operasyon_kodu = self.stage_operasyon_edit.text().split("(")[-1].strip(")")
        safha = self.safha_edit.text()
        harcama_kalemi = self.harcama_kalemi_edit.text()
        birim = self.birim_combo.currentText()
        miktar = self.miktar_spin.value()
        birim_ucret = self.birim_ucret_spin.value()
        toplam = miktar * birim_ucret
        aciklama = self.aciklama_edit.text()

        # Tabloya yeni satır ekle
        row_position = self.harcama_table.rowCount()
        self.harcama_table.insertRow(row_position)

        # Hücrelere değerleri yerleştir
        self.harcama_table.setItem(row_position, 0, QTableWidgetItem(no))
        self.harcama_table.setItem(row_position, 1, QTableWidgetItem(tarih))
        self.harcama_table.setItem(row_position, 2, QTableWidgetItem(bolge_kodu))
        self.harcama_table.setItem(row_position, 3, QTableWidgetItem(kaynak_tipi_kodu))
        self.harcama_table.setItem(row_position, 4, QTableWidgetItem(stage_kodu))
        self.harcama_table.setItem(row_position, 5, QTableWidgetItem(stage_operasyon_kodu))
        self.harcama_table.setItem(row_position, 6, QTableWidgetItem(safha))
        self.harcama_table.setItem(row_position, 7, QTableWidgetItem(harcama_kalemi))
        self.harcama_table.setItem(row_position, 8, QTableWidgetItem(birim))
        self.harcama_table.setItem(row_position, 9, QTableWidgetItem(str(miktar)))
        self.harcama_table.setItem(row_position, 10, QTableWidgetItem(f"₺ {birim_ucret:.2f}"))
        self.harcama_table.setItem(row_position, 11, QTableWidgetItem(f"₺ {toplam:.2f}"))
        self.harcama_table.setItem(row_position, 12, QTableWidgetItem(aciklama))

        # No değerini artır
        next_no = int(no) + 1
        self.harcama_no.setText(str(next_no))

        # Mesaj göster
        QMessageBox.information(self, "Bilgi", "Harcama başarıyla kaydedildi.")
    def clear_harcama_form(self):
        # Formu temizle ama No'yu koru
        current_no = self.harcama_no.text()

        self.harcama_date.setDate(QDate.currentDate())
        self.bolge_kodu_combo.setCurrentIndex(0)
        self.kaynak_tipi_combo.setCurrentIndex(0)
        self.stage_combo.setCurrentIndex(0)
        self.safha_edit.clear()
        self.harcama_kalemi_edit.clear()
        self.birim_combo.setCurrentIndex(0)
        self.miktar_spin.setValue(0)
        self.birim_ucret_spin.setValue(0)
        self.aciklama_edit.clear()

        # No değerini koru
        self.harcama_no.setText(current_no)
    def export_to_excel_harcama(self):
        try:
            # Dosya seçme diyaloğunu göster
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Excel Dosyasını Kaydet", "",
                "Excel Files (*.xlsx);;All Files (*)", options=options
            )

            if not file_name:
                return  # Kullanıcı iptal etti

            if not file_name.endswith('.xlsx'):
                file_name += '.xlsx'

            # Tablodan verileri al
            data = []
            headers = []

            # Başlıkları al
            for col in range(self.harcama_table.columnCount()):
                headers.append(self.harcama_table.horizontalHeaderItem(col).text())

            # Verileri al
            for row in range(self.harcama_table.rowCount()):
                row_data = []
                for col in range(self.harcama_table.columnCount()):
                    item = self.harcama_table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            # DataFrame oluştur
            df = pd.DataFrame(data, columns=headers)

            # Excel'e kaydet
            df.to_excel(file_name, sheet_name="2025 SCV Proje Harcama", index=False)

            QMessageBox.information(self, "Başarılı", f"Veriler başarıyla {file_name} dosyasına kaydedildi.")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Excel'e aktarma sırasında bir hata oluştu: {str(e)}")
    def setup_masraf_tab(self):
        self.load_data()
        # Masraf sekmesi içeriği
        layout = QVBoxLayout(self.masraf_tab)

        # Header fields (HAZIRLAYAN, BÖLÜMÜ, etc.)
        header_form = QFormLayout()

        # Hazırlayan
        self.hazirlayan_edit = QLineEdit()
        header_form.addRow("HAZIRLAYAN:", self.hazirlayan_edit)

        # Bölümü
        self.bolumu_edit = QLineEdit()
        header_form.addRow("BÖLÜMÜ:", self.bolumu_edit)

        # Sarf Yeri
        self.sarf_yeri_edit = QLineEdit()
        header_form.addRow("SARF YERİ:", self.sarf_yeri_edit)

        # Ürün Yılı
        self.urun_yili_edit = QLineEdit()
        self.urun_yili_edit.setText(str(QDate.currentDate().year()))
        header_form.addRow("ÜRÜN YILI:", self.urun_yili_edit)

        # Tarih (Belgenin tarihi)
        self.belge_tarih_edit = QDateEdit()
        self.belge_tarih_edit.setDate(QDate.currentDate())
        self.belge_tarih_edit.setCalendarPopup(True)
        header_form.addRow("TARİH:", self.belge_tarih_edit)

        layout.addLayout(header_form)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # Form layout for expense details
        form_layout = QFormLayout()

        # Tarih
        self.masraf_date = QDateEdit()
        self.masraf_date.setDate(QDate.currentDate())
        self.masraf_date.setCalendarPopup(True)
        form_layout.addRow("TARİHİ:", self.masraf_date)

        # Bölge Kodu
        self.bolge_kodu_combo = QComboBox()
        for code, name in self.bolge_kodlari.items():
            self.bolge_kodu_combo.addItem(f"{name} ({code})", code)
        form_layout.addRow("BÖLGE KODU:", self.bolge_kodu_combo)

        # Kaynak Tipi Kodu
        self.kaynak_tipi_combo = QComboBox()
        for code, name in self.kaynak_tipleri.items():
            self.kaynak_tipi_combo.addItem(f"{name} ({code})", code)
        form_layout.addRow("KAYNAK TİPİ KODU:", self.kaynak_tipi_combo)

        # Stage Kodu
        self.stage_combo = QComboBox()
        self.stage_combo.currentIndexChanged.connect(self.update_operasyon_combo)
        for code, name in self.stages.items():
            self.stage_combo.addItem(f"{name} ({code})", code)
        form_layout.addRow("STAGE KODU:", self.stage_combo)

        # Operasyon Kodu
        self.operasyon_combo = QComboBox()
        self.operasyon_combo.currentIndexChanged.connect(self.update_stage_operasyon)
        form_layout.addRow("OPERASYON KODU:", self.operasyon_combo)

        # Stage-Operasyon Kodu (Otomatik oluşturulan)
        self.stage_operasyon_edit = QLineEdit()
        self.stage_operasyon_edit.setReadOnly(True)
        form_layout.addRow("STAGE-OPERASYON KODU:", self.stage_operasyon_edit)

        # No.Su
        self.no_su_edit = QLineEdit()
        form_layout.addRow("NO.SU:", self.no_su_edit)

        # Kimden Alındığı
        self.who_edit = QLineEdit()
        form_layout.addRow("KİMDEN ALINDIĞI:", self.who_edit)

        # Açıklama
        self.aciklama_edit = QLineEdit()
        form_layout.addRow("AÇIKLAMA:", self.aciklama_edit)

        # Tutar
        self.tutar_edit = QLineEdit()
        form_layout.addRow("TUTARI:", self.tutar_edit)

        layout.addLayout(form_layout)

        # Butonlar
        buttons_layout = QHBoxLayout()
        self.masraf_save_btn = QPushButton("Masraf Kaydet")
        self.masraf_save_btn.clicked.connect(self.save_masraf)
        self.excel_export_btn = QPushButton("Excel'e Aktar")
        self.excel_export_btn.clicked.connect(self.export_to_excel)
        self.clear_form_btn = QPushButton("Formu Temizle")
        self.clear_form_btn.clicked.connect(self.clear_masraf_form)
        buttons_layout.addWidget(self.masraf_save_btn)
        buttons_layout.addWidget(self.excel_export_btn)
        buttons_layout.addWidget(self.clear_form_btn)
        layout.addLayout(buttons_layout)

        # Harcama tablosu
        table_title = QLabel("Kaydedilen Masraflar")
        table_title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(table_title)

        self.masraf_table = QTableWidget(0, 9)
        self.masraf_table.setHorizontalHeaderLabels([
            "TARİHİ", "BÖLGE KODU", "KAYNAK TİPİ", "STAGE", "STAGE-OPR.",
            "NO.SU", "KİMDEN ALINDIĞI", "AÇIKLAMA", "TUTARI"
        ])

        # Tablo sütun genişliklerini ayarla
        self.masraf_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.masraf_table)

        # İlk combo box değişimini tetikle
        self.update_operasyon_combo()
    def save_masraf(self):
        # Masraf kaydetme işlemi
        date = self.masraf_date.date().toString("dd.MM.yyyy")
        bolge_kodu = self.bolge_kodu_combo.currentData()
        bolge_adi = self.bolge_kodu_combo.currentText().split(" (")[0]

        kaynak_tipi_kodu = self.kaynak_tipi_combo.currentData()
        kaynak_tipi_adi = self.kaynak_tipi_combo.currentText().split(" (")[0]

        stage_kodu = self.stage_combo.currentData()
        stage_operasyon_kodu = self.stage_operasyon_edit.text()

        no_su = self.no_su_edit.text()
        kimden_alindigi = self.who_edit.text()
        aciklama = self.aciklama_edit.text()
        tutar = self.tutar_edit.text()

        # Eğer tutar alanı sayısal değilse uyarı ver
        try:
            float_tutar = float(tutar.replace(",", "."))
            formatted_tutar = f"₺ {float_tutar:.2f}"
        except ValueError:
            QMessageBox.warning(self, "Uyarı", "Lütfen geçerli bir tutar giriniz.")
            return

        row_position = self.masraf_table.rowCount()
        self.masraf_table.insertRow(row_position)

        # Excel şablonundaki sıra ile aynı olacak şekilde hücreleri doldur
        self.masraf_table.setItem(row_position, 0, QTableWidgetItem(date))
        self.masraf_table.setItem(row_position, 1, QTableWidgetItem(bolge_kodu))
        self.masraf_table.setItem(row_position, 2, QTableWidgetItem(kaynak_tipi_kodu))
        self.masraf_table.setItem(row_position, 3, QTableWidgetItem(stage_kodu))
        self.masraf_table.setItem(row_position, 4, QTableWidgetItem(stage_operasyon_kodu))
        self.masraf_table.setItem(row_position, 5, QTableWidgetItem(no_su))
        self.masraf_table.setItem(row_position, 6, QTableWidgetItem(kimden_alindigi))
        self.masraf_table.setItem(row_position, 7, QTableWidgetItem(aciklama))
        self.masraf_table.setItem(row_position, 8, QTableWidgetItem(formatted_tutar))

        # Formu temizle
        self.clear_masraf_form()

        # Mesaj göster
        QMessageBox.information(self, "Bilgi", "Masraf başarıyla kaydedildi.")
    def clear_masraf_form(self):
        self.masraf_date.setDate(QDate.currentDate())
        self.bolge_kodu_combo.setCurrentIndex(0)
        self.kaynak_tipi_combo.setCurrentIndex(0)
        self.stage_combo.setCurrentIndex(0)
        self.operasyon_combo.setCurrentIndex(0)
        self.no_su_edit.clear()
        self.who_edit.clear()
        self.aciklama_edit.clear()
        self.tutar_edit.clear()
    def export_to_excel(self):
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
            image_path = get_resource_path("img.png")

            worksheet.insert_image('A1', image_path, {'x_scale': 0.5, 'y_scale': 0.5, 'x_offset': 10, 'y_offset': 10})

            # Masraf listesi başlığı - sağ tarafta
            worksheet.merge_range('H3:I3', 'MASRAF LİSTESİ', title_format)

            # Sol taraftaki bilgi etiketleri
            worksheet.write('A4', 'HAZIRLAYAN', label_format)
            worksheet.write('B4', self.hazirlayan_edit.text(), header_info_format)

            worksheet.write('A5', 'BÖLÜMÜ', label_format)
            worksheet.write('B5', self.bolumu_edit.text(), header_info_format)

            worksheet.write('A6', 'SARF YERİ', label_format)
            worksheet.write('B6', self.sarf_yeri_edit.text(), header_info_format)

            worksheet.write('A7', 'ÜRÜN YILI', label_format)
            worksheet.write('B7', self.urun_yili_edit.text(), header_info_format)

            worksheet.write('A8', 'TARİH', label_format)
            worksheet.write('B8', self.belge_tarih_edit.date().toString("dd.MM.yyyy"), header_info_format)

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
    def load_data(self):
        # Sabit verileri yükle
        self._load_default_data()

        # Kaydedilmiş kullanıcı verilerini yükle
        self._load_user_data()
    def _load_default_data(self):
        # Kaynak tipi verileri
        self.kaynak_tipleri = {
            "01": "İşçilik",
            "02": "Malzeme",
            "03": "Hizmet",
            "04": "Enerji",
            "05": "Kiralama"
        }

        # Stage verileri
        self.stages = {
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
        self.operasyonlar = {
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
            # Tarla Hazırlığı (02)
            "02": {
                "01": "Tarla Kirası",
                "02": "Çiflik Ve Depo Kirası",
                "03": "Soil Analysis",
                "04": "Güz Sürüm",
                "05": "Bahar Sürümü",
                "06": "Dal Parçalama",
                "07": "Bahar Sürümü 2",
                "08": "Bahar Sürümü 3",
                "97": "Malzeme İndirme Yükleme",
                "98": "Malzeme Nakliye",
                "99": "Ekipman Bakım Tamirat"
            },
            # Gübreleme (03)
            "03": {
                "01": "Gübre Uygulama",
                "02": "Gübre Uygulama Destek",
                "97": "Malzeme İndirme Yükleme",
                "98": "Malzeme Nakliye",
                "99": "Ekipman Bakım Tamirat"
            },
            # Dikim (04)
            "04": {
                "01": "Dikim",
                "02": "Dikim Destek",
                "03": "Aşılama",
                "97": "Malzeme İndirme Yükleme",
                "98": "Malzeme Nakliye",
                "99": "Ekipman Bakım Tamirat"
            },
            # İlaçlama (05)
            "05": {
                "01": "Herbicide Round-up",
                "02": "Herbicide Dual 960",
                "03": "Fungucide",
                "04": "Insecticide",
                "05": "Tarot",
                "05": "Herbicide Round-up destek",
                "06": "Herbicide Dual 960 destek",
                "07": "Fungucide destek",
                "08": "Insecticide destek",
                "97": "Malzeme İndirme Yükleme",
                "98": "Malzeme Nakliye",
                "99": "Ekipman Bakım Tamirat"
            },
            # Sulama (06)
            "06": {
                "01": "Sulama Kurulumu",
                "02": "Sulama",
                "03": "Sulama Tamir",
                "97": "Malzeme İndirme Yükleme",
                "98": "Malzeme Nakliye",
                "99": "Ekipman Bakım Tamirat"
            },
            # Çapalama (07)
            "07": {
                "01": "Elle Çapalama",
                "02": "Mekanik Çapalama",
                "97": "Malzeme İndirme Yükleme",
                "98": "Malzeme Nakliye",
                "99": "Ekipman Bakım Tamirat"
            },
            # Kırım (08)
            "08": {
                "01": "Kırım",
                "02": "Kırım Destek",
                "03": "Kırımdan Dikiş Mak. Taşıma",
                "97": "Malzeme İndirme Yükleme",
                "98": "Malzeme Nakliye",
                "99": "Ekipman Bakım Tamirat"
            },
            # Kurutma (09)
            "09": {
                "01": "Dikiş Mak.",
                "02": "Dikiş Mak. Destek",
                "03": "Dikiş Mak.Dan Seraya Taşıma",
                "04": "Sera Kurutma Kontrol",
                "05": "İstifleme",
                "06": "Sera Kurulumu",
                "07": "Seralarda Ot Temizliği",
                "08": "Yaprak Kesme",
                "09": "Fırın Bakım Ve Kontrol İşçiliği",
                "10": "Fırına Taşıma Ve Yerleştirme İşçiliği",
                "11": "Raks Doldurma İşçiliği",
                "12": "Seraya Taşıma Ve Serme İşçiliği",
                "13": "Yaprak Düzenleme İşçiliği",
                "97": "Malzeme İndirme Yükleme",
                "98": "Malzeme Nakliye",
                "99": "Ekipman Bakım Tamirat"
            },
            # Kutulama (10)
            "10": {
                "01": "Kutulama",
                "02": "Tavlama",
                "97": "Malzeme İndirme Yükleme",
                "98": "Malzeme Nakliye",
                "99": "Ekipman Bakım Tamirat"
            },
            # Diğer (11)
            "11": {
                "01": "Çevre Düzenleme",
                "02": "Kahya / Aile",
                "03": "Diğer",
                "04": "Dayıbaşı",
                "05": "Bakım",
                "06": "Tespit-Tesellüm",
                "07": "Kasko , Sigorta Poliçeleri",
                "08": "Müşteri Temsil Ağırlama",
                "09": "Ekipman Bakım Tamirat",
                "97": "Malzeme İndirme Yükleme",
                "98": "Malzeme Nakliye",
                "99": "Traktör , Römork Bakım Tamirat"
            },
            # Nakliye (12)
            "12": {
                "98": "Gayrimamul"
            },
            # Supervisor (13)
            "13": {
                "01": "Supervisor"
            },
            # Kültürel İşlemler (14)
            "14": {
                "01": "Sürgün Kontrol",
                "02": "Tepe Kırımı"
            }
        }

        # Stage-Operasyon kombinasyonları
        self.stage_operasyonlar = {
            # Fidelik (01) kombinasyonları
            "0101": "Fidelik_Fide Yastığı Hazırlama",
            "0102": "Fidelik_Tohum Atma",
            "0103": "Fidelik_Fidelik Sulama",
            "0104": "Fidelik_Fide Çekimi",
            "0105": "Fidelik_Gübre Uygulama",
            "0106": "Fidelik_Ot Temizleme",
            "0107": "Fidelik_Sera Havalandırma - Kapatma",
            "0108": "Fidelik_İlaçlama",
            "0109": "Fidelik_Fide Kırpma",
            "0197": "Fidelik_Malzeme İndirme Yükleme",
            "0198": "Fidelik_Malzeme Nakliye",
            "0199": "Fidelik_Ekipman Bakım Tamirat",

            # Tarla Hazırlığı (02) kombinasyonları
            "0201": "Tarla Hazırlığı_Tarla Kirası",
            "0202": "Tarla Hazırlığı_Çiflik Ve Depo Kirası",
            "0203": "Tarla Hazırlığı_Soil Analysis",
            "0204": "Tarla Hazırlığı_Güz Sürüm",
            "0205": "Tarla Hazırlığı_Bahar Sürümü",
            "0206": "Tarla Hazırlığı_Dal Parçalama",
            "0207": "Tarla Hazırlığı_Bahar Sürümü 2",
            "0208": "Tarla Hazırlığı_Bahar Sürümü 3",
            "0297": "Tarla Hazırlığı_Malzeme İndirme Yükleme",
            "0298": "Tarla Hazırlığı_Malzeme Nakliye",
            "0299": "Tarla Hazırlığı_Ekipman Bakım Tamirat",

            # Gübreleme (03) kombinasyonları
            "0301": "Gübreleme_Gübre Uygulama",
            "0302": "Gübreleme_Gübre Uygulama Destek",
            "0397": "Gübreleme_Malzeme İndirme Yükleme",
            "0398": "Gübreleme_Malzeme Nakliye",
            "0399": "Gübreleme_Ekipman Bakım Tamirat",

            # Dikim (04) kombinasyonları
            "0401": "Dikim_Dikim",
            "0402": "Dikim_Dikim Destek",
            "0403": "Dikim_Aşılama",
            "0497": "Dikim_Malzeme İndirme Yükleme",
            "0498": "Dikim_Malzeme Nakliye",
            "0499": "Dikim_Ekipman Bakım Tamirat",

            # İlaçlama (05) kombinasyonları
            "0501": "İlaçlama_Herbicide Round-up",
            "0502": "İlaçlama_Herbicide Dual 960",
            "0503": "İlaçlama_Fungucide",
            "0504": "İlaçlama_Insecticide",
            "0505": "İlaçlama_Tarot",
            "0505": "İlaçlama_Herbicide Round-up destek",
            "0506": "İlaçlama_Herbicide Dual 960 destek",
            "0507": "İlaçlama_Fungucide destek",
            "0508": "İlaçlama_Insecticide destek",
            "0597": "İlaçlama_Malzeme İndirme Yükleme",
            "0598": "İlaçlama_Malzeme Nakliye",
            "0599": "İlaçlama_Ekipman Bakım Tamirat",

            # Sulama (06) kombinasyonları
            "0601": "Sulama_Sulama Kurulumu",
            "0602": "Sulama_Sulama",
            "0603": "Sulama_Sulama Tamir",
            "0697": "Sulama_Malzeme İndirme Yükleme",
            "0698": "Sulama_Malzeme Nakliye",
            "0699": "Sulama_Ekipman Bakım Tamirat",

            # Çapalama (07) kombinasyonları
            "0701": "Çapalama_Elle Çapalama",
            "0702": "Çapalama_Mekanik Çapalama",
            "0797": "Çapalama_Malzeme İndirme Yükleme",
            "0798": "Çapalama_Malzeme Nakliye",
            "0799": "Çapalama_Ekipman Bakım Tamirat",

            # Kırım (08) kombinasyonları
            "0801": "Kırım_Kırım",
            "0802": "Kırım_Kırım Destek",
            "0803": "Kırım_Kırımdan Dikiş Mak. Taşıma",
            "0897": "Kırım_Malzeme İndirme Yükleme",
            "0898": "Kırım_Malzeme Nakliye",
            "0899": "Kırım_Ekipman Bakım Tamirat",

            # Kurutma (09) kombinasyonları
            "0901": "Kurutma_Dikiş Mak.",
            "0902": "Kurutma_Dikiş Mak. Destek",
            "0903": "Kurutma_Dikiş Mak.Dan Seraya Taşıma",
            "0904": "Kurutma_Sera Kurutma Kontrol",
            "0905": "Kurutma_İstifleme",
            "0906": "Kurutma_Sera Kurulumu",
            "0907": "Kurutma_Seralarda Ot Temizliği",
            "0908": "Kurutma_Yaprak Kesme",
            "0909": "Kurutma_Fırın Bakım Ve Kontrol İşçiliği",
            "0910": "Kurutma_Fırına Taşıma Ve Yerleştirme İşçiliği",
            "0911": "Kurutma_Raks Doldurma İşçiliği",
            "0912": "Kurutma_Seraya Taşıma Ve Serme İşçiliği",
            "0913": "Kurutma_Yaprak Düzenleme İşçiliği",
            "0997": "Kurutma_Malzeme İndirme Yükleme",
            "0998": "Kurutma_Malzeme Nakliye",
            "0999": "Kurutma_Ekipman Bakım Tamirat",

            # Kutulama (10) kombinasyonları
            "1001": "Kutulama_Kutulama",
            "1002": "Kutulama_Tavlama",
            "1097": "Kutulama_Malzeme İndirme Yükleme",
            "1098": "Kutulama_Malzeme Nakliye",
            "1099": "Kutulama_Ekipman Bakım Tamirat",

            # Diğer (11) kombinasyonları
            "1101": "Diğer_Çevre Düzenleme",
            "1102": "Diğer_Kahya / Aile",
            "1103": "Diğer_Diğer",
            "1104": "Diğer_Dayıbaşı",
            "1105": "Diğer_Bakım",
            "1106": "Diğer_Tespit-Tesellüm",
            "1107": "Diğer_Kasko , Sigorta Poliçeleri",
            "1108": "Diğer_Müşteri Temsil Ağırlama",
            "1109": "Diğer_Ekipman Bakım Tamirat",
            "1197": "Diğer_Malzeme İndirme Yükleme",
            "1198": "Diğer_Malzeme Nakliye",
            "1199": "Diğer_Traktör , Römork Bakım Tamirat",

            # Nakliye (12) kombinasyonları
            "1298": "Nakliye_Gayrimamul",

            # Supervisor (13) kombinasyonları
            "1301": "Supervisor_Supervisor",

            # Kültürel İşlemler (14) kombinasyonları
            "1401": "Kültürel İşlemler_Sürgün Kontrol",
            "1402": "Kültürel İşlemler_Tepe Kırımı"
        }

        # Örnek bölge kodları (gerçek verilerinize göre güncellenmelidir)
        self.bolge_kodlari = {
            "10.": "ADY",
            "20.": "MNS",
            "30.": "MRD"
        }
    def _load_user_data(self):
        try:
            # Kullanıcı verilerini JSON dosyasından yükle
            if os.path.exists("user_data.json"):
                with open("user_data.json", "r", encoding="utf-8") as f:
                    user_data = json.load(f)

                # Kullanıcı verilerini mevcut verilere ekle
                if "kaynak_tipleri" in user_data:
                    self.kaynak_tipleri.update(user_data["kaynak_tipleri"])

                if "stages" in user_data:
                    self.stages.update(user_data["stages"])

                if "bolge_kodlari" in user_data:
                    self.bolge_kodlari.update(user_data["bolge_kodlari"])

                # Operasyonlar için özel birleştirme
                if "operasyonlar" in user_data:
                    for stage_id, ops in user_data["operasyonlar"].items():
                        if stage_id in self.operasyonlar:
                            self.operasyonlar[stage_id].update(ops)
                        else:
                            self.operasyonlar[stage_id] = ops

                # Stage-Operasyon kombinasyonlarını güncelle
                if "stage_operasyonlar" in user_data:
                    self.stage_operasyonlar.update(user_data["stage_operasyonlar"])

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Kullanıcı verileri yüklenirken hata oluştu: {str(e)}")
    def save_user_data(self):
        try:
            # Şu anki durumu bir sözlük olarak kaydet
            user_data = {
                "kaynak_tipleri": self.kaynak_tipleri,
                "stages": self.stages,
                "bolge_kodlari": self.bolge_kodlari,
                "operasyonlar": self.operasyonlar,
                "stage_operasyonlar": self.stage_operasyonlar
            }

            # JSON dosyasına kaydet
            with open("user_data.json", "w", encoding="utf-8") as f:
                json.dump(user_data, f, ensure_ascii=False, indent=4)

            QMessageBox.information(self, "Bilgi", "Veriler başarıyla kaydedildi.")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler kaydedilirken bir hata oluştu: {str(e)}")
    def setup_veri_yonetimi_tab(self):
        # Veri Yönetimi sekmesi
        self.load_data()

        self.veri_tab = QWidget()
        veri_layout = QVBoxLayout(self.veri_tab)

        # Tab widget
        veri_tabs = QTabWidget()

        # Bölge Kodları sekmesi
        bolge_tab = QWidget()
        bolge_layout = QVBoxLayout(bolge_tab)
        self.operasyon_table = QTableWidget()
        # Tablo
        self.bolge_table = QTableWidget()
        self.bolge_table.setColumnCount(2)
        self.bolge_table.setHorizontalHeaderLabels(["Kod", "Açıklama"])
        self.bolge_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        # Tabloyu doldur
        self.populate_bolge_table()

        # Butonlar
        bolge_button_layout = QHBoxLayout()
        add_bolge_button = QPushButton("Ekle")
        add_bolge_button.clicked.connect(self.add_bolge)
        edit_bolge_button = QPushButton("Düzenle")
        edit_bolge_button.clicked.connect(self.edit_bolge)
        delete_bolge_button = QPushButton("Sil")
        delete_bolge_button.clicked.connect(self.delete_bolge)

        bolge_button_layout.addWidget(add_bolge_button)
        bolge_button_layout.addWidget(edit_bolge_button)
        bolge_button_layout.addWidget(delete_bolge_button)

        bolge_layout.addWidget(self.bolge_table)
        bolge_layout.addLayout(bolge_button_layout)

        # Kaynak Tipleri sekmesi
        kaynak_tab = QWidget()
        kaynak_layout = QVBoxLayout(kaynak_tab)

        # Tablo
        self.kaynak_table = QTableWidget()
        self.kaynak_table.setColumnCount(2)
        self.kaynak_table.setHorizontalHeaderLabels(["Kod", "Açıklama"])
        self.kaynak_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        # Tabloyu doldur
        self.populate_kaynak_table()

        # Butonlar
        kaynak_button_layout = QHBoxLayout()
        add_kaynak_button = QPushButton("Ekle")
        add_kaynak_button.clicked.connect(self.add_kaynak)
        edit_kaynak_button = QPushButton("Düzenle")
        edit_kaynak_button.clicked.connect(self.edit_kaynak)
        delete_kaynak_button = QPushButton("Sil")
        delete_kaynak_button.clicked.connect(self.delete_kaynak)

        kaynak_button_layout.addWidget(add_kaynak_button)
        kaynak_button_layout.addWidget(edit_kaynak_button)
        kaynak_button_layout.addWidget(delete_kaynak_button)

        kaynak_layout.addWidget(self.kaynak_table)
        kaynak_layout.addLayout(kaynak_button_layout)

        # Stage sekmesi
        stage_tab = QWidget()
        stage_layout = QVBoxLayout(stage_tab)

        # Tablo
        self.stage_table = QTableWidget()
        self.stage_table.setColumnCount(2)
        self.stage_table.setHorizontalHeaderLabels(["Kod", "Açıklama"])
        self.stage_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        # Tabloyu doldur
        self.populate_stage_table()

        # Butonlar
        stage_button_layout = QHBoxLayout()
        add_stage_button = QPushButton("Ekle")
        add_stage_button.clicked.connect(self.add_stage)
        edit_stage_button = QPushButton("Düzenle")
        edit_stage_button.clicked.connect(self.edit_stage)
        delete_stage_button = QPushButton("Sil")
        delete_stage_button.clicked.connect(self.delete_stage)

        stage_button_layout.addWidget(add_stage_button)
        stage_button_layout.addWidget(edit_stage_button)
        stage_button_layout.addWidget(delete_stage_button)

        stage_layout.addWidget(self.stage_table)
        stage_layout.addLayout(stage_button_layout)

        # Operasyon sekmesi
        operasyon_tab = QWidget()
        operasyon_layout = QVBoxLayout(operasyon_tab)

        # Stage seçimi
        stage_select_layout = QHBoxLayout()
        stage_select_layout.addWidget(QLabel("Stage:"))
        self.operasyon_stage_combo = QComboBox()
        self.operasyon_stage_combo.currentIndexChanged.connect(self.populate_operasyon_table)
        stage_select_layout.addWidget(self.operasyon_stage_combo)

        # Combobox'ı doldur
        for code, name in self.stages.items():
            self.operasyon_stage_combo.addItem(f"{code} - {name}", code)

        # Tablo
        self.operasyon_table.setColumnCount(2)
        self.operasyon_table.setHorizontalHeaderLabels(["Kod", "Açıklama"])
        self.operasyon_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        # Butonlar
        operasyon_button_layout = QHBoxLayout()
        add_operasyon_button = QPushButton("Ekle")
        add_operasyon_button.clicked.connect(self.add_operasyon)
        edit_operasyon_button = QPushButton("Düzenle")
        edit_operasyon_button.clicked.connect(self.edit_operasyon)
        delete_operasyon_button = QPushButton("Sil")
        delete_operasyon_button.clicked.connect(self.delete_operasyon)

        operasyon_button_layout.addWidget(add_operasyon_button)
        operasyon_button_layout.addWidget(edit_operasyon_button)
        operasyon_button_layout.addWidget(delete_operasyon_button)

        operasyon_layout.addLayout(stage_select_layout)
        operasyon_layout.addWidget(self.operasyon_table)
        operasyon_layout.addLayout(operasyon_button_layout)

        # Kaydet ve geri yükle butonları
        save_button = QPushButton("Değişiklikleri Kaydet")
        save_button.clicked.connect(self.save_user_data)
        reset_button = QPushButton("Varsayılan Değerlere Sıfırla")
        reset_button.clicked.connect(self.reset_to_defaults)

        # Sekmeleri ekleme
        veri_tabs.addTab(bolge_tab, "Bölge Kodları")
        veri_tabs.addTab(kaynak_tab, "Kaynak Tipleri")
        veri_tabs.addTab(stage_tab, "Stage")
        veri_tabs.addTab(operasyon_tab, "Operasyonlar")

        veri_layout.addWidget(veri_tabs)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(reset_button)
        veri_layout.addLayout(buttons_layout)

        # Tab'ı ana widget'a ekle
        self.tabs.addTab(self.veri_tab, "Kod İşlemleri")

        # İlk seçili stage için operasyon tablosunu doldur
        self.populate_operasyon_table()
    # Tablo doldurma fonksiyonları
    def populate_bolge_table(self):
        self.bolge_table.setRowCount(0)
        for row_idx, (code, desc) in enumerate(sorted(self.bolge_kodlari.items())):
            self.bolge_table.insertRow(row_idx)
            self.bolge_table.setItem(row_idx, 0, QTableWidgetItem(code))
            self.bolge_table.setItem(row_idx, 1, QTableWidgetItem(desc))
    def populate_kaynak_table(self):
        self.kaynak_table.setRowCount(0)
        for row_idx, (code, desc) in enumerate(sorted(self.kaynak_tipleri.items())):
            self.kaynak_table.insertRow(row_idx)
            self.kaynak_table.setItem(row_idx, 0, QTableWidgetItem(code))
            self.kaynak_table.setItem(row_idx, 1, QTableWidgetItem(desc))
        #self.stage_table.setRowCount(0)
    def populate_stage_table(self):
        for row_idx, (code, desc) in enumerate(sorted(self.stages.items())):
            self.stage_table.insertRow(row_idx)
            self.stage_table.setItem(row_idx, 0, QTableWidgetItem(code))
            self.stage_table.setItem(row_idx, 1, QTableWidgetItem(desc))
    def populate_operasyon_table(self):
        self.operasyon_table.setRowCount(0)

        # Seçili stage kodunu al
        current_stage = self.operasyon_stage_combo.currentData()
        if not current_stage or current_stage not in self.operasyonlar:
            return

        # Seçili stage için operasyonları doldur
        for row_idx, (code, desc) in enumerate(sorted(self.operasyonlar[current_stage].items())):
            self.operasyon_table.insertRow(row_idx)
            self.operasyon_table.setItem(row_idx, 0, QTableWidgetItem(code))
            self.operasyon_table.setItem(row_idx, 1, QTableWidgetItem(desc))
    # Dialog fonksiyonları
    def show_code_dialog(self, title, code="", desc="", editable_code=True):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)

        form_layout = QFormLayout()

        code_input = QLineEdit(code)
        code_input.setEnabled(editable_code)
        desc_input = QLineEdit(desc)

        form_layout.addRow("Kod:", code_input)
        form_layout.addRow("Açıklama:", desc_input)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        layout.addWidget(button_box)

        result = dialog.exec_()
        if result == QDialog.Accepted:
            return code_input.text(), desc_input.text()
        return None, None
    # Ekleme/Düzenleme/Silme fonksiyonları
    def add_bolge(self):
        code, desc = self.show_code_dialog("Bölge Ekle")
        if code and desc:
            if code in self.bolge_kodlari:
                QMessageBox.warning(self, "Uyarı", "Bu kod zaten kullanılıyor.")
                return
            self.bolge_kodlari[code] = desc
            self.populate_bolge_table()
    def edit_bolge(self):
        selected_items = self.bolge_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlenecek bir satır seçin.")
            return

        row = selected_items[0].row()
        code = self.bolge_table.item(row, 0).text()
        desc = self.bolge_table.item(row, 1).text()

        _, new_desc = self.show_code_dialog("Bölge Düzenle", code, desc, False)
        if new_desc:
            self.bolge_kodlari[code] = new_desc
            self.populate_bolge_table()
    def delete_bolge(self):
        selected_items = self.bolge_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek bir satır seçin.")
            return

        row = selected_items[0].row()
        code = self.bolge_table.item(row, 0).text()

        reply = QMessageBox.question(self, "Onay",
                                     f"'{code}' kodlu bölgeyi silmek istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            del self.bolge_kodlari[code]
            self.populate_bolge_table()
    # Benzer şekilde kaynak, stage ve operasyon için ekleme/düzenleme/silme fonksiyonları...
    def add_kaynak(self):
        code, desc = self.show_code_dialog("Kaynak Tipi Ekle")
        if code and desc:
            if code in self.kaynak_tipleri:
                QMessageBox.warning(self, "Uyarı", "Bu kod zaten kullanılıyor.")
                return
            self.kaynak_tipleri[code] = desc
            self.populate_kaynak_table()
    def edit_kaynak(self):
        selected_items = self.kaynak_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlenecek bir satır seçin.")
            return

        row = selected_items[0].row()
        code = self.kaynak_table.item(row, 0).text()
        desc = self.kaynak_table.item(row, 1).text()

        _, new_desc = self.show_code_dialog("Kaynak Tipi Düzenle", code, desc, False)
        if new_desc:
            self.kaynak_tipleri[code] = new_desc
            self.populate_kaynak_table()
    def delete_kaynak(self):
        selected_items = self.kaynak_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek bir satır seçin.")
            return

        row = selected_items[0].row()
        code = self.kaynak_table.item(row, 0).text()

        reply = QMessageBox.question(self, "Onay",
                                     f"'{code}' kodlu kaynak tipini silmek istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            del self.kaynak_tipleri[code]
            self.populate_kaynak_table()
    def add_stage(self):
        code, desc = self.show_code_dialog("Stage Ekle")
        if code and desc:
            if code in self.stages:
                QMessageBox.warning(self, "Uyarı", "Bu kod zaten kullanılıyor.")
                return
            self.stages[code] = desc
            self.operasyonlar[code] = {}  # Yeni stage için boş operasyon listesi oluştur
            self.populate_stage_table()

            # Stage combobox'ı güncelle
            self.operasyon_stage_combo.addItem(f"{code} - {desc}", code)
    def edit_stage(self):
        selected_items = self.stage_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlenecek bir satır seçin.")
            return

        row = selected_items[0].row()
        code = self.stage_table.item(row, 0).text()
        desc = self.stage_table.item(row, 1).text()

        _, new_desc = self.show_code_dialog("Stage Düzenle", code, desc, False)
        if new_desc:
            self.stages[code] = new_desc
            self.populate_stage_table()

            # Stage combobox'ı güncelle
            for i in range(self.operasyon_stage_combo.count()):
                if self.operasyon_stage_combo.itemData(i) == code:
                    self.operasyon_stage_combo.setItemText(i, f"{code} - {new_desc}")
                    break
    def delete_stage(self):
        selected_items = self.stage_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek bir satır seçin.")
            return

        row = selected_items[0].row()
        code = self.stage_table.item(row, 0).text()

        reply = QMessageBox.question(self, "Onay",
                                     f"'{code}' kodlu stage'i silmek istediğinize emin misiniz? İlgili tüm operasyonlar da silinecektir.",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            del self.stages[code]
            if code in self.operasyonlar:
                del self.operasyonlar[code]

            # Stage-operasyon kombinasyonlarını temizle
            keys_to_delete = []
            for key in self.stage_operasyonlar.keys():
                if key.startswith(code):
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self.stage_operasyonlar[key]

            self.populate_stage_table()

            # Stage combobox'ı güncelle
            for i in range(self.operasyon_stage_combo.count()):
                if self.operasyon_stage_combo.itemData(i) == code:
                    self.operasyon_stage_combo.removeItem(i)
                    break
    def add_operasyon(self):
        current_stage = self.operasyon_stage_combo.currentData()
        if not current_stage:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir stage seçin.")
            return

        code, desc = self.show_code_dialog("Operasyon Ekle")
        if code and desc:
            if code in self.operasyonlar[current_stage]:
                QMessageBox.warning(self, "Uyarı", "Bu kod zaten kullanılıyor.")
                return

            self.operasyonlar[current_stage][code] = desc

            # Stage-operasyon kombinasyonunu da ekle
            combined_key = f"{current_stage}{code}"
            stage_name = self.stages[current_stage]
            combined_value = f"{stage_name}_{desc}"
            self.stage_operasyonlar[combined_key] = combined_value

            self.populate_operasyon_table()
    def edit_operasyon(self):
        current_stage = self.operasyon_stage_combo.currentData()
        if not current_stage:
            return

        selected_items = self.operasyon_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlenecek bir satır seçin.")
            return

        row = selected_items[0].row()
        code = self.operasyon_table.item(row, 0).text()
        desc = self.operasyon_table.item(row, 1).text()

        _, new_desc = self.show_code_dialog("Operasyon Düzenle", code, desc, False)
        if new_desc:
            self.operasyonlar[current_stage][code] = new_desc

            # Stage-operasyon kombinasyonunu da güncelle
            combined_key = f"{current_stage}{code}"
            stage_name = self.stages[current_stage]
            combined_value = f"{stage_name}_{new_desc}"
            self.stage_operasyonlar[combined_key] = combined_value

            self.populate_operasyon_table()
    def delete_operasyon(self):
        current_stage = self.operasyon_stage_combo.currentData()
        if not current_stage:
            return

        selected_items = self.operasyon_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek bir satır seçin.")
            return

        row = selected_items[0].row()
        code = self.operasyon_table.item(row, 0).text()

        reply = QMessageBox.question(self, "Onay",
                                     f"'{code}' kodlu operasyonu silmek istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            del self.operasyonlar[current_stage][code]

            # Stage-operasyon kombinasyonunu da sil
            combined_key = f"{current_stage}{code}"
            if combined_key in self.stage_operasyonlar:
                del self.stage_operasyonlar[combined_key]

            self.populate_operasyon_table()
    def reset_to_defaults(self):
        reply = QMessageBox.question(self, "Onay",
                                     "Tüm verileri varsayılan değerlere sıfırlamak istediğinize emin misiniz? Bu işlem geri alınamaz.",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Kullanıcı veri dosyasını sil (varsa)
            if os.path.exists("user_data.json"):
                os.remove("user_data.json")

            # Varsayılan verileri tekrar yükle
            self._load_default_data()

            # Tabloları güncelle
            self.populate_bolge_table()
            self.populate_kaynak_table()
            self.populate_stage_table()

            # Stage combobox'ı güncelle
            self.operasyon_stage_combo.clear()
            for code, name in self.stages.items():
                self.operasyon_stage_combo.addItem(f"{code} - {name}", code)

            self.populate_operasyon_table()

            QMessageBox.information(self, "Bilgi", "Veriler varsayılan değerlere sıfırlandı.")
def get_resource_path(filename):
    """Uygulamanın çalıştığı dizinde dosya yolunu al (exe veya geliştirici modunda)"""
    if getattr(sys, 'frozen', False):  # Eğer exe olarak çalışıyorsa
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

def main():
    app = QApplication(sys.argv)

    def copy_data_file_if_needed():
        """user_data.json dosyasını doğru dizine kopyalar"""
        user_data_path = get_resource_path("user_data.json")
        if not os.path.exists(user_data_path):
            shutil.copy('user_data.json', user_data_path)

    # Uygulama başlatıldığında çalıştır
    copy_data_file_if_needed()

    # Style dosyasını dinamik olarak yükle
    style_path = get_resource_path("style.qss")
    with open(style_path, "r") as f:
        app.setStyleSheet(f.read())

    window = HarcamaMasrafApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
