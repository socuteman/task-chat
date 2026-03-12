# Task-Chat Full

**Система управления задачами для медицинских учреждений с чатом**

## Обзор

Task-Chat Full — это Flask-приложение для управления задачами и организации коммуникации между врачами и физиками в медицинской среде.

### Роли пользователей

| Роль | Возможности |
|------|-------------|
| **Врач** | Создание задач, просмотр своих задач, чат с физиками |
| **Физик** | Просмотр задач, изменение статуса, чат с врачами |
| **Администратор** | Полный доступ ко всем задачам и пользователям |

### Основные возможности

- ✅ **Аутентификация** — вход с разделением по ролям
- ✅ **Управление задачами** — CRUD операции с приоритетами и сроками
- ✅ **Статусы задач**: `Ожидает`, `В работе`, `Выполнена`, `Отменена`
- ✅ **Чат по задачам** — обмен сообщениями в реальном времени
- ✅ **Статус "печатает"** — индикатор набора текста
- ✅ **Прикрепление файлов** — загрузка изображений, PDF, DICOM, архивов
- ✅ **Счетчик непрочитанных** — уведомления о новых сообщениях
- ✅ **Админ-панель** — управление пользователями и задачами

---

## Установка

### Требования

- Python 3.8+
- pip

### Шаги установки

1. **Перейдите в директорию проекта:**
   ```bash
   cd "/home/honorbook/Документы/Проекты/Task-chat works/Task-Chat-Full"
   ```

2. **Создайте виртуальное окружение (рекомендуется):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # или
   venv\Scripts\activate  # Windows
   ```

3. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Запустите приложение:**
   ```bash
   python run.py
   ```

5. **Откройте в браузере:**
   ```
   http://localhost:5000
   ```

---

## Учетные данные по умолчанию

После первого запуска создается пользователь:

| Логин | Пароль | Роль |
|-------|--------|------|
| `admin` | `admin123` | Администратор |

---

## Структура проекта

```
Task-Chat-Full/
├── app.py                  # Основное приложение (все роуты)
├── run.py                  # Точка входа
├── config.py               # Конфигурация
├── requirements.txt        # Зависимости
├── README.md               # Документация
├── models/
│   └── __init__.py         # SQLAlchemy модели
├── forms/
│   ├── __init__.py
│   ├── auth.py             # Формы аутентификации
│   └── task.py             # Формы задач
├── templates/
│   ├── base.html           # Базовый шаблон
│   ├── login.html          # Страница входа
│   ├── index.html          # Главная (список задач)
│   ├── chat.html           # Страница чата
│   └── admin_*.html        # Админ-шаблоны
├── static/
│   ├── css/
│   │   ├── style.css       # Основные стили
│   │   └── font-awesome.min.css
│   ├── js/
│   │   ├── main.js         # Общая логика
│   │   ├── chat.js         # Логика чата
│   │   └── tasks.js        # Логика задач
│   └── uploads/            # Загруженные файлы
├── instance/
│   └── taskchat.db         # SQLite база данных
└── logs/                   # Логи (в production)
```

---

## API Endpoints

### Авторизация
| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET/POST | `/login` | Вход |
| GET | `/logout` | Выход |
| GET/POST | `/register` | Регистрация (только админ) |

### Задачи
| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Главная страница |
| GET | `/api/tasks` | JSON список задач |
| GET | `/api/users/<role>` | Пользователи по роли |
| POST | `/create_task` | Создать задачу |
| POST | `/update_task/<id>` | Обновить задачу |

### Чат
| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/task/<id>/chat` | Страница чата |
| GET | `/task/<id>/get_messages` | Получить сообщения |
| POST | `/task/<id>/send_message` | Отправить сообщение |
| GET | `/unread_messages` | Непрочитанные сообщения |
| POST | `/task/<id>/typing` | Статус "печатает" |
| GET | `/task/<id>/typing_status` | Проверить "печатает" |

### Файлы
| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/task/<id>/files` | Список файлов |
| GET | `/task/<id>/files/<id>/download` | Скачать файл |
| GET | `/task/<id>/files/<id>/view` | Просмотр файла |
| DELETE | `/task/<id>/files/<id>` | Удалить файл |
| POST | `/task/<id>/add_files` | Загрузить файлы |

### Админ-панель
| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/admin` | Главная админки |
| GET | `/admin/users` | Пользователи |
| GET | `/admin/tasks` | Задачи |
| POST | `/admin/tasks/mass_update` | Массовое обновление |
| POST | `/admin/tasks/mass_delete` | Массовое удаление |

---

## Конфигурация

### Переменные окружения (.env)

```env
SECRET_KEY=ваш-секретный-ключ
DATABASE_URL=sqlite:///instance/taskchat.db
FLASK_ENV=development
```

### Настройки в config.py

- `SECRET_KEY` — ключ сессии
- `SQLALCHEMY_DATABASE_URI` — строка подключения к БД
- `UPLOAD_FOLDER` — папка для загруженных файлов
- `MAX_CONTENT_LENGTH` — максимальный размер файла (50 MB)
- `ALLOWED_EXTENSIONS` — разрешенные расширения файлов

---

## Разработка

### Добавление новых маршрутов

1. Откройте `app.py`
2. Добавьте новый роут:
   ```python
   @app.route('/new-endpoint', methods=['GET', 'POST'])
   @login_required
   def new_endpoint():
       return render_template('new.html')
   ```

### Работа с базой данных

Модели находятся в `models/__init__.py`:
- `User` — пользователи
- `Task` — задачи
- `ChatMessage` — сообщения
- `TaskFile` — файлы задач
- `TypingStatus` — статус "печатает"

### Сброс базы данных

```bash
rm instance/taskchat.db
python run.py  # БД создастся заново
```

---

## Production

### Запуск через Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app('production')"
```

### Настройка Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Лицензия

Проект создан для внутреннего использования.

---

## Поддержка

Вопросы и предложения направляйте разработчику.
