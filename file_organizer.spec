# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 添加必要的隐藏导入
hidden_imports = [
    'PyQt6.QtWidgets',
    'PyQt6.QtGui', 
    'PyQt6.QtCore',
    'winreg',
    'logging',
    'shutil',
    'uuid',
    'platform',
    'subprocess',
    'datetime',
    'time',
    'threading',
    'os',
    'sys'
]

a = Analysis(
    ['file_copy.py'],
    pathex=[],
    binaries=[],
    # 包含数据文件
    datas=[
        ('scheduled_tasks.json', '.'),
        ('settings.json', '.')
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=0,
)

# 添加PyQt6插件
pyqt6_plugins = [
    'PyQt6.Qt6Plugins',
    'PyQt6.Qt6Core',
    'PyQt6.Qt6Gui',
    'PyQt6.Qt6Widgets'
]

for plugin in pyqt6_plugins:
    a.binaries.append((plugin, plugin, 'BINARY'))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
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
    icon=None,
)