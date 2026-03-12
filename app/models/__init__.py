from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

db = SQLAlchemy()


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

    # Связи
    doctor_tasks = db.relationship('Task', foreign_keys='Task.doctor_id', backref='doctor', lazy=True)
    physicist_tasks = db.relationship('Task', foreign_keys='Task.physicist_id', backref='physicist', lazy=True)
    uploaded_files = db.relationship('TaskFile', foreign_keys='TaskFile.uploader_id', backref='uploader', lazy=True)
    typing_statuses = db.relationship('TypingStatus', backref='user', lazy=True)
    sent_messages = db.relationship('ChatMessage', foreign_keys='ChatMessage.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('ChatMessage', foreign_keys='ChatMessage.receiver_id', backref='receiver', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_last_seen(self):
        self.last_seen = datetime.utcnow()
        db.session.commit()

    def is_online(self):
        if self.last_seen:
            return datetime.utcnow() - self.last_seen < timedelta(minutes=5)
        return False

    def get_full_name(self):
        """Фамилия И.О."""
        if self.middle_name:
            return f'{self.first_name} {self.last_name[0]}.{self.middle_name[0]}.'
        return f'{self.first_name} {self.last_name[0]}.'

    def get_full_name_full(self):
        """Фамилия Имя Отчество"""
        if self.middle_name:
            return f'{self.first_name} {self.last_name} {self.middle_name}'
        return f'{self.first_name} {self.last_name}'

    def get_full_name_with_dept(self):
        """Фамилия Имя Отчество (Отделение)"""
        return f'{self.get_full_name_full()} ({self.department})'

    def get_role_display(self):
        roles = {
            'admin': 'Администратор',
            'doctor': 'Врач',
            'physicist': 'Физик'
        }
        return roles.get(self.role, self.role)

    def get_role_short(self):
        shorts = {
            'admin': 'А',
            'doctor': 'В',
            'physicist': 'Ф'
        }
        return shorts.get(self.role, self.role[0].upper())

    def __repr__(self):
        return f'<User {self.username}>'


class Task(db.Model):
    __tablename__ = 'task'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'in_progress', 'completed', 'cancelled'
    priority = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high', 'urgent'
    
    # Тип исследования и дополнительные поля
    research_type = db.Column(db.String(50), default='import_ct')  # 'import_ct', 'mr', 'pet'
    expert_group = db.Column(db.String(100), nullable=True)  # Экспертная группа (для import_ct)
    patient_card = db.Column(db.String(100), nullable=True)
    aria_availability = db.Column(db.String(20), nullable=True)  # 'new' (Новый) или 'existing' (Уже есть)
    ct_diagnostic = db.Column(db.String(100), nullable=True)
    treatment = db.Column(db.String(100), nullable=True)
    mr_diagnostic = db.Column(db.String(100), nullable=True)
    pet_diagnostic = db.Column(db.String(100), nullable=True)
    breath_control = db.Column(db.String(20), nullable=True)  # 'no', 'breath_hold', 'free'

    # Внешние ключи
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    physicist_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Даты
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Связи
    chat_messages = db.relationship('ChatMessage', backref='task', lazy=True, cascade='all, delete-orphan')
    files = db.relationship('TaskFile', backref='task', lazy=True, cascade='all, delete-orphan')

    def get_status_display(self):
        statuses = {
            'pending': 'Ожидает',
            'in_progress': 'В работе',
            'completed': 'Выполнена',
            'cancelled': 'Отменена'
        }
        return statuses.get(self.status, self.status)

    def get_priority_display(self):
        priorities = {
            'low': 'Низкий',
            'medium': 'Средний',
            'high': 'Высокий',
            'urgent': 'Срочно'
        }
        return priorities.get(self.priority, self.priority)

    def __repr__(self):
        return f'<Task {self.title}>'


class ChatMessage(db.Model):
    __tablename__ = 'chat_message'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ChatMessage {self.id}>'


class PersonalChat(db.Model):
    """Личный чат между двумя пользователями"""
    __tablename__ = 'personal_chat'

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    messages = db.relationship('PersonalMessage', backref='chat', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('user1_id', 'user2_id', name='unique_user_pair'),
    )

    def __repr__(self):
        return f'<PersonalChat {self.user1_id}-{self.user2_id}>'


class PersonalMessage(db.Model):
    """Сообщение в личном чате"""
    __tablename__ = 'personal_message'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('personal_chat.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связи
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_personal_messages')
    files = db.relationship('PersonalChatFile', backref='message', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PersonalMessage {self.id}>'


class PersonalChatFile(db.Model):
    """Файл в личном чате"""
    __tablename__ = 'personal_chat_file'

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('personal_message.id'), nullable=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_image = db.Column(db.Boolean, default=False)

    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)

    def __repr__(self):
        return f'<PersonalChatFile {self.original_filename}>'


class TaskFile(db.Model):
    __tablename__ = 'task_file'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)  # Уникальное имя на диске
    file_size = db.Column(db.Integer, nullable=False)  # Размер в байтах
    mime_type = db.Column(db.String(100), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Флаги типа файла
    is_image = db.Column(db.Boolean, default=False)
    is_pdf = db.Column(db.Boolean, default=False)
    is_dicom = db.Column(db.Boolean, default=False)
    is_archive = db.Column(db.Boolean, default=False)

    @property
    def file_size_mb(self):
        """Размер файла в МБ"""
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def download_url(self):
        """URL для скачивания файла"""
        return f'/task/{self.task_id}/files/{self.id}/download'

    @property
    def view_url(self):
        """URL для просмотра файла"""
        if self.is_image or self.is_pdf:
            return f'/task/{self.task_id}/files/{self.id}/view'
        return self.download_url

    def get_icon_class(self):
        """Возвращает класс иконки Font Awesome"""
        if self.is_image:
            return 'fa-file-image'
        elif self.is_pdf:
            return 'fa-file-pdf'
        elif self.is_dicom:
            return 'fa-file-medical'
        elif self.is_archive:
            return 'fa-file-archive'
        return 'fa-file-alt'

    def __repr__(self):
        return f'<TaskFile {self.original_filename}>'


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

    def __repr__(self):
        return f'<TypingStatus User:{self.user_id} Task:{self.task_id} Chat:{self.chat_id}>'
