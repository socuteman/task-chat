# API Документация Task-Chat v0.4.9

**Разработчик:** iak  
**Контакт:** bawel@ya.ru

---

## Обзор

Task-Chat предоставляет RESTful API для взаимодействия с системой. Все endpoints возвращают JSON.

### Базовый URL

```
http://localhost:5000
```

### Аутентификация

Большинство endpoints требуют аутентификации через сессию Flask-Login.

**Публичные endpoints (не требуют аутентификации):**
- `GET /api/stats`
- `GET /login`
- `POST /login`

---

## Публичные endpoints

### GET /api/stats

Получить статистику системы.

**Аутентификация:** Не требуется

**Ответ:**
```json
{
  "users": {
    "total": 10,
    "online": 3
  },
  "tasks": {
    "total": 50,
    "pending": 15,
    "in_progress": 20,
    "completed": 10,
    "cancelled": 5
  },
  "messages": {
    "total": 500,
    "today": 25
  },
  "files": {
    "total": 100,
    "size_bytes": 1048576
  },
  "uptime": 3600
}
```

**Поля ответа:**

| Поле | Тип | Описание |
|------|-----|----------|
| `users.total` | int | Всего пользователей |
| `users.online` | int | Пользователей онлайн (last_seen < 5 мин) |
| `tasks.total` | int | Всего задач |
| `tasks.pending` | int | Задачи в статусе «Ожидает» |
| `tasks.in_progress` | int | Задачи в работе |
| `tasks.completed` | int | Выполненные задачи |
| `tasks.cancelled` | int | Отменённые задачи |
| `messages.total` | int | Всего сообщений в чатах задач |
| `messages.today` | int | Сообщений сегодня |
| `files.total` | int | Всего файлов |
| `files.size_bytes` | int | Общий размер файлов в байтах |
| `uptime` | int | Время работы сервера в секундах |

---

## Endpoints авторизации

### POST /login

Вход в систему.

**Аутентификация:** Не требуется

**Тело запроса (form-data):**
```
username: admin
password: admin123
```

**Ответ при успехе:**
```
HTTP 302 Found
Location: /
```

**Ответ при ошибке:**
```
HTTP 302 Found
Location: /login
Flash: "Неверное имя пользователя или пароль"
```

### GET /logout

Выход из системы.

**Аутентификация:** Требуется

**Ответ:**
```
HTTP 302 Found
Location: /login
```

### POST /register

Регистрация нового пользователя.

**Аутентификация:** Требуется (только admin)

**Тело запроса (AJAX, form-data):**
```
username: ivanov
password: password123
role: doctor
first_name: Иванов
last_name: Иван
middle_name: Иванович
department: РО1
```

**Ответ при успехе:**
```json
{
  "success": true,
  "message": "Пользователь ivanov успешно зарегистрирован",
  "user": {
    "id": 5,
    "username": "ivanov",
    "role": "doctor"
  }
}
```

**Ответ при ошибке:**
```json
{
  "success": false,
  "error": "Пользователь с таким именем уже существует"
}
```

**Коды ошибок:**
- 400: Не заполнены поля или пароль < 3 символов
- 400: Пользователь существует

---

## Endpoints задач

### GET /api/tasks

Получить список задач.

**Аутентификация:** Требуется

**Логика доступа:**
- **Врач**: видит только свои задачи (`doctor_id = current_user.id`)
- **Физик**: видит все задачи
- **Админ**: видит все задачи

**Ответ:**
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Задача #1",
      "description": "Описание задачи",
      "status": "pending",
      "status_display": "Ожидает",
      "priority": "medium",
      "priority_display": "Средний",
      "doctor": "Иванов И.И.",
      "doctor_full_name": "Иванов Иван Иванович (РО1)",
      "created_at": "12.03.2026 10:00",
      "updated_at": "12.03.2026 11:00",
      "unread_count": 0,
      "files": [
        {
          "id": 1,
          "original_filename": "scan.pdf",
          "is_image": false,
          "is_pdf": true,
          "icon_class": "fa-file-pdf",
          "download_url": "/task/1/files/1/download",
          "view_url": "/task/1/files/1/view"
        }
      ],
      "patient_card": "12345",
      "aria_availability": "new",
      "research_type": "import_ct",
      "expert_group": "ПГШ",
      "ct_diagnostic": "Siemens (Корпус А)",
      "treatment": "Varian (Корпус Б)",
      "breath_control": "breath_hold",
      "mr_diagnostic": null,
      "pet_diagnostic": null
    }
  ],
  "stats": {
    "total": 10,
    "pending": 5,
    "in_progress": 3,
    "completed": 2,
    "cancelled": 0,
    "active_chats": 4
  }
}
```

**Поле `active_chats`:** Считается только задачи, где:
- Пользователь является участником (врач-создатель ИЛИ отправлял сообщения)
- Статус задачи не `completed` и не `cancelled`

### GET /api/task/<id>

Получить детальную информацию о задаче.

**Аутентификация:** Требуется

**Параметры:**
- `id` (int): ID задачи

**Логика доступа:**
- Врач-создатель: доступ есть
- Другие врачи: 403 Нет доступа
- Физики: доступ есть
- Админ: доступ есть

**Ответ:**
```json
{
  "id": 1,
  "title": "Задача #1",
  "status": "pending",
  "status_display": "Ожидает",
  "priority": "medium",
  "updated_at": "12.03.2026 11:00",
  "completed_at": null,
  "messages_count": 5,
  "participants": [
    {
      "id": 1,
      "username": "admin",
      "full_name": "Админ Админ Админович",
      "full_name_with_dept": "Админ Админ Админович (ТП)",
      "role": "Администратор",
      "is_online": true
    },
    {
      "id": 2,
      "username": "petrov",
      "full_name": "Петров Пётр Петрович",
      "full_name_with_dept": "Петров Пётр Петрович (ФРО)",
      "role": "Физик",
      "is_online": false
    }
  ],
  "patient_card": "12345",
  "research_type": "import_ct",
  "expert_group": "ПГШ",
  "ct_diagnostic": "Siemens (Корпус А)",
  "treatment": "Varian (Корпус Б)",
  "breath_control": "breath_hold",
  "mr_diagnostic": null,
  "pet_diagnostic": null
}
```

**Поле `participants`:** Врач-создатель + все, кто отправлял сообщения в чат задачи.

### POST /create_task

Создать новую задачу.

**Аутентификация:** Требуется (только doctor)

**Тело запроса (form-data):**
```
title: Задача #1
description: Описание задачи
study_type: import_ct
patient_card: 12345
aria_availability: new
ct_building: Корпус А
ct_equipment: Siemens
treatment_building: Корпус Б
treatment_device: Varian
breath_control: breath_hold
expert_group: ПГШ
files: <file>
```

**Логика:**
- Если `title` не заполнен, создаётся автоматически: `Задача #<id>`
- `ct_diagnostic` формируется из `ct_equipment` + `ct_building`
- `treatment` формируется из `treatment_device` + `treatment_building`
- `breath_control` сохраняется отдельно

**Ответ при успехе:**
```
HTTP 302 Found
Location: /
Flash: "Задача успешно создана"
```

**Ответ при ошибке:**
```
HTTP 302 Found
Location: /
Flash: "Заполните обязательные поля (номер карты пациента и тип исследования)"
```

**Коды ошибок:**
- 403: Только врачи могут создавать задачи

### POST /update_task/<id>

Обновить статус задачи.

**Аутентификация:** Требуется (physicist, admin)

**Параметры:**
- `id` (int): ID задачи

**Тело запроса (form-data):**
```
status: in_progress
```

**Логика:**
- Если статус `completed`, устанавливается `completed_at`
- Если статус не `completed`, `completed_at` сбрасывается
- `updated_at` устанавливается в текущее время

**Ответ при успехе:**
```
HTTP 302 Found
Location: /
Flash: "Статус задачи обновлен"
```

**Ответ при ошибке:**
```
HTTP 302 Found
Location: /
Flash: "У вас нет прав для обновления этой задачи"
```

**Коды ошибок:**
- 403: Только физики и администраторы

---

## Endpoints пользователей

### GET /api/users/<role>

Получить пользователей по роли.

**Аутентификация:** Требуется

**Параметры:**
- `role` (string): `admin`, `doctor`, `physicist`

**Ответ:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "is_online": true
  }
]
```

### GET /api/users/all

Получить всех пользователей.

**Аутентификация:** Требуется

**Ответ:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "full_name": "Админ Админ Админович",
    "department": "ТП",
    "role": "Администратор",
    "is_online": true
  }
]
```

### GET /api/online_users

Получить онлайн-пользователей, сгруппированных по отделениям.

**Аутентификация:** Требуется

**Ответ:**
```json
{
  "РО1": [
    {
      "id": 2,
      "username": "ivanov",
      "full_name": "Иванов Иван Иванович",
      "role": "Врач",
      "role_short": "В",
      "department": "РО1",
      "last_seen": "10:30"
    }
  ],
  "ФРО": [
    {
      "id": 3,
      "username": "petrov",
      "full_name": "Петров Пётр Петрович",
      "role": "Физик",
      "role_short": "Ф",
      "department": "ФРО",
      "last_seen": "10:25"
    }
  ]
}
```

---

## Endpoints чата задач

### GET /task/<id>/get_messages

Получить сообщения задачи.

**Аутентификация:** Требуется

**Параметры:**
- `id` (int): ID задачи
- `last_id` (int, optional): Получить сообщения после указанного ID

**Ответ:**
```json
{
  "messages": [
    {
      "id": 1,
      "content": "Привет! Как дела с задачей?",
      "sender_id": 1,
      "sender_name": "admin",
      "created_at": "10:30",
      "created_at_iso": "2026-03-12T10:30:00",
      "is_read": true
    }
  ]
}
```

### POST /task/<id>/send_message

Отправить сообщение в чат задачи.

**Аутентификация:** Требуется

**Параметры:**
- `id` (int): ID задачи

**Тело запроса (JSON):**
```json
{
  "content": "Текст сообщения"
}
```

**Логика определения получателя:**
- Если отправляет врач → `receiver_id` = первый физик
- Если отправляет физик → `receiver_id` = врач-создатель
- Если отправляет админ → `receiver_id` = врач-создатель

**Ответ при успехе:**
```json
{
  "success": true,
  "message": {
    "id": 5,
    "content": "Текст сообщения",
    "sender_id": 1,
    "created_at": "2026-03-12T11:00:00"
  }
}
```

**Ответ при ошибке:**
```json
{
  "error": "Нет доступа",
  "success": false
}
```

**Коды ошибок:**
- 400: Пустое сообщение
- 403: Врач может писать только в свои задачи

### GET /unread_messages

Получить непрочитанные сообщения.

**Аутентификация:** Требуется

**Ответ:**
```json
{
  "tasks_with_unread": [
    {
      "task_id": 1,
      "task_title": "Задача #1",
      "unread_count": 3,
      "last_sender": "petrov"
    }
  ],
  "total_unread": 3
}
```

### POST /task/<id>/typing

Отправить статус «печатает».

**Аутентификация:** Требуется

**Параметры:**
- `id` (int): ID задачи

**Тело запроса (JSON):**
```json
{
  "is_typing": true
}
```

**Ответ:**
```json
{
  "success": true
}
```

### GET /task/<id>/typing_status

Получить статус «печатает».

**Аутентификация:** Требуется

**Параметры:**
- `id` (int): ID задачи

**Ответ:**
```json
{
  "is_typing": true,
  "username": "petrov"
}
```

**Логика:**
- Показывает первого пользователя, который печатает
- Статус сбрасывается через 5 секунд

---

## Endpoints файлов задач

### GET /task/<id>/files

Получить список файлов задачи.

**Аутентификация:** Требуется

**Параметры:**
- `id` (int): ID задачи

**Ответ:**
```json
{
  "files": [
    {
      "id": 1,
      "original_filename": "scan.pdf",
      "stored_filename": "abc123.pdf",
      "file_size": 1048576,
      "file_size_mb": 1.0,
      "mime_type": "application/pdf",
      "is_image": false,
      "is_pdf": true,
      "is_dicom": false,
      "is_archive": false,
      "icon_class": "fa-file-pdf",
      "uploaded_at": "12.03.2026 10:00",
      "uploader_id": 1,
      "uploader_name": "admin"
    }
  ]
}
```

### GET /task/<id>/files/<file_id>/download

Скачать файл.

**Аутентификация:** Требуется

**Параметры:**
- `id` (int): ID задачи
- `file_id` (int): ID файла

**Ответ:**
```
HTTP 200 OK
Content-Disposition: attachment; filename="scan.pdf"
Content-Type: application/pdf
<binary data>
```

### GET /task/<id>/files/<file_id>/view

Просмотреть файл (изображения, PDF).

**Аутентификация:** Требуется

**Параметры:**
- `id` (int): ID задачи
- `file_id` (int): ID файла

**Ответ:**
```
HTTP 200 OK
Content-Type: image/jpeg (или application/pdf)
<binary data>
```

### POST /task/<id>/add_files

Загрузить файлы в задачу.

**Аутентификация:** Требуется

**Параметры:**
- `id` (int): ID задачи

**Тело запроса (form-data):**
```
files: <file1>
files: <file2>
...
```

**Ответ при успехе:**
```json
{
  "success": true,
  "uploaded_files": [
    {
      "id": 2,
      "original_filename": "doc2.pdf",
      "download_url": "/task/1/files/2/download"
    }
  ],
  "errors": []
}
```

### DELETE /task/<id>/files/<file_id>

Удалить файл.

**Аутентификация:** Требуется

**Параметры:**
- `id` (int): ID задачи
- `file_id` (int): ID файла

**Ответ при успехе:**
```json
{
  "success": true
}
```

---

## Endpoints личных чатов

### GET /chats

Получить список личных чатов.

**Аутентификация:** Требуется

**Ответ:**
```json
{
  "chats": [
    {
      "chat_id": 1,
      "partner_id": 2,
      "partner_username": "ivanov",
      "partner_full_name": "Иванов Иван Иванович",
      "partner_full_name_short": "Иванов И.И.",
      "partner_role": "Врач",
      "partner_department": "РО1",
      "partner_is_online": true,
      "unread_count": 2,
      "last_message_content": "Привет!",
      "last_message_is_file": false,
      "last_message_file_type": null,
      "last_message_date": "12.03",
      "last_message_time": "10:30"
    }
  ]
}
```

### POST /chat/start/<user_id>

Начать чат с пользователем.

**Аутентификация:** Требуется

**Параметры:**
- `user_id` (int): ID собеседника

**Ответ при успехе:**
```json
{
  "chat_id": 1,
  "created": false
}
```

**Ответ при ошибке:**
```json
{
  "error": "Нельзя начать чат с самим собой"
}
```

### POST /chat/<chat_id>/send_message

Отправить сообщение в личный чат.

**Аутентификация:** Требуется

**Параметры:**
- `chat_id` (int): ID чата

**Тело запроса (JSON):**
```json
{
  "content": "Текст сообщения",
  "file_ids": [1, 2]
}
```

**Ответ при успехе:**
```json
{
  "success": true,
  "message": {
    "id": 5,
    "content": "Текст сообщения",
    "sender_id": 1,
    "created_at_iso": "2026-03-12T11:00:00",
    "files": [
      {
        "id": 1,
        "original_filename": "image.png",
        "file_size_mb": 0.5,
        "is_image": true,
        "url": "/chat/1/files/1/view"
      }
    ]
  }
}
```

### GET /chat/<chat_id>/get_messages

Получить сообщения личного чата.

**Аутентификация:** Требуется

**Параметры:**
- `chat_id` (int): ID чата
- `last_id` (int, optional): Получить сообщения после указанного ID

**Ответ:**
```json
[
  {
    "id": 1,
    "content": "Привет!",
    "sender_id": 1,
    "is_read": true,
    "created_at_iso": "2026-03-12T10:30:00",
    "files": []
  }
]
```

### POST /chat/<chat_id>/upload_file

Загрузить файл в личный чат.

**Аутентификация:** Требуется

**Параметры:**
- `chat_id` (int): ID чата

**Тело запроса (form-data):**
```
file: <file>
```

**Ответ при успехе:**
```json
{
  "success": true,
  "file": {
    "id": 1,
    "original_filename": "image.png",
    "file_size_mb": 0.5,
    "is_image": true,
    "url": "/chat/1/files/1/download"
  }
}
```

### GET /chat/<chat_id>/files/<file_id>/download

Скачать файл из личного чата.

**Аутентификация:** Требуется

**Параметры:**
- `chat_id` (int): ID чата
- `file_id` (int): ID файла

### GET /chat/<chat_id>/files/<file_id>/view

Просмотреть файл (изображения).

**Аутентификация:** Требуется

**Параметры:**
- `chat_id` (int): ID чата
- `file_id` (int): ID файла

### POST /chat/<chat_id>/typing

Статус «печатает» для личного чата.

**Аутентификация:** Требуется

**Параметры:**
- `chat_id` (int): ID чата

**Тело запроса (JSON):**
```json
{
  "is_typing": true
}
```

### GET /chat/<chat_id>/typing_status

Получить статус «печатает» личного чата.

**Аутентификация:** Требуется

**Параметры:**
- `chat_id` (int): ID чата

**Ответ:**
```json
{
  "is_typing": true,
  "username": "ivanov"
}
```

### GET /api/personal_chats/unread_count

Получить количество непрочитанных личных сообщений.

**Аутентификация:** Требуется

**Ответ:**
```json
{
  "total_unread": 5
}
```

---

## Админ endpoints

### GET /admin/api/stats

Получить расширенную статистику.

**Аутентификация:** Требуется (только admin)

**Ответ:**
```json
{
  "total_users": 10,
  "total_tasks": 50,
  "total_messages": 500,
  "total_files": 100,
  "total_file_size_mb": 10.5,
  "tasks_by_status": {
    "pending": 15,
    "in_progress": 20,
    "completed": 10,
    "cancelled": 5
  },
  "users_by_role": {
    "admin": 1,
    "doctor": 5,
    "physicist": 4
  },
  "active_chats": 8,
  "total_personal_chats": 12,
  "active_personal_chats": 5,
  "total_personal_messages": 200,
  "files_by_type": [
    {"type": "images", "count": 30, "size_mb": 5.2},
    {"type": "pdf", "count": 50, "size_mb": 3.8}
  ]
}
```

### GET /admin/api/users

Получить список всех пользователей.

**Аутентификация:** Требуется (только admin)

**Ответ:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "role_display": "Администратор",
    "first_name": "Админ",
    "last_name": "Админов",
    "middle_name": "",
    "full_name": "Админ А.",
    "department": "ТП",
    "created_at": "12.03.2026 10:00",
    "last_seen": "12.03.2026 11:00",
    "is_online": true
  }
]
```

### GET /admin/api/tasks

Получить список всех задач.

**Аутентификация:** Требуется (только admin)

**Ответ:**
```json
[
  {
    "id": 1,
    "title": "Задача #1",
    "status": "pending",
    "status_display": "Ожидает",
    "doctor": "Иванов И.И.",
    "doctor_full_name": "Иванов Иван Иванович (РО1)",
    "research_type": "import_ct",
    "patient_card": "12345",
    "created_at": "12.03.2026 10:00",
    "updated_at": "12.03.2026 11:00"
  }
]
```

### GET /admin/api/doctors

Получить список врачей.

**Аутентификация:** Требуется (только admin)

**Ответ:**
```json
[
  {
    "id": 2,
    "username": "ivanov"
  }
]
```

### POST /admin/tasks/mass_update

Массовое обновление задач.

**Аутентификация:** Требуется (только admin)

**Тело запроса (form-data):**
```
task_ids: 1
task_ids: 2
task_ids: 3
action: change_status
new_status: completed
```

**Действия:**
- `change_status` — изменить статус
- `change_doctor` — изменить врача

**Ответ при успехе:**
```
HTTP 302 Found
Location: /admin/tasks
Flash: "Задачи обновлены"
```

### POST /admin/tasks/mass_delete

Массовое удаление задач.

**Аутентификация:** Требуется (только admin)

**Тело запроса (form-data):**
```
task_ids: 1
task_ids: 2
action: delete
```

**Ответ при успехе:**
```
HTTP 302 Found
Location: /admin/tasks
Flash: "Задачи удалены"
```

---

## Коды ошибок

### HTTP статусы

| Код | Описание |
|-----|----------|
| 200 | Успех |
| 302 | Переадресация |
| 400 | Неверный запрос |
| 401 | Неавторизован |
| 403 | Доступ запрещён |
| 404 | Не найдено |
| 500 | Внутренняя ошибка сервера |

### Формат ошибок JSON

```json
{
  "error": "Описание ошибки",
  "success": false
}
```

---

## Примеры использования

### Python (requests)

```python
import requests

# Вход
session = requests.Session()
response = session.post('http://localhost:5000/login', data={
    'username': 'admin',
    'password': 'admin123'
})

# Получить статистику
response = session.get('http://localhost:5000/api/stats')
stats = response.json()

# Получить задачи
response = session.get('http://localhost:5000/api/tasks')
tasks = response.json()

# Создать задачу
response = session.post('http://localhost:5000/create_task', data={
    'study_type': 'import_ct',
    'patient_card': '12345'
})

# Отправить сообщение
response = session.post('http://localhost:5000/task/1/send_message', 
                       json={'content': 'Привет!'})
```

### cURL

```bash
# Статистика (публичный endpoint)
curl http://localhost:5000/api/stats

# Вход с cookies
curl -c cookies.txt -b cookies.txt \
  -X POST http://localhost:5000/login \
  -d "username=admin&password=admin123"

# Получить задачи
curl -b cookies.txt http://localhost:5000/api/tasks
```

---

## Ограничения

### Размер файлов

- Максимальный размер файла: **50 MB**
- `MAX_CONTENT_LENGTH = 50 * 1024 * 1024`

### Разрешённые расширения

```python
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
ALLOWED_PDF_EXTENSIONS = {'pdf'}
ALLOWED_DICOM_EXTENSIONS = {'dcm', 'dicom'}
ALLOWED_ARCHIVE_EXTENSIONS = {'zip', 'rar', '7z'}
ALLOWED_DOCUMENT_EXTENSIONS = {'doc', 'docx', 'xls', 'xlsx', 'txt'}
```

---

**Версия документации:** 0.4.9  
**Дата обновления:** Март 2026
