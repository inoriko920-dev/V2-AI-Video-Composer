# -*- mode: python ; coding: utf-8 -*-

datas = [
    ('resources', 'resources'),
    ('schemas', 'schemas'),
    ('LICENSES', 'LICENSES'),
    ('RELEASE_NOTES_0.2.0.md', '.'),
    ('docs/USER_GUIDE.md', '.'),
    ('MAINTENANCE.md', '.'),
    ('BACKUP_AND_RECOVERY.md', '.'),
]

a = Analysis(
    ['src/aavc/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI Automatic Video Composer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI Automatic Video Composer',
)
