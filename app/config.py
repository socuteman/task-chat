import os
import sys
from datetime import timedelta
from pathlib import Path

# Получаем базовый путь (для EXE и обычного запуска)
if getattr(sys, 'frozen', False):
    # Запуск из скомпилированного EXE
    basedir = Path(sys.executable).parent
    # Для данных используем директорию data рядом с EXE
    data_dir = basedir / 'data'
else:
    # Обычный запуск Python
    basedir = Path(__file__).parent.resolve()
    # Для данных используем директорию data рядом с проектом
    data_dir = basedir.parent / 'data'

# Создаём директорию данных если не существует
data_dir.mkdir(exist_ok=True)


class Config:
    """Базовая конфигурация"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'task-chat-secret-key-change-in-production-2026'

    # База данных - в директории data/instance
    instance_dir = data_dir / 'instance'
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{instance_dir / "taskchat.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Сессии
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # Загрузка файлов - в директории data/uploads
    UPLOAD_FOLDER = data_dir / 'uploads'
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB max file size

    # Разрешенные расширения для файлов
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    ALLOWED_PDF_EXTENSIONS = {'pdf'}
    ALLOWED_DICOM_EXTENSIONS = {'dcm', 'dicom'}
    ALLOWED_ARCHIVE_EXTENSIONS = {'zip', 'rar', '7z'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'doc', 'docx', 'xls', 'xlsx', 'txt'}

    ALLOWED_EXTENSIONS = (
        ALLOWED_IMAGE_EXTENSIONS |
        ALLOWED_PDF_EXTENSIONS |
        ALLOWED_DICOM_EXTENSIONS |
        ALLOWED_ARCHIVE_EXTENSIONS |
        ALLOWED_DOCUMENT_EXTENSIONS
    )

    # Размеры для миниатюр изображений
    IMAGE_THUMBNAIL_SIZE = (800, 600)

    # Pagination
    TASKS_PER_PAGE = 20
    MESSAGES_PER_PAGE = 50

    # Typing status timeout (секунды)
    TYPING_STATUS_TIMEOUT = 5

    # Логирование - в директории data/logs
    LOG_DIR = data_dir / 'logs'
    LOG_FORMAT = 'json'  # json или text
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = 10

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    ENV = 'development'


class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    ENV = 'production'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Логирование в файл
        import logging
        from logging.handlers import RotatingFileHandler
        import os
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/taskchat.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Task Chat startup')


class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
