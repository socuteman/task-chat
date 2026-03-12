#!/usr/bin/env python3
"""
Task-Chat Server Runner
Запускает ТОЛЬКО сервер, без GUI
"""

import os
import sys

# Определяем директорию
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = BASE_DIR

# Добавляем путь
sys.path.insert(0, RESOURCE_DIR)

# Переменные окружения
os.environ['TASKCHAT_DATA_DIR'] = os.environ.get('TASKCHAT_DATA_DIR', os.path.join(BASE_DIR, 'data'))
os.environ['FLASK_TEMPLATES_FOLDER'] = os.environ.get('FLASK_TEMPLATES_FOLDER', os.path.join(RESOURCE_DIR, 'templates'))
os.environ['FLASK_STATIC_FOLDER'] = os.environ.get('FLASK_STATIC_FOLDER', os.path.join(RESOURCE_DIR, 'static'))

# Импортируем и запускаем ТОЛЬКО сервер
from app.app import create_app

app = create_app('production')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    try:
        from waitress import serve
        serve(app, host=host, port=port, threads=4)
    except ImportError:
        app.run(host=host, port=port, debug=False)
