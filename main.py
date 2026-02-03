#!/usr/bin/env python3
# main.py - Точка входа для EXE сборки
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

import os
import sys
import traceback

# Добавляем путь к статическим файлам в EXE режиме
if getattr(sys, 'frozen', False):
    # Если запущено как EXE, добавляем путь к временной папке
    base_path = sys._MEIPASS
else:
    # Если запущено как скрипт
    base_path = os.path.dirname(os.path.abspath(__file__))

# Добавляем пути для статических файлов
static_path = os.path.join(base_path, 'static')
templates_path = os.path.join(base_path, 'templates')

try:
    from app import app
    
    if __name__ == '__main__':
        print("=" * 50)
        print("Запуск Task Chat")
        print("=" * 50)
        print(f"Статические файлы: {static_path}")
        print(f"Шаблоны: {templates_path}")
        print(f"База данных: {os.path.join(os.path.dirname(__file__), 'task_chat.db')}")
        print("=" * 50)
        print("Приложение доступно по адресам:")
        print("• http://localhost:5000")
        print("• http://127.0.0.1:5000")
        print("• http://[ваш-ip-адрес]:5000 (в локальной сети)")
        print("=" * 50)
        print("Для остановки нажмите Ctrl+C")
        print("=" * 50)
        
        # Запуск приложения
        app.run(
            host='0.0.0.0', 
            port=5000, 
            debug=False,
            threaded=True
        )
        
except Exception as e:
    print(f"Ошибка при запуске приложения: {e}")
    print("Трассировка ошибки:")
    traceback.print_exc()
    input("Нажмите Enter для выхода...")