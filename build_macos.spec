# -*- mode: python ; coding: utf-8 -*-
"""
Спецификация для PyInstaller для macOS
Создает .app bundle для macOS
"""
import os
import sys

block_cipher = None

# Разделитель для данных на macOS
data_separator = ':'

# Собираем данные
datas = []
if os.path.exists('data'):
    datas.append(('data', 'data'))
if os.path.exists('resources'):
    datas.append(('resources', 'resources'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'sqlite3',
        'PIL',
        'PIL.Image',
        'requests',
        'json',
        'base64',
        'io',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NanoBananaPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Без консоли для GUI приложения
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/app.icns' if os.path.exists('resources/icons/app.icns') else None,
)

# Для macOS создаем .app bundle
app = BUNDLE(
    exe,
    name='NanoBananaPro.app',
    icon='resources/icons/app.icns' if os.path.exists('resources/icons/app.icns') else None,
    bundle_identifier='com.nanobanana.pro',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2024 NanoBanana Pro',
        'LSMinimumSystemVersion': '10.13',
    },
)


