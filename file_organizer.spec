# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['1.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 添加PyQt6相关的隐藏导入
pyqt6_modules = [
    'PyQt6.QtCore',
    'PyQt6.QtGui', 
    'PyQt6.QtWidgets',
    'PyQt6.QtPrintSupport',
]

for module in pyqt6_modules:
    a.add_hidden_imports([module])

# 添加其他可能需要的模块
a.add_hidden_imports(['uuid', 'shutil', 'logging', 'threading', 'datetime', 'time'])

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='文件整理工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为False以隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon_256.png',  # 使用PNG图标文件（PyInstaller会自动转换为ICO）
)