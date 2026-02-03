# build_exe.py
# Copyright iak (c) 2026 Task Chat Project
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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