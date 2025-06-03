# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['desktop_agent.py'],
    pathex=[],
    binaries=[],
    datas=[('requirements_agent.txt', '.')],
    hiddenimports=[
        'requests',
        'PIL',
        'PIL.Image',
        'mss',
        'schedule',
        'psutil',
        'json',
        'datetime',
        'threading',
        'logging',
        'platform',
        'hashlib',
        'uuid',
        'io',
        'time',
        'os',
        'sys'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Try to add optional imports safely
try:
    import pynput
    a.hiddenimports.extend(['pynput', 'pynput.keyboard', 'pynput.mouse'])
except ImportError:
    pass

# Platform-specific imports
import platform
if platform.system() == "Windows":
    try:
        import win32api
        a.hiddenimports.extend(['win32api', 'win32gui', 'win32process'])
    except ImportError:
        pass
elif platform.system() == "Linux":
    try:
        import Xlib
        a.hiddenimports.extend(['Xlib', 'Xlib.display'])
    except ImportError:
        pass

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DesktopMonitoringAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
