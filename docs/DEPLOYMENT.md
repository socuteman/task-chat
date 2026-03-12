# Руководство по развёртыванию Task-Chat v0.4.9

**Разработчик:** iak  
**Контакт:** bawel@ya.ru

---

## Содержание

1. [Требования к системе](#требования-к-системе)
2. [Запуск EXE-версии (Windows)](#запуск-exe-версии-windows)
3. [Запуск из исходного кода](#запуск-из-исходного-кода)
4. [Сборка EXE](#сборка-exe)
5. [Конфигурация](#конфигурация)
6. [Данные и логи](#данные-и-логи)
7. [Диагностика](#диагностика)

---

## Требования к системе

### Минимальные требования

| Компонент | Требование |
|-----------|------------|
| **ОС** | Windows 10 / Linux Ubuntu 18.04+ |
| **Процессор** | 2 ядра, 2.0 GHz |
| **ОЗУ** | 2 GB |
| **Диск** | 1 GB свободного места |

### Рекомендуемые требования

| Компонент | Требование |
|-----------|------------|
| **ОС** | Windows 10/11 |
| **Процессор** | 4 ядра, 2.5 GHz |
| **ОЗУ** | 4 GB |
| **Диск** | 10 GB SSD |

### Программные требования

Для EXE-версии:
- Python не требуется

Для запуска из исходного кода:
- Python 3.8 или выше
- pip (менеджер пакетов Python)

---

## Запуск EXE-версии (Windows)

### Шаг 1: Подготовка

EXE-файл находится в директории:
```
E:\Projects\Task-chat-0-4-9\task-chat\dist\TaskChat-Server\TaskChat-Server.exe
```

### Шаг 2: Запуск

**Вариант A: Прямой запуск**

1. Откройте проводник
2. Перейдите в директорию `dist\TaskChat-Server`
3. Дважды кликните на `TaskChat-Server.exe`

**Вариант B: Запуск из командной строки**

```cmd
cd E:\Projects\Task-chat-0-4-9\task-chat\dist\TaskChat-Server
TaskChat-Server.exe
```

### Шаг 3: Проверка работы

1. Откройте браузер
2. Введите: `http://localhost:5000`
3. Должна открыться страница входа

### Шаг 4: Вход в систему

- **Логин:** `admin`
- **Пароль:** `admin123`

### Структура после запуска

После первого запуска рядом с EXE создаётся директория `data`:

```
TaskChat-Server/
├── TaskChat-Server.exe
├── _internal/
├── data/ (создаётся при запуске)
│   ├── instance/
│   │   └── taskchat.db (база данных)
│   ├── uploads/ (загруженные файлы)
│   └── logs/ (логи приложения)
│       ├── taskchat.log
│       └── taskchat_history.log
└── templates/
└── static/
```

---

## Запуск из исходного кода

### Шаг 1: Установка Python

1. Скачайте Python 3.8+ с https://www.python.org/
2. Установите, отметив галочку «Add Python to PATH»

### Шаг 2: Проверка установки

```cmd
python --version
pip --version
```

### Шаг 3: Перейдите в директорию проекта

```cmd
cd E:\Projects\Task-chat-0-4-9\task-chat\app
```

### Шаг 4: Установка зависимостей

```cmd
pip install -r ..\requirements.txt
```

### Шаг 5: Запуск сервера

```cmd
python run.py
```

### Шаг 6: Проверка работы

1. Откройте браузер
2. Введите: `http://localhost:5000`

---

## Сборка EXE

### Требования

- Python 3.8+
- PyInstaller 6.x

### Шаг 1: Установка PyInstaller

```cmd
pip install pyinstaller
```

### Шаг 2: Перейдите в директорию проекта

```cmd
cd E:\Projects\Task-chat-0-4-9\task-chat
```

### Шаг 3: Сборка

```cmd
pyinstaller --clean taskchat.spec
```

### Шаг 4: Результат

Готовый EXE находится в:
```
dist\TaskChat-Server\TaskChat-Server.exe
```

### Spec-файл

`taskchat.spec` содержит конфигурацию сборки:

```python
a = Analysis(
    ['app/run.py'],
    datas=[
        ('app/templates', 'templates'),
        ('app/static', 'static'),
    ],
    hiddenimports=[
        'flask', 'flask_login', 'flask_sqlalchemy', 'flask_wtf',
        'werkzeug', 'wtforms', 'waitress', 'psutil', 'yaml',
        'requests', 'jinja2', 'markupsafe', 'sqlalchemy'
    ],
)
```

---

## Конфигурация

### Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `SECRET_KEY` | Встроенный | Ключ сессии |
| `DATABASE_URL` | `sqlite:///data/instance/taskchat.db` | Строка подключения к БД |
| `FLASK_CONFIG` | `development` | `development` или `production` |
| `PORT` | `5000` | Порт сервера |
| `HOST` | `0.0.0.0` | Хост для bind |
| `TASKCHAT_DATA_DIR` | `./data` | Директория данных |
| `LOG_LEVEL` | `INFO` | Уровень логирования |
| `FLASK_TEMPLATES_FOLDER` | `templates` | Путь к шаблонам |
| `FLASK_STATIC_FOLDER` | `static` | Путь к статике |

### Установка переменных окружения (Windows)

**Временная установка (до перезапуска консоли):**

```cmd
set PORT=8080
set HOST=127.0.0.1
set LOG_LEVEL=DEBUG
```

**Постоянная установка:**

1. Откройте «Система» → «Дополнительные параметры системы»
2. Нажмите «Переменные среды»
3. Добавьте новые переменные

### Пример конфигурации для production

```cmd
set SECRET_KEY=your-secret-key-here
set FLASK_CONFIG=production
set PORT=5000
set HOST=0.0.0.0
set LOG_LEVEL=WARNING
```

---

## Данные и логи

### Расположение данных

**При запуске из EXE:**
```
<директория_с_EXE>/data/
```

**При запуске из исходного кода:**
```
<директория_проекта>/../data/
```

### Структура директории data

```
data/
├── instance/
│   └── taskchat.db (SQLite база данных)
├── uploads/
│   ├── <task_id>/ (файлы задач)
│   └── personal_chats/ (файлы личных чатов)
└── logs/
    ├── taskchat.log (текущий лог)
    └── taskchat_history.log (архивные логи)
```

### Резервное копирование

**Скрипт для Windows (backup.bat):**

```batch
@echo off
set BACKUP_DIR=E:\Backups\TaskChat
set DATA_DIR=E:\Projects\Task-chat-0-4-9\task-chat\data
set DATE=%DATE:~-4,4%%DATE:~-7,2%%DATE:~-10,2%

echo Creating backup: %DATE%
mkdir %BACKUP_DIR%

:: Резервное копирование БД
xcopy %DATA_DIR%\instance %BACKUP_DIR%\instance_%DATE% /E /I /Y

:: Резервное копирование файлов
xcopy %DATA_DIR%\uploads %BACKUP_DIR%\uploads_%DATE% /E /I /Y

echo Backup completed: %DATE%
```

**Расписание резервного копирования:**

- База данных: ежедневно
- Файлы: ежедневно
- Логи: еженедельно (опционально)

### Восстановление из резервной копии

1. Остановите сервер
2. Скопируйте файлы из резервной копии:
   ```cmd
   xcopy E:\Backups\TaskChat\instance_*\* data\instance\ /E /I /Y
   xcopy E:\Backups\TaskChat\uploads_*\* data\uploads\ /E /I /Y
   ```
3. Запустите сервер

---

## Диагностика

### Проверка состояния сервера

**API статистики:**
```bash
curl http://localhost:5000/api/stats
```

**Ответ:**
```json
{
  "users": { "total": 10, "online": 3 },
  "tasks": { "total": 50, "pending": 15, ... },
  "messages": { "total": 500, "today": 25 },
  "files": { "total": 100, "size_bytes": 1048576 },
  "uptime": 3600
}
```

### Просмотр логов

**Windows (PowerShell):**
```powershell
# Просмотр текущего лога
Get-Content data\logs\taskchat.log -Tail 50 -Wait

# Поиск по логам
Select-String -Path data\logs\taskchat.log -Pattern "ERROR"
```

**Windows (cmd):**
```cmd
type data\logs\taskchat.log
```

### Частые ошибки

#### Port 5000 already in use

**Проблема:** Порт 5000 занят другим приложением.

**Решение:**
```cmd
# Найти процесс
netstat -ano | findstr :5000

# Завершить процесс
taskkill /PID <PID> /F

# Или изменить порт
set PORT=5001
python app/run.py
```

#### Database is locked

**Проблема:** База данных заблокирована.

**Решение:**
1. Остановите сервер
2. Удалите lock-файл (если существует):
   ```
   data\instance\taskchat.db.lock
   ```
3. Запустите сервер

#### Module not found

**Проблема:** Не установлены зависимости.

**Решение:**
```cmd
pip install -r requirements.txt
```

#### No module named 'app'

**Проблема:** Неправильный путь запуска.

**Решение:**
```cmd
cd E:\Projects\Task-chat-0-4-9\task-chat\app
python run.py
```

### Проверка целостности базы данных

```bash
sqlite3 data/instance/taskchat.db "PRAGMA integrity_check;"
```

### Оптимизация базы данных

```bash
sqlite3 data/instance/taskchat.db "VACUUM;"
```

---

## Мониторинг

### Проверка онлайн-пользователей

Через API:
```bash
curl http://localhost:5000/api/online_users
```

### Проверка активных задач

Через API:
```bash
curl http://localhost:5000/api/tasks
```

### Проверка логов в реальном времени

```powershell
Get-Content data\logs\taskchat.log -Tail 100 -Wait
```

---

## Обновление

### Обновление EXE-версии

1. Скачайте новую версию
2. Остановите текущий сервер
3. Сделайте резервную копию `data/`
4. Замените файлы приложения
5. Запустите новую версию

### Обновление из исходного кода

```cmd
# Остановите сервер

# Обновите код
git pull origin main

# Обновите зависимости
pip install -r requirements.txt --upgrade

# Запустите сервер
python app/run.py
```

---

## Поддержка

**Разработчик:** iak  
**Email:** bawel@ya.ru

**Версия руководства:** 0.4.9  
**Дата обновления:** Март 2026
