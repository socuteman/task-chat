#!/usr/bin/env python3
"""
Task-Chat — Точка входа для запуска сервера
Запуск: python run.py
"""

import os
import sys

# Отладочный вывод
print("=" * 50)
print("Task-Chat Server Starting...")
print(f"Python: {sys.executable}")
print(f"sys.path: {sys.path[:3]}")
print(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
print(f"CWD: {os.getcwd()}")
print("=" * 50)

# Определяем директорию
if getattr(sys, 'frozen', False):
    # Запуск из EXE (--onefile)
    BASE_DIR = os.path.dirname(sys.executable)
    # В режиме onefile файлы в sys._MEIPASS
    RESOURCE_DIR = sys._MEIPASS
    print(f"Running from EXE (onefile)")
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"RESOURCE_DIR: {RESOURCE_DIR}")
else:
    # Запуск из исходников
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = BASE_DIR
    print(f"Running from source")
    print(f"BASE_DIR: {BASE_DIR}")

# Добавляем путь для импортов
sys.path.insert(0, RESOURCE_DIR)

# Переменные окружения
data_dir = os.environ.get('TASKCHAT_DATA_DIR', os.path.join(BASE_DIR, 'data'))
os.environ['TASKCHAT_DATA_DIR'] = data_dir
os.environ['FLASK_TEMPLATES_FOLDER'] = os.environ.get('FLASK_TEMPLATES_FOLDER', os.path.join(RESOURCE_DIR, 'templates'))
os.environ['FLASK_STATIC_FOLDER'] = os.environ.get('FLASK_STATIC_FOLDER', os.path.join(RESOURCE_DIR, 'static'))

print(f"DATA_DIR: {data_dir}")
print(f"TEMPLATES: {os.environ['FLASK_TEMPLATES_FOLDER']}")
print(f"STATIC: {os.environ['FLASK_STATIC_FOLDER']}")
print("=" * 50)

# Импортируем приложение
try:
    from app.app import create_app
    print("Imported create_app from app.app")
except ImportError as e:
    print(f"Import error: {e}")
    try:
        from app import create_app
        print("Imported create_app from app (fallback)")
    except ImportError as e2:
        print(f"Fallback import error: {e2}")
        raise

# Создаём приложение
config_name = os.environ.get('FLASK_CONFIG', 'production')
app = create_app(config_name)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"Starting server on {host}:{port}")
    print("=" * 50)
    
    # Пробуем waitress для Windows, иначе встроенный сервер
    try:
        from waitress import serve
        print("Using Waitress WSGI server...")
        serve(app, host=host, port=port, threads=4)
    except ImportError:
        print("Using Flask built-in server...")
        app.run(host=host, port=port, debug=False)
