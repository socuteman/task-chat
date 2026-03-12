#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task-Chat Full v0.3.2 - Advanced Logging Module
Модуль расширенного логирования с поддержкой различных форматов и категорий

Разработчик: iak
Версия: 0.3.2
"""

import os
import sys
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any


class ColoredFormatter(logging.Formatter):
    """Цветной форматтер для консольного вывода"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f'{log_color}{record.levelname}{self.RESET}'
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON форматтер для структурированного логирования"""
    
    def __init__(self, category: str = 'system'):
        super().__init__()
        self.category = category
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'category': getattr(record, 'category', self.category),
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Добавляем дополнительные поля
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'username'):
            log_entry['username'] = record.username
        if hasattr(record, 'task_id'):
            log_entry['task_id'] = record.task_id
        if hasattr(record, 'chat_id'):
            log_entry['chat_id'] = record.chat_id
        if hasattr(record, 'extra_data'):
            log_entry['extra_data'] = record.extra_data
        
        # Добавляем информацию об исключении
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class CategoryFilter(logging.Filter):
    """Фильтр для добавления категории к логам"""
    
    def __init__(self, category: str):
        super().__init__()
        self.category = category
    
    def filter(self, record):
        record.category = self.category
        return True


class TaskChatLogger:
    """
    Основной класс логирования Task-Chat
    
    Поддерживает:
    - JSON и текстовый формат
    - Ротацию по размеру и времени
    - Категории логов (auth, tasks, chat, files, admin, system)
    - Консольный и файловый вывод
    - Различные уровни логирования
    """
    
    CATEGORIES = ['auth', 'tasks', 'chat', 'files', 'admin', 'system', 'api', 'database']
    LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    _instances: Dict[str, logging.Logger] = {}
    
    def __init__(
        self,
        name: str = 'taskchat',
        log_dir: Optional[str] = None,
        log_format: str = 'json',
        log_level: str = 'INFO',
        console_output: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 10
    ):
        self.name = name
        self.log_dir = Path(log_dir) if log_dir else Path(__file__).parent / 'logs'
        self.log_dir.mkdir(exist_ok=True)
        self.log_format = log_format
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.console_output = console_output
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        self._setup_logger()
    
    def _setup_logger(self):
        """Настройка логгера"""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.log_level)
        
        # Очищаем существующие обработчики
        self.logger.handlers.clear()
        
        # Создаем форматтеры
        if self.log_format == 'json':
            file_formatter = JSONFormatter()
            console_formatter = ColoredFormatter(
                '%(asctime)s | %(levelname)-8s | %(category)-10s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(category)-10s | %(name)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_formatter = ColoredFormatter(
                '%(asctime)s | %(levelname)-8s | %(category)-10s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Файловый обработчик с ротацией по размеру
        log_file = self.log_dir / f'{self.name}.log'
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Файловый обработчик с ротацией по времени (для истории)
        time_log_file = self.log_dir / f'{self.name}_history.log'
        time_handler = TimedRotatingFileHandler(
            time_log_file,
            when='D',
            interval=1,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        time_handler.setFormatter(file_formatter)
        self.logger.addHandler(time_handler)
        
        # Консольный обработчик
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def get_category_logger(self, category: str) -> logging.Logger:
        """
        Получение логгера для конкретной категории
        
        Args:
            category: Категория лога (auth, tasks, chat, files, admin, system, api, database)
        
        Returns:
            Logger с установленной категорией
        """
        if category not in self.CATEGORIES:
            category = 'system'
        
        category_logger = logging.getLogger(f'{self.name}.{category}')
        category_logger.handlers = self.logger.handlers.copy()
        category_logger.addFilter(CategoryFilter(category))
        category_logger.setLevel(self.log_level)
        
        return category_logger
    
    def debug(self, message: str, **kwargs):
        """Логирование уровня DEBUG"""
        self._log('debug', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Логирование уровня INFO"""
        self._log('info', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Логирование уровня WARNING"""
        self._log('warning', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Логирование уровня ERROR"""
        self._log('error', message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Логирование уровня CRITICAL"""
        self._log('critical', message, **kwargs)
    
    def _log(self, level: str, message: str, **kwargs):
        """Внутренний метод логирования"""
        log_method = getattr(self.logger, level)
        
        # Создаем запись лога с дополнительными полями
        extra = {}
        for key, value in kwargs.items():
            if key in ['user_id', 'username', 'task_id', 'chat_id', 'extra_data']:
                extra[key] = value
        
        log_method(message, extra=extra)
    
    def log_auth(self, level: str, message: str, user_id: Optional[int] = None, **kwargs):
        """Логирование событий аутентификации"""
        logger = self.get_category_logger('auth')
        getattr(logger, level)(message, extra={'user_id': user_id, **kwargs})
    
    def log_task(self, level: str, message: str, task_id: Optional[int] = None, **kwargs):
        """Логирование событий задач"""
        logger = self.get_category_logger('tasks')
        getattr(logger, level)(message, extra={'task_id': task_id, **kwargs})
    
    def log_chat(self, level: str, message: str, chat_id: Optional[int] = None, **kwargs):
        """Логирование событий чата"""
        logger = self.get_category_logger('chat')
        getattr(logger, level)(message, extra={'chat_id': chat_id, **kwargs})
    
    def log_file(self, level: str, message: str, **kwargs):
        """Логирование событий файлов"""
        logger = self.get_category_logger('files')
        getattr(logger, level)(message, **kwargs)
    
    def log_admin(self, level: str, message: str, user_id: Optional[int] = None, **kwargs):
        """Логирование действий администратора"""
        logger = self.get_category_logger('admin')
        getattr(logger, level)(message, extra={'user_id': user_id, **kwargs})
    
    def log_api(self, level: str, message: str, **kwargs):
        """Логирование API запросов"""
        logger = self.get_category_logger('api')
        getattr(logger, level)(message, **kwargs)
    
    def log_database(self, level: str, message: str, **kwargs):
        """Логирование событий базы данных"""
        logger = self.get_category_logger('database')
        getattr(logger, level)(message, **kwargs)


# Глобальный экземпляр логгера
_logger: Optional[TaskChatLogger] = None


def get_logger(
    log_dir: Optional[str] = None,
    log_format: str = 'json',
    log_level: str = 'INFO'
) -> TaskChatLogger:
    """
    Получение глобального экземпляра логгера
    
    Args:
        log_dir: Директория для логов
        log_format: Формат логов (json или text)
        log_level: Уровень логирования
    
    Returns:
        Экземпляр TaskChatLogger
    """
    global _logger
    if _logger is None:
        _logger = TaskChatLogger(
            log_dir=log_dir,
            log_format=log_format,
            log_level=log_level
        )
    return _logger


def init_app_logging(app, log_dir: Optional[str] = None, log_format: str = 'json'):
    """
    Инициализация логирования для Flask приложения
    
    Args:
        app: Flask приложение
        log_dir: Директория для логов
        log_format: Формат логов
    """
    logger = get_logger(log_dir=log_dir, log_format=log_format)
    
    # Устанавливаем логгер для Flask приложения
    app.logger.handlers = logger.logger.handlers
    app.logger.setLevel(logger.logger.level)
    
    # Логирование запуска приложения
    logger.info('Task-Chat application starting', extra={
        'extra_data': {
            'version': '0.3.2',
            'environment': app.config.get('ENV', 'development')
        }
    })
    
    return logger


# Декораторы для логирования
def log_api_request(category: str = 'api'):
    """Декоратор для логирования API запросов"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger()
            logger.log_api('info', f'API Request: {func.__name__}', extra_data={
                'function': func.__name__,
                'args': str(args)[:100],
                'kwargs': {k: v for k, v in kwargs.items() if k != 'password'}
            })
            
            try:
                result = func(*args, **kwargs)
                logger.log_api('info', f'API Response: {func.__name__} - Success')
                return result
            except Exception as e:
                logger.log_api('error', f'API Error: {func.__name__} - {str(e)}')
                raise
        return wrapper
    return decorator


def log_user_action(action: str):
    """Декоратор для логирования действий пользователя"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask_login import current_user
            logger = get_logger()
            
            user_id = current_user.id if current_user.is_authenticated else None
            username = current_user.username if current_user.is_authenticated else 'anonymous'
            
            logger.info(f'User action: {action}', user_id=user_id, username=username)
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f'User action failed: {action} - {str(e)}', user_id=user_id)
                raise
        return wrapper
    return decorator
