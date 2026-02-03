#!/usr/bin/env python3
# main.py - Точка входа для EXE сборки

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
        print("Запуск Медицинского Чата")
        print("=" * 50)
        print(f"Статические файлы: {static_path}")
        print(f"Шаблоны: {templates_path}")
        print(f"База данных: {os.path.join(os.path.dirname(__file__), 'medical_chat.db')}")
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