# Техническая документация Task-Chat Server v0.4.9

**Разработчик:** iak  
**Контакт:** bawel@ya.ru  
**Дата:** Март 2026

---

## Содержание

1. [Архитектура приложения](#архитектура-приложения)
2. [Модули и компоненты](#модули-и-компоненты)
3. [Модели данных](#модели-данных)
4. [Система аутентификации](#система-аутентификации)
5. [Права доступа](#права-доступа)
6. [Логирование](#логирование)
7. [Обработка файлов](#обработка-файлов)
8. [Сборка EXE](#сборка-exe)

---

## Архитектура приложения

### Технологический стек

- **Backend:** Python 3.8+, Flask 2.3.3
- **ORM:** SQLAlchemy 2.0
- **База данных:** SQLite 3.x
- **Аутентификация:** Flask-Login
- **Формы:** Flask-WTF, WTForms
- **WSGI сервер:** Waitress (Windows), Gunicorn (Linux)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript

### Паттерн Application Factory

Приложение создаётся через factory-функцию `create_app()`:

```python
def create_app(config_name='development'):
    app = Flask(__name__, template_folder=templates_folder, static_folder=static_folder)
    app.config.from_object(config[config_name])
    
    # Инициализация расширений
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    # Регистрация маршрутов (внутри функции)
    @app.route('/')
    def index():
        ...
    
    return app
```

### Точки входа

**run.py:**
```python
from app.app import create_app
app = create_app('production')

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000, threads=4)
```

**server_runner.py:**
Альтернативный entry point для запуска только сервера (без GUI).

---

## Модули и компоненты

### app.py

Основной модуль приложения. Содержит все маршруты:

| Раздел | Маршруты |
|--------|----------|
| Авторизация | `/login`, `/logout`, `/register` |
| Главная | `/`, `/online_users` |
| API задач | `/api/tasks`, `/api/task/<id>`, `/api/users/*`, `/api/stats` |
| CRUD задач | `/create_task`, `/update_task/<id>` |
| Чат задач | `/task/<id>/chat`, `/task/<id>/get_messages`, `/task/<id>/send_message` |
| Файлы задач | `/task/<id>/files`, `/task/<id>/files/<id>/download`, `/task/<id>/add_files` |
| Личные чаты | `/chats`, `/chat/<id>`, `/chat/start/<user_id>` |
| Админ-панель | `/admin`, `/admin/users`, `/admin/tasks`, `/admin/tasks/mass_update` |

### config.py

Модуль конфигурации:

```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    UPLOAD_FOLDER = data_dir / 'uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
    LOG_DIR = data_dir / 'logs'
```

**Динамическое определение путей:**
- При запуске из EXE: `data/` рядом с executable
- При запуске из исходников: `../data/` относительно `app/`

### models/__init__.py

Модели SQLAlchemy:
- `User` — пользователи
- `Task` — задачи
- `ChatMessage` — сообщения в чате задачи
- `TaskFile` — файлы задач
- `TypingStatus` — статус "печатает"
- `PersonalChat` — личный чат
- `PersonalMessage` — сообщение в личном чате
- `PersonalChatFile` — файл в личном чате

### forms/

- **auth.py:** `LoginForm`, `RegistrationForm`, `PasswordChangeForm`
- **task.py:** `TaskForm`, `TaskEditForm`, `CommentForm`, `MassActionForm`

### logging_config.py

Модуль логирования с поддержкой:
- JSON и текстовый формат
- Ротация по размеру и времени
- Категории: `auth`, `tasks`, `chat`, `files`, `admin`, `system`

---

## Модели данных

### User

```python
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'doctor', 'physicist'
    first_name = db.Column(db.String(80), nullable=False)  # Фамилия
    last_name = db.Column(db.String(80), nullable=False)   # Имя
    middle_name = db.Column(db.String(80), nullable=True)  # Отчество
    department = db.Column(db.String(50), nullable=False)  # Отделение
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
```

**Методы:**
- `set_password(password)` — хэширование пароля
- `check_password(password)` — проверка пароля
- `update_last_seen()` — обновление времени последнего посещения
- `is_online()` — проверка онлайн (last_seen < 5 минут)
- `get_full_name()` — Фамилия И.О.
- `get_full_name_full()` — Фамилия Имя Отчество
- `get_full_name_with_dept()` — Фамилия Имя Отчество (Отделение)
- `get_role_display()` — отображение роли (Администратор, Врач, Физик)
- `get_role_short()` — краткая роль (А, В, Ф)

### Task

```python
class Task(db.Model):
    __tablename__ = 'task'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')
    priority = db.Column(db.String(20), default='medium')
    research_type = db.Column(db.String(50), default='import_ct')
    expert_group = db.Column(db.String(100), nullable=True)
    patient_card = db.Column(db.String(100), nullable=True)
    aria_availability = db.Column(db.String(20), nullable=True)
    ct_diagnostic = db.Column(db.String(100), nullable=True)
    treatment = db.Column(db.String(100), nullable=True)
    mr_diagnostic = db.Column(db.String(100), nullable=True)
    pet_diagnostic = db.Column(db.String(100), nullable=True)
    breath_control = db.Column(db.String(20), nullable=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    physicist_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
```

**Методы:**
- `get_status_display()` — отображение статуса
- `get_priority_display()` — отображение приоритета

### ChatMessage

```python
class ChatMessage(db.Model):
    __tablename__ = 'chat_message'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### TaskFile

```python
class TaskFile(db.Model):
    __tablename__ = 'task_file'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_image = db.Column(db.Boolean, default=False)
    is_pdf = db.Column(db.Boolean, default=False)
    is_dicom = db.Column(db.Boolean, default=False)
    is_archive = db.Column(db.Boolean, default=False)
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def download_url(self):
        return f'/task/{self.task_id}/files/{self.id}/download'
    
    @property
    def view_url(self):
        if self.is_image or self.is_pdf:
            return f'/task/{self.task_id}/files/{self.id}/view'
        return self.download_url
    
    def get_icon_class(self):
        if self.is_image: return 'fa-file-image'
        elif self.is_pdf: return 'fa-file-pdf'
        elif self.is_dicom: return 'fa-file-medical'
        elif self.is_archive: return 'fa-file-archive'
        return 'fa-file-alt'
```

### TypingStatus

```python
class TypingStatus(db.Model):
    __tablename__ = 'typing_status'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('personal_chat.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_typing = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('task_id', 'user_id', name='unique_task_user_typing'),
        db.UniqueConstraint('chat_id', 'user_id', name='unique_chat_user_typing'),
    )
```

### PersonalChat

```python
class PersonalChat(db.Model):
    __tablename__ = 'personal_chat'
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user1_id', 'user2_id', name='unique_user_pair'),
    )
```

### PersonalMessage

```python
class PersonalMessage(db.Model):
    __tablename__ = 'personal_message'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('personal_chat.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_personal_messages')
    files = db.relationship('PersonalChatFile', backref='message', lazy=True, cascade='all, delete-orphan')
```

### PersonalChatFile

```python
class PersonalChatFile(db.Model):
    __tablename__ = 'personal_chat_file'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('personal_message.id'), nullable=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_image = db.Column(db.Boolean, default=False)
```

---

## Система аутентификации

### Вход в систему

```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            user.update_last_seen()
            return redirect(url_for('index'))
        flash('Неверное имя пользователя или пароль', 'danger')
    
    return render_template('login.html', form=form)
```

### Регистрация (только admin)

```python
@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role != 'admin':
        flash('Только администратор может регистрировать пользователей', 'danger')
        return redirect(url_for('index'))
    
    # AJAX запрос из модального окна
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'doctor')
        # ...
        
        user = User(username=username, role=role, ...)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, ...})
```

### Проверка прав доступа

```python
@login_required
def some_route():
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))
```

---

## Права доступа

### Детальная матрица прав

| Функция | admin | doctor | physicist |
|---------|-------|--------|-----------|
| Просмотр всех задач | ✅ | ❌ (только свои) | ✅ |
| Создание задач | ❌ | ✅ | ❌ |
| Редактирование задачи | ✅ | ❌ | ❌ |
| Изменение статуса | ✅ | ❌ | ✅ |
| Удаление задачи | ✅ | ❌ | ❌ |
| Чат задачи | ✅ | ✅ (свои) | ✅ |
| Загрузка файлов | ✅ | ✅ (свои) | ✅ |
| Регистрация пользователей | ✅ | ❌ | ❌ |
| Удаление пользователей | ✅ | ❌ | ❌ |
| Смена пароля пользователя | ✅ | ❌ | ❌ |
| Массовые операции | ✅ | ❌ | ❌ |
| Админ-панель | ✅ | ❌ | ❌ |

### Логика доступа к чату задачи

**Доступ к чату:**
- Врач-создатель: всегда
- Физик: всегда
- Админ: всегда
- Другие врачи: нет

**Отправка сообщения:**
```python
@app.route('/task/<int:id>/send_message', methods=['POST'])
def send_message(id):
    task = Task.query.get_or_404(id)
    
    # Врач может писать только в свои задачи
    if current_user.role == 'doctor' and current_user.id != task.doctor_id:
        return jsonify({'error': 'Нет доступа', 'success': False}), 403
    
    # Определение получателя
    if current_user.role == 'admin':
        receiver_id = task.doctor_id
    elif current_user.role == 'physicist':
        receiver_id = task.doctor_id
    elif current_user.id == task.doctor_id:
        # Врач отправляет - получают все физики
        physicist = User.query.filter_by(role='physicist').first()
        receiver_id = physicist.id if physicist else task.physicist_id
```

---

## Логирование

### Категории логов

| Категория | События |
|-----------|---------|
| `auth` | Вход, выход, регистрация, смена пароля |
| `tasks` | Создание, обновление, удаление задач |
| `chat` | Отправка сообщений в чат задач |
| `files` | Загрузка файлов |
| `admin` | Действия администратора |
| `system` | Системные события |

### Пример записи лога

```python
app.logger.info(f'Task #{task.id} created by {current_user.username}', 
                extra={'category': 'tasks', 'task_id': task.id, 
                       'user_id': current_user.id, 'username': current_user.username})
```

### Конфигурация логирования

```python
class TaskChatLogger:
    def __init__(self, log_dir='logs', log_format='json', log_level='INFO'):
        # Ротация по размеру (10 MB)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=10
        )
        # Ротация по времени (ежедневно)
        time_handler = TimedRotatingFileHandler(
            time_log_file, when='D', interval=1, backupCount=10
        )
```

---

## Обработка файлов

### Загрузка файлов

```python
@app.route('/task/<int:id>/add_files', methods=['POST'])
def add_files(id):
    task = Task.query.get_or_404(id)
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(task.id))
    os.makedirs(upload_dir, exist_ok=True)
    
    for file in request.files.getlist('files'):
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            file.save(file_path)
            
            # Определение типа файла
            ext = filename.rsplit('.', 1)[1].lower()
            task_file = TaskFile(
                task_id=task.id,
                uploader_id=current_user.id,
                original_filename=filename,
                stored_filename=unique_filename,
                file_size=os.path.getsize(file_path),
                is_image=ext in app.config['ALLOWED_IMAGE_EXTENSIONS'],
                is_pdf=ext in app.config['ALLOWED_PDF_EXTENSIONS'],
                is_dicom=ext in app.config['ALLOWED_DICOM_EXTENSIONS'],
                is_archive=ext in app.config['ALLOWED_ARCHIVE_EXTENSIONS']
            )
            db.session.add(task_file)
    
    db.session.commit()
```

### Раздача файлов

```python
@app.route('/static/uploads/<path:filename>')
def serve_uploaded_file(filename):
    if getattr(sys, 'frozen', False):
        upload_base = Path(sys.executable).parent / 'data' / 'uploads'
    else:
        upload_base = Path(__file__).parent.parent / 'data' / 'uploads'
    
    return send_from_directory(str(upload_base), filename)
```

---

## Сборка EXE

### taskchat.spec

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

exe = EXE(
    pyz, a.scripts, [],
    name='TaskChat-Server',
    console=True,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    name='TaskChat-Server',
)
```

### Процесс сборки

```bash
pip install pyinstaller
pyinstaller --clean taskchat.spec
```

**Результат:** `dist/TaskChat-Server/TaskChat-Server.exe`

### Пути в EXE

```python
if getattr(sys, 'frozen', False):
    # Запуск из EXE
    basedir = Path(sys.executable).parent
    data_dir = basedir / 'data'
else:
    # Запуск из исходников
    basedir = Path(__file__).parent.resolve()
    data_dir = basedir.parent / 'data'
```

---

## Временная зона

Все даты отображаются в **Московском времени (UTC+3)**:

```python
@app.context_processor
def utility_processor():
    def moscow_time(dt):
        if dt is None:
            return None
        return dt + timedelta(hours=3)
    return dict(moscow_time=moscow_time)
```

Использование в шаблонах:
```jinja2
{{ moscow_time(task.created_at).strftime('%d.%m.%Y %H:%M') }}
```

---

## Онлайн-статус

```python
def is_online(self):
    if self.last_seen:
        return datetime.utcnow() - self.last_seen < timedelta(minutes=5)
    return False
```

Обновление `last_seen`:
```python
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.update_last_seen()
```

---

## Создание пользователя admin по умолчанию

```python
with app.app_context():
    db.create_all()
    if not User.query.first():
        admin = User(
            username='admin', 
            role='admin', 
            first_name='Админ', 
            last_name='Админов', 
            department='ТП'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Создан пользователь admin / admin123")
```

---

## Поддержка

**Разработчик:** iak  
**Email:** bawel@ya.ru
