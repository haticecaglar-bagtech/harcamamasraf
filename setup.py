# setup.py
import sys
import subprocess
import os

def pyinstall():
    # Windows için path separator
    sep = ";" if os.name == "nt" else ":"
    
    command = [
        "pyinstaller",
        "--onefile",  # Tek bir exe dosyası oluştur - TÜM DOSYALAR EXE İÇİNDE
        "--windowed",  # Konsol penceresi gösterme
        "--name", "HarcamaMasrafTakip",
        "main.py",
        # Tüm görsel dosyaları ekle - EXE İÇİNE
        "--add-data", f"logo.jpeg{sep}.",
        "--add-data", f"logo.png{sep}.",
        "--add-data", f"1.gif{sep}.",
        "--add-data", f"2.gif{sep}.",
        "--add-data", f"3.gif{sep}.",
        "--add-data", f"4.gif{sep}.",
        "--add-data", f"5.gif{sep}.",
        "--add-data", f"6.gif{sep}.",
        "--add-data", f"icons{sep}icons",
        # API klasöründeki TÜM dosyaları ekle - EXE İÇİNE
        "--add-data", f"api{sep}api",
        # API klasöründeki style.qss dosyasını da ekle
        "--add-data", f"api/style.qss{sep}api",
        # Flask ve API bağımlılıkları
        "--hidden-import=flask",
        "--hidden-import=flask_cors",
        "--hidden-import=werkzeug",
        "--hidden-import=werkzeug.security",
        "--hidden-import=werkzeug.serving",
        "--hidden-import=werkzeug.middleware.proxy_fix",
        "--hidden-import=requests",
        # SQLite (Python built-in, ama emin olmak için)
        "--hidden-import=sqlite3",
        # Excel işlemleri
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=openpyxl",
        "--hidden-import=openpyxl.styles",
        "--hidden-import=openpyxl.utils",
        "--hidden-import=openpyxl.utils.dataframe",
        "--hidden-import=openpyxl.utils.get_column_letter",
        "--hidden-import=xlsxwriter",
        "--hidden-import=xlrd",
        "--hidden-import=pandas.io.formats.excel",
        "--hidden-import=pandas.io.excel._openpyxl",
        "--hidden-import=pandas.io.excel._xlrd",
        "--hidden-import=pandas.io.excel._xlsxwriter",
        # Grafik ve görselleştirme
        "--hidden-import=matplotlib",
        "--hidden-import=matplotlib.pyplot",
        "--hidden-import=matplotlib.backends",
        "--hidden-import=matplotlib.backends.backend_qt5agg",
        "--hidden-import=matplotlib.figure",
        "--hidden-import=matplotlib.backends.backend_qt5agg.FigureCanvasQTAgg",
        # Python modülleri - tüm dosyalar otomatik bulunur ama emin olmak için
        "--hidden-import=RestApi",
        "--hidden-import=sqlalchemy",
        "--hidden-import=sqlalchemy.orm",
        "--hidden-import=sqlalchemy.dialects.sqlite",
        "--hidden-import=db",
        "--hidden-import=db.models",
        "--hidden-import=db.session",
        "--hidden-import=db.init_database",
        "--hidden-import=db.seed",
        "--hidden-import=db.seed_data",
        "--hidden-import=repositories",
        "--hidden-import=repositories.user_repository",
        "--hidden-import=repositories.catalog_repository",
        "--hidden-import=repositories.expense_repository",
        "--hidden-import=repositories.harcama_repository",
        "--hidden-import=config",
        "--hidden-import=backend_logging",
        "--hidden-import=api_error_handlers",
        "--hidden-import=jwt_auth",
        "--hidden-import=api_auth_context",
        "--hidden-import=jwt",
        "--hidden-import=harcamaOperations",
        "--hidden-import=masrafOperations",
        "--hidden-import=kodOperations",
        "--hidden-import=OdemeOperations",
        "--hidden-import=bolgeGoruntuleOperations",
        "--hidden-import=ustDuzeyYoneticiOperations",
        "--hidden-import=kullaniciYonetimiOperations",
        "--hidden-import=harcama_masraf_app",
        "--hidden-import=LoginRegister",
        "--hidden-import=splash_screen",
        "--hidden-import=api_client",
        # API klasöründeki modül
        "--hidden-import=api.v1",
        # PyQt5 modülleri
        "--hidden-import=PyQt5",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.Qt",
        # Diğer yardımcı modüller
        "--hidden-import=datetime",
        "--hidden-import=logging",
        "--hidden-import=traceback",
        "--hidden-import=os",
        "--hidden-import=sys",
        "--hidden-import=threading",
        "--hidden-import=time",
        "--hidden-import=json",
        "--hidden-import=re",
        "--hidden-import=difflib",
        "--hidden-import=collections",
        "--hidden-import=collections.abc",
        # Collect all submodules - TÜM ALT MODÜLLER EXE İÇİNE
        "--collect-all=flask",
        "--collect-all=werkzeug",
        "--collect-all=pandas",
        "--collect-all=openpyxl",
        "--collect-all=PyQt5",
        "--collect-all=matplotlib",
        "--collect-all=numpy",
        # Tüm binary dosyaları dahil et
        "--collect-binaries=all",
        # Tüm data dosyalarını dahil et
        "--collect-data=all",
        # Tüm submodules'ları dahil et
        "--collect-submodules=all",
        # UPX sıkıştırmayı devre dışı bırak (bazı sistemlerde sorun çıkarabilir)
        "--noupx",
        # Icon ekle (varsa)
    ]
    
    # Icon dosyası varsa ekle
    if os.path.exists("icons/a.png"):
        command.extend(["--icon", "icons/a.png"])

    subprocess.check_call(command)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pyinstall":
        pyinstall()
    else:
        print("Usage: python setup.py pyinstall")
