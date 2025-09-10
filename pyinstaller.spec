# Reproduzierbarer Build – ggf. Pfade anpassen
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

added_pkgs = collect_submodules('qrcode')  # Beispiel: qrcode-Plugins einbinden

a = Analysis(
    ['src/InventarQRTool.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=added_pkgs,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='InventarQRTool',
    icon='assets/app.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # True, wenn Konsole gewünscht
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
