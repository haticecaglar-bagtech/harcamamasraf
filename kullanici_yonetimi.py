#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kullanıcı Yönetim Scripti
Bu script ile kullanıcı ekleyebilir, rol atayabilir ve bölge kodları tanımlayabilirsiniz.
"""

import sys
import os
import requests
from werkzeug.security import generate_password_hash

# API base URL
API_BASE_URL = "http://127.0.0.1:5000"

def print_menu():
    """Ana menüyü göster"""
    print("\n" + "="*50)
    print("KULLANICI YÖNETİM SİSTEMİ")
    print("="*50)
    print("1. Yeni Kullanıcı Ekle")
    print("2. Kullanıcı Rolü Güncelle")
    print("3. Kullanıcıya Bölge Ekle")
    print("4. Kullanıcı Bilgilerini Görüntüle")
    print("5. Tüm Kullanıcıları Listele")
    print("0. Çıkış")
    print("="*50)

def add_user():
    """Yeni kullanıcı ekle"""
    print("\n--- Yeni Kullanıcı Ekleme ---")
    username = input("Kullanıcı Adı: ").strip()
    password = input("Şifre: ").strip()
    
    if not username or not password:
        print("❌ Kullanıcı adı ve şifre boş olamaz!")
        return
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/register", json={
            'username': username,
            'password': password
        })
        
        if response.status_code == 201:
            print(f"✅ Kullanıcı '{username}' başarıyla eklendi!")
            
            # Rol atama
            assign_role = input("\nRol atamak ister misiniz? (e/h): ").strip().lower()
            if assign_role == 'e':
                update_user_role_with_username(username)
            
            # Bölge atama
            assign_bolge = input("\nBölge kodu eklemek ister misiniz? (e/h): ").strip().lower()
            if assign_bolge == 'e':
                add_user_bolge_with_username(username)
        else:
            error_data = response.json()
            print(f"❌ Hata: {error_data.get('error', 'Bilinmeyen hata')}")
    except Exception as e:
        print(f"❌ Hata: {str(e)}")

def update_user_role():
    """Kullanıcı rolü güncelle"""
    print("\n--- Kullanıcı Rolü Güncelleme ---")
    username = input("Kullanıcı Adı: ").strip()
    update_user_role_with_username(username)

def update_user_role_with_username(username):
    """Kullanıcı rolü güncelle (username ile)"""
    
    print("\nRol Seçenekleri:")
    print("1. normal - Normal Kullanıcı")
    print("2. admin - Admin")
    print("3. ust_duzey_yonetici - Üst Düzey Yönetici")
    
    role_choice = input("Rol seçiniz (1/2/3): ").strip()
    role_map = {
        '1': 'normal',
        '2': 'admin',
        '3': 'ust_duzey_yonetici'
    }
    
    role = role_map.get(role_choice)
    if not role:
        print("❌ Geçersiz rol seçimi!")
        return
    
    try:
        response = requests.put(f"{API_BASE_URL}/api/users/{username}/role", json={
            'role': role
        })
        
        if response.status_code == 200:
            print(f"✅ Kullanıcı '{username}' rolü '{role}' olarak güncellendi!")
        else:
            error_data = response.json()
            print(f"❌ Hata: {error_data.get('error', 'Bilinmeyen hata')}")
    except Exception as e:
        print(f"❌ Hata: {str(e)}")

def add_user_bolge():
    """Kullanıcıya bölge ekle"""
    print("\n--- Kullanıcıya Bölge Ekleme ---")
    username = input("Kullanıcı Adı: ").strip()
    add_user_bolge_with_username(username)

def add_user_bolge_with_username(username):
    """Kullanıcıya bölge ekle (username ile)"""
    
    # Ana bölge kodlarını göster
    print("\n" + "="*50)
    print("ANA BÖLGE KODLARI (Alt bölgeler otomatik eklenir):")
    print("="*50)
    print("  10 - ADY - DOĞU")
    print("  11 - ADY - BATI")
    print("  20 - MAN")
    print("  30 - MAR")
    print("="*50)
    print("\n💡 İpucu: Ana bölge kodunu (10, 11, 20, 30) eklediğinizde,")
    print("   o ana bölgeye ait tüm alt bölgeler otomatik olarak eklenir!")
    print("\nÖrnek: MAN (20) eklediğinizde şunlar da eklenir:")
    print("  - 21 (MAN - FCV MAK.)")
    print("  - 24 (MAN - N.RUSTICA)")
    print("  - 25 (MAN - IZMIR)")
    print("  - 22 (MAN-JTI SCV)")
    print("  - 26 (MAN-SCV TOPPING)")
    print("  - 23 (MAN-PMI SCV)")
    print("="*50)
    
    # Tüm bölge kodlarını da göster (opsiyonel)
    show_all = input("\nTüm bölge kodlarını görmek ister misiniz? (e/h): ").strip().lower()
    if show_all == 'e':
        try:
            response = requests.get(f"{API_BASE_URL}/api/bolge_kodlari")
            if response.status_code == 200:
                bolge_kodlari = response.json()
                print("\nTüm Bölge Kodları:")
                for kod, ad in sorted(bolge_kodlari.items()):
                    # Ana bölgeleri vurgula
                    if kod in ['10', '11', '20', '30']:
                        print(f"  ⭐ {kod}: {ad} (ANA BÖLGE)")
                    else:
                        print(f"     {kod}: {ad}")
        except:
            print("⚠️ Bölge kodları yüklenemedi.")
    
    bolge_kodu = input("\nBölge Kodu (Ana bölge: 10, 11, 20, 30 veya alt bölge): ").strip()
    
    if not bolge_kodu:
        print("❌ Bölge kodu boş olamaz!")
        return
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/users/{username}/bolge", json={
            'bolge_kodu': bolge_kodu
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ {data.get('message', 'Başarılı!')}")
            
            # Eklenen bölgeleri göster
            if 'eklenen_bolgeler' in data and data['eklenen_bolgeler']:
                print(f"\n📋 Eklenen Bölgeler ({len(data['eklenen_bolgeler'])} adet):")
                for bolge in data['eklenen_bolgeler']:
                    print(f"   - {bolge}")
            
            if 'zaten_var_olanlar' in data and data['zaten_var_olanlar']:
                print(f"\n⚠️ Zaten Mevcut Olanlar ({len(data['zaten_var_olanlar'])} adet):")
                for bolge in data['zaten_var_olanlar']:
                    print(f"   - {bolge}")
        else:
            error_data = response.json()
            print(f"❌ Hata: {error_data.get('message', error_data.get('error', 'Bilinmeyen hata'))}")
    except Exception as e:
        print(f"❌ Hata: {str(e)}")

def view_user_info():
    """Kullanıcı bilgilerini görüntüle"""
    print("\n--- Kullanıcı Bilgileri ---")
    username = input("Kullanıcı Adı: ").strip()
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/users/{username}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"\nKullanıcı Bilgileri:")
            print(f"  Kullanıcı Adı: {user_data.get('username')}")
            print(f"  Rol: {user_data.get('role', 'normal')}")
            print(f"  Varsayılan Bölge: {user_data.get('default_bolge_kodu', 'Yok')}")
            print(f"  Bölge Kodları:")
            bolge_kodlari = user_data.get('bolge_kodlari', [])
            if bolge_kodlari:
                for kod in bolge_kodlari:
                    print(f"    - {kod}")
            else:
                print("    (Bölge kodu atanmamış)")
        else:
            error_data = response.json()
            print(f"❌ Hata: {error_data.get('error', 'Kullanıcı bulunamadı')}")
    except Exception as e:
        print(f"❌ Hata: {str(e)}")

def list_all_users():
    """Tüm kullanıcıları listele"""
    print("\n--- Tüm Kullanıcılar ---")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/users")
        
        if response.status_code == 200:
            users = response.json().get('users', [])
            if users:
                print(f"\nToplam {len(users)} kullanıcı bulundu:\n")
                for user in users:
                    print(f"  Kullanıcı Adı: {user.get('username')}")
                    print(f"  Rol: {user.get('role', 'normal')}")
                    print(f"  Bölge Kodları: {', '.join(user.get('bolge_kodlari', [])) or 'Yok'}")
                    print("-" * 40)
            else:
                print("❌ Kullanıcı bulunamadı!")
        else:
            print("❌ Kullanıcılar yüklenemedi!")
    except Exception as e:
        print(f"❌ Hata: {str(e)}")

def main():
    """Ana fonksiyon"""
    print("\n🚀 Kullanıcı Yönetim Sistemine Hoş Geldiniz!")
    print("⚠️  Not: API sunucusunun çalıştığından emin olun (http://127.0.0.1:5000)")
    
    while True:
        print_menu()
        choice = input("\nSeçiminiz: ").strip()
        
        if choice == '1':
            add_user()
        elif choice == '2':
            update_user_role()
        elif choice == '3':
            add_user_bolge()
        elif choice == '4':
            view_user_info()
        elif choice == '5':
            list_all_users()
        elif choice == '0':
            print("\n👋 Çıkılıyor...")
            break
        else:
            print("❌ Geçersiz seçim! Lütfen tekrar deneyin.")
        
        input("\nDevam etmek için Enter'a basın...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Program sonlandırıldı.")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {str(e)}")

