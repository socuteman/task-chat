# build_exe.py
# Copyright (c) 2026 iak
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
    '--name=TaskChat',
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
print("Файл: dist/TaskChat.exe")