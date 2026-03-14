# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('logo.jpeg', '.'), ('logo.png', '.'), ('1.gif', '.'), ('2.gif', '.'), ('3.gif', '.'), ('4.gif', '.'), ('5.gif', '.'), ('6.gif', '.'), ('icons', 'icons'), ('api', 'api'), ('api/style.qss', 'api')]
binaries = []
hiddenimports = ['flask', 'flask_cors', 'werkzeug', 'werkzeug.security', 'werkzeug.serving', 'werkzeug.middleware.proxy_fix', 'requests', 'sqlite3', 'pandas', 'numpy', 'openpyxl', 'openpyxl.styles', 'openpyxl.utils', 'openpyxl.utils.dataframe', 'openpyxl.utils.get_column_letter', 'xlsxwriter', 'xlrd', 'pandas.io.formats.excel', 'pandas.io.excel._openpyxl', 'pandas.io.excel._xlrd', 'pandas.io.excel._xlsxwriter', 'matplotlib', 'matplotlib.pyplot', 'matplotlib.backends', 'matplotlib.backends.backend_qt5agg', 'matplotlib.figure', 'matplotlib.backends.backend_qt5agg.FigureCanvasQTAgg', 'RestApi', 'harcamaOperations', 'masrafOperations', 'kodOperations', 'OdemeOperations', 'bolgeGoruntuleOperations', 'ustDuzeyYoneticiOperations', 'kullaniciYonetimiOperations', 'harcama_masraf_app', 'LoginRegister', 'splash_screen', 'api_client', 'api.v1', 'PyQt5', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.Qt', 'datetime', 'logging', 'traceback', 'os', 'sys', 'threading', 'time', 'json', 're', 'difflib', 'collections', 'collections.abc']
datas += collect_data_files('all')
binaries += collect_dynamic_libs('all')
hiddenimports += collect_submodules('all')
tmp_ret = collect_all('flask')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('werkzeug')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pandas')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('openpyxl')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('PyQt5')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('matplotlib')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('numpy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HarcamaMasrafTakip',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icons\\a.png'],
)
