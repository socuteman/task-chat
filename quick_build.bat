@echo off
chcp 65001 > nul
title Быстрая сборка TaskChat

echo ========================================
echo     БЫСТРАЯ СБОРКА В EXE
echo ========================================
echo.

echo 1. Установка зависимостей...
pip install flask flask-login flask-sqlalchemy flask-wtf werkzeug jinja2 wtforms email-validator

echo.
echo 2. Очистка старых файлов...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
del *.spec 2>nul

echo.
echo 3. Создание spec файла...
python -c "
import PyInstaller.__main__

PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--console',
    '--name=MedicalChat',
    '--add-data=templates;templates',
    '--add-data=static;static',
    '--hidden-import=flask',
    '--hidden-import=flask_login',
    '--hidden-import=flask_login.login_manager',
    '--hidden-import=flask_login.utils',
    '--hidden-import=flask_login.mixins',
    '--hidden-import=flask_sqlalchemy',
    '--hidden-import=flask_wtf',
    '--hidden-import=flask_wtf.csrf',
    '--hidden-import=jinja2',
    '--hidden-import=jinja2.ext',
    '--hidden-import=werkzeug',
    '--hidden-import=werkzeug.middleware',
    '--hidden-import=wtforms',
    '--hidden-import=wtforms.fields',
    '--hidden-import=wtforms.validators',
    '--hidden-import=email_validator',
    '--hidden-import=sqlalchemy',
    '--hidden-import=sqlalchemy.orm',
    '--hidden-import=sqlalchemy.ext',
])
"

echo.
echo 4. Редактирование spec файла...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo 
echo a = Analysis(
echo     ['main.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[
echo         ('templates', 'templates'),
echo         ('static', 'static')
echo     ],
echo     hiddenimports=[
echo         'flask',
echo         'flask_login',
echo         'flask_login.login_manager',
echo         'flask_login.utils',
echo         'flask_login.mixins',
echo         'flask_sqlalchemy',
echo         'flask_wtf',
echo         'flask_wtf.csrf',
echo         'jinja2',
echo         'jinja2.ext',
echo         'werkzeug',
echo         'werkzeug.middleware',
echo         'wtforms',
echo         'wtforms.fields',
echo         'wtforms.validators',
echo         'email_validator',
echo         'sqlalchemy',
echo         'sqlalchemy.orm',
echo         'sqlalchemy.ext',
echo     ],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[],
echo     noarchive=False,
echo )
echo 
echo pyz = PYZ(a.pure)
echo 
echo exe = EXE(
echo     pyz,
echo     a.scripts,
echo     a.binaries,
echo     a.datas,
echo     [],
echo     name='MedicalChat',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     upx_exclude=[],
echo     runtime_tmpdir=None,
echo     console=True,
echo     disable_windowed_traceback=False,
echo     argv_emulation=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo )
) > TaskChat.spec

echo.
echo 5. Сборка EXE...
pyinstaller TaskChat.spec

echo.
if exist "dist\TaskChat.exe" (
    echo ✓ УСПЕХ! EXE создан: dist\TaskChat.exe
    echo.
    echo Нажмите Enter для запуска...
    pause
    cd dist
    TaskChat.exe
    cd..
) else (
    echo ✗ ОШИБКА сборки!
    pause
)