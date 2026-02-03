# build_exe.py
import PyInstaller.__main__
import os
import shutil

# Очистка
print("Очистка старых файлов...")
for folder in ['build', 'dist']:
    if os.path.exists(folder):
        shutil.rmtree(folder)

for file in os.listdir('.'):
    if file.endswith('.spec'):
        os.remove(file)

# Сборка
print("Сборка EXE...")
PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--console',
    '--name=MedicalChat',
    '--add-data=templates;templates',
    '--add-data=static;static',
    '--hidden-import=flask',
    '--hidden-import=flask_login',
    '--hidden-import=flask_sqlalchemy',
    '--hidden-import=flask_wtf',
    '--hidden-import=jinja2',
    '--hidden-import=werkzeug',
    '--hidden-import=wtforms',
    '--hidden-import=email_validator',
    '--hidden-import=sqlalchemy',
    '--collect-all=flask_login',  # Важно!
    '--collect-all=flask_wtf',
    '--collect-all=flask_sqlalchemy',
])

print("✓ Сборка завершена!")
print("Файл: dist/MedicalChat.exe")