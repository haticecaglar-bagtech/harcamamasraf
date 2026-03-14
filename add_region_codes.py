#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bölge kodlarını veritabanına ekleme scripti
Bu script, görüntüdeki bölge kodlarını API üzerinden veritabanına ekler.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_client import ApiClient

def main():
    """Ana fonksiyon - bölge kodlarını ekler"""
    
    # API client oluştur
    api_client = ApiClient()
    
    # Görüntüdeki bölge kodları listesi
    bolge_listesi = [
        {"kod": "10", "ad": "ADY - DOĞU"},
        {"kod": "11", "ad": "ADY - BATI"},
        {"kod": "20", "ad": "MNS"},
        {"kod": "30", "ad": "MAR"},
        {"kod": "21", "ad": "MNS - FCV MAK."},
        {"kod": "24", "ad": "MNS - N.RUSTICA"},
        {"kod": "35", "ad": "MAR - IZ"},
        {"kod": "25", "ad": "MNS - IZ"},
        {"kod": "12", "ad": "ADY DOĞU-JTI SCV"},
        {"kod": "13", "ad": "ADY BATI-JTI SCV"},
        {"kod": "22", "ad": "MNS-JTI SCV"},
        {"kod": "32", "ad": "MAR-JTI SCV"},
        {"kod": "14", "ad": "ADY DOĞU-SCV TOPPING"},
        {"kod": "15", "ad": "ADY BATI-SCV TOPPING"},
        {"kod": "26", "ad": "MNS-SCV TOPPING"},
        {"kod": "36", "ad": "MAR-SCV TOPPING"},
        {"kod": "16", "ad": "ADY DOĞU-PMI SCV"},
        {"kod": "17", "ad": "ADY BATI-PMI SCV"},
        {"kod": "23", "ad": "MNS-PMI SCV"},
        {"kod": "33", "ad": "MAR-PMI SCV"},
        {"kod": "18", "ad": "ADY BATI - N.RUSTICA"},
        {"kod": "37", "ad": "MAR-BASMA"},
        {"kod": "34", "ad": "MAR-N.RUSTICA"},
        {"kod": "38", "ad": "MAR-PRILEP"},
        {"kod": "39", "ad": "MAR-KATERINI"}
    ]
    
    print("Bölge kodları ekleniyor...")
    print(f"Toplam {len(bolge_listesi)} bölge kodu eklenecek.")
    
    try:
        # API'ye toplu ekleme isteği gönder
        response = api_client.bulk_add_bolge(bolge_listesi)
        
        if response and response.get('success'):
            print("✅ Başarılı!")
            print(f"📊 {response.get('added_count', 0)} bölge eklendi")
            print(f"⏭️  {response.get('skipped_count', 0)} bölge atlandı (zaten mevcut)")
            
            if response.get('errors'):
                print("⚠️  Hatalar:")
                for error in response['errors']:
                    print(f"   - {error}")
        else:
            print("❌ Hata oluştu!")
            if response:
                print(f"Hata mesajı: {response.get('error', 'Bilinmeyen hata')}")
            else:
                print("API'den yanıt alınamadı")
                
    except Exception as e:
        print(f"❌ Script hatası: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("BÖLGE KODLARI EKLEME SCRIPTİ")
    print("=" * 50)
    
    success = main()
    
    if success:
        print("\n✅ Script başarıyla tamamlandı!")
    else:
        print("\n❌ Script hata ile sonlandı!")
        sys.exit(1)
