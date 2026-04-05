from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QLineEdit, QDialog,
                             QDialogButtonBox, QFormLayout, QGroupBox, QGridLayout,
                             QCheckBox, QListWidget, QListWidgetItem, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import requests
from config import get_api_root


class KullaniciYonetimiTab(QWidget):
    def __init__(self, api_client, admin_user_id, admin_username, admin_password):
        super().__init__()
        self.api_client = api_client
        self.admin_user_id = admin_user_id
        self.admin_username = admin_username
        self.admin_password = admin_password
        
        try:
            self.setup_ui()
            self.load_users()
        except Exception as e:
            print(f"DEBUG - KullaniciYonetimiTab init hatası: {str(e)}")
            import traceback
            traceback.print_exc()
            # Hata olsa bile UI'yi göster
            self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Başlık
        title = QLabel("👥 Kullanıcı Yönetimi")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        add_user_btn = QPushButton("➕ Yeni Kullanıcı Ekle")
        add_user_btn.clicked.connect(self.show_add_user_dialog)
        add_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                font-size: 14px;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #047857;
            }
        """)
        button_layout.addWidget(add_user_btn)
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.load_users)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                font-size: 14px;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        
        # Kullanıcı tablosu
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels([
            "Kullanıcı Adı", "Rol", "Bölgeler", "İşlemler", "Sil"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.users_table)
    
    def load_users(self):
        """Tüm kullanıcıları yükle"""
        try:
            response = requests.get(f"{get_api_root()}/users")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    users = data.get('data', [])
                    
                    self.users_table.setRowCount(len(users))
                    
                    for row_idx, user in enumerate(users):
                        username = user.get('username', '')
                        role = user.get('role', 'normal')
                        bolgeler = ', '.join(user.get('bolge_kodlari', []))  # 'bolgeler' yerine 'bolge_kodlari'
                        
                        # Kullanıcı adı
                        self.users_table.setItem(row_idx, 0, QTableWidgetItem(username))
                        
                        # Rol
                        role_item = QTableWidgetItem(role)
                        self.users_table.setItem(row_idx, 1, role_item)
                        
                        # Bölgeler
                        self.users_table.setItem(row_idx, 2, QTableWidgetItem(bolgeler))
                        
                        # İşlemler butonu
                        actions_btn = QPushButton("⚙️ Düzenle")
                        actions_btn.clicked.connect(lambda checked, u=username: self.edit_user(u))
                        actions_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #8b5cf6;
                                color: white;
                                padding: 5px 10px;
                                border-radius: 3px;
                            }
                            QPushButton:hover {
                                background-color: #7c3aed;
                            }
                        """)
                        self.users_table.setCellWidget(row_idx, 3, actions_btn)
                        
                        # Sil butonu (admin kendini silemez)
                        if username != self.admin_username:
                            delete_btn = QPushButton("🗑️ Sil")
                            delete_btn.clicked.connect(lambda checked, u=username: self.delete_user(u))
                            delete_btn.setStyleSheet("""
                                QPushButton {
                                    background-color: #ef4444;
                                    color: white;
                                    padding: 5px 10px;
                                    border-radius: 3px;
                                }
                                QPushButton:hover {
                                    background-color: #dc2626;
                                }
                            """)
                            self.users_table.setCellWidget(row_idx, 4, delete_btn)
                        else:
                            self.users_table.setItem(row_idx, 4, QTableWidgetItem("-"))
                else:
                    QMessageBox.warning(self, "Uyarı", "Kullanıcılar yüklenemedi.")
            else:
                QMessageBox.critical(self, "Hata", f"Sunucu hatası: {response.status_code}")
        except Exception as e:
            print(f"DEBUG - Kullanıcılar yüklenirken hata: {str(e)}")
            import traceback
            traceback.print_exc()
            # QMessageBox yerine sadece print yapıyoruz (init sırasında widget henüz gösterilmemiş olabilir)
            # QMessageBox.critical(self, "Hata", f"Kullanıcılar yüklenirken hata oluştu: {str(e)}")
    
    def show_add_user_dialog(self):
        """Yeni kullanıcı ekleme dialog'u"""
        # Admin şifresini sor
        admin_password, ok = QInputDialog.getText(
            self, 
            "Admin Şifresi", 
            "Kullanıcı eklemek için admin şifrenizi girin:",
            QLineEdit.Password
        )
        
        if not ok or not admin_password:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Yeni Kullanıcı Ekle")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        # Form alanları
        username_edit = QLineEdit()
        username_edit.setPlaceholderText("Kullanıcı adı")
        layout.addRow("Kullanıcı Adı:", username_edit)
        
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.Password)
        password_edit.setPlaceholderText("Şifre")
        layout.addRow("Şifre:", password_edit)
        
        role_combo = QComboBox()
        role_combo.addItem("Normal Kullanıcı", "normal")
        role_combo.addItem("Admin", "admin")
        role_combo.addItem("Üst Düzey Yönetici", "ust_duzey_yonetici")
        layout.addRow("Rol:", role_combo)
        
        # Bölge seçimi
        bolge_group = QGroupBox("Bölgeler")
        bolge_layout = QVBoxLayout()
        self.bolge_list = QListWidget()
        
        # Tüm bölgeleri yükle
        try:
            response = requests.get(f"{get_api_root()}/bolge_kodlari")
            if response.status_code == 200:
                bolge_kodlari = response.json()
                for kod, ad in bolge_kodlari.items():
                    item = QListWidgetItem(f"{ad} ({kod})")
                    item.setData(Qt.UserRole, kod)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Unchecked)
                    self.bolge_list.addItem(item)
        except Exception as e:
            print(f"Bölge kodları yüklenirken hata: {e}")
        
        bolge_layout.addWidget(self.bolge_list)
        bolge_group.setLayout(bolge_layout)
        layout.addRow(bolge_group)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            username = username_edit.text().strip()
            password = password_edit.text().strip()
            role = role_combo.currentData()
            
            if not username or not password:
                QMessageBox.warning(self, "Uyarı", "Kullanıcı adı ve şifre boş olamaz!")
                return
            
            # Kullanıcıyı ekle
            try:
                response = requests.post(f"{get_api_root()}/register", json={
                    'username': username,
                    'password': password,
                    'admin_username': self.admin_username,
                    'admin_password': admin_password
                })
                
                if response.status_code == 201:
                    # Rol atama
                    if role != 'normal':
                        role_response = requests.put(
                            f"{get_api_root()}/users/{username}/role",
                            json={'role': role}
                        )
                    
                    # Bölge atama
                    selected_bolgeler = []
                    for i in range(self.bolge_list.count()):
                        item = self.bolge_list.item(i)
                        if item.checkState() == Qt.Checked:
                            bolge_kodu = item.data(Qt.UserRole)
                            selected_bolgeler.append(bolge_kodu)
                            
                            # Her bölgeyi ekle
                            bolge_response = requests.post(
                                f"{get_api_root()}/users/{username}/bolge",
                                json={'bolge_kodu': bolge_kodu}
                            )
                    
                    QMessageBox.information(self, "Başarılı", 
                        f"Kullanıcı '{username}' başarıyla eklendi!\n"
                        f"Rol: {role}\n"
                        f"Bölgeler: {', '.join(selected_bolgeler) if selected_bolgeler else 'Yok'}")
                    self.load_users()
                else:
                    error_data = response.json()
                    QMessageBox.critical(self, "Hata", 
                        f"Kullanıcı eklenemedi: {error_data.get('error', 'Bilinmeyen hata')}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kullanıcı eklenirken hata: {str(e)}")
    
    def edit_user(self, username):
        """Kullanıcı düzenleme dialog'u"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Kullanıcı Düzenle: {username}")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        # Kullanıcı bilgilerini al
        try:
            response = requests.get(f"{get_api_root()}/users/{username}")
            if response.status_code != 200:
                QMessageBox.warning(self, "Uyarı", "Kullanıcı bilgileri alınamadı.")
                return
            
            user_data = response.json()
            current_role = user_data.get('role', 'normal')
            current_bolgeler = set(user_data.get('bolgeler', []))
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kullanıcı bilgileri alınırken hata: {str(e)}")
            return
        
        # Kullanıcı adı (değiştirilemez)
        username_label = QLabel(username)
        username_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addRow("Kullanıcı Adı:", username_label)
        
        # Rol seçimi
        role_combo = QComboBox()
        role_combo.addItem("Normal Kullanıcı", "normal")
        role_combo.addItem("Admin", "admin")
        role_combo.addItem("Üst Düzey Yönetici", "ust_duzey_yonetici")
        
        # Mevcut rolü seç
        index = role_combo.findData(current_role)
        if index >= 0:
            role_combo.setCurrentIndex(index)
        
        layout.addRow("Rol:", role_combo)
        
        # Şifre değiştirme
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.Password)
        password_edit.setPlaceholderText("Yeni şifre (boş bırakılırsa değişmez)")
        layout.addRow("Yeni Şifre:", password_edit)
        
        # Bölge seçimi
        bolge_group = QGroupBox("Bölgeler")
        bolge_layout = QVBoxLayout()
        bolge_list = QListWidget()
        
        # Tüm bölgeleri yükle
        try:
            response = requests.get(f"{get_api_root()}/bolge_kodlari")
            if response.status_code == 200:
                bolge_kodlari = response.json()
                for kod, ad in bolge_kodlari.items():
                    item = QListWidgetItem(f"{ad} ({kod})")
                    item.setData(Qt.UserRole, kod)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    # Mevcut bölgeleri işaretle
                    if kod in current_bolgeler:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
                    bolge_list.addItem(item)
        except Exception as e:
            print(f"Bölge kodları yüklenirken hata: {e}")
        
        bolge_layout.addWidget(bolge_list)
        bolge_group.setLayout(bolge_layout)
        layout.addRow(bolge_group)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            # Rol güncelleme
            new_role = role_combo.currentData()
            if new_role != current_role:
                try:
                    role_response = requests.put(
                        f"{get_api_root()}/users/{username}/role",
                        json={'role': new_role}
                    )
                    if role_response.status_code == 200:
                        QMessageBox.information(self, "Başarılı", f"Rol '{new_role}' olarak güncellendi.")
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"Rol güncellenirken hata: {str(e)}")
            
            # Şifre güncelleme (eğer girildiyse)
            new_password = password_edit.text().strip()
            if new_password:
                # Şifre güncelleme endpoint'i yoksa burada eklenebilir
                QMessageBox.information(self, "Bilgi", "Şifre güncelleme özelliği yakında eklenecek.")
            
            # Bölge güncelleme
            selected_bolgeler = set()
            for i in range(bolge_list.count()):
                item = bolge_list.item(i)
                if item.checkState() == Qt.Checked:
                    bolge_kodu = item.data(Qt.UserRole)
                    selected_bolgeler.add(bolge_kodu)
            
            # Eklenecek bölgeler
            to_add = selected_bolgeler - current_bolgeler
            # Silinecek bölgeler
            to_remove = current_bolgeler - selected_bolgeler
            
            # Bölgeleri ekle
            for bolge_kodu in to_add:
                try:
                    requests.post(
                        f"{get_api_root()}/users/{username}/bolge",
                        json={'bolge_kodu': bolge_kodu}
                    )
                except Exception as e:
                    print(f"Bölge eklenirken hata: {e}")
            
            # Bölgeleri sil (API endpoint'i gerekli)
            if to_remove:
                QMessageBox.information(self, "Bilgi", 
                    f"Bölge silme özelliği yakında eklenecek.\n"
                    f"Silinecek bölgeler: {', '.join(to_remove)}")
            
            self.load_users()
    
    def delete_user(self, username):
        """Kullanıcı silme"""
        reply = QMessageBox.question(self, "Onay", 
            f"'{username}' kullanıcısını silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Silme endpoint'i yoksa burada eklenebilir
            QMessageBox.information(self, "Bilgi", "Kullanıcı silme özelliği yakında eklenecek.")
            # self.load_users()

