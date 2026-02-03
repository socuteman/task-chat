# Copyright (c) 2026 iak
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import sys
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, get_flashed_messages
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from models import db, User, Task, ChatMessage
from datetime import datetime, timedelta

def moscow_time(dt):
    """Преобразует время UTC в московское"""
    if dt is None:
        return None
    return dt + timedelta(hours=3)

# Определяем пути для EXE режима
def get_base_path():
    """Определяем базовый путь в зависимости от режима запуска"""
    if getattr(sys, 'frozen', False):
        # Режим EXE
        return sys._MEIPASS
    else:
        # Режим скрипта
        return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()

app = Flask(__name__, 
            static_folder=os.path.join(BASE_PATH, 'static'),
            template_folder=os.path.join(BASE_PATH, 'templates'))

# Сделаем функцию доступной в шаблонах (ПЕРЕМЕЩАЕМ ЗДЕСЬ, ПОСЛЕ СОЗДАНИЯ app)
@app.context_processor
def utility_processor():
    return dict(moscow_time=moscow_time)

# Настройка конфигурации
app.config['SECRET_KEY'] = 'task-chat-secret-key-2024-change-this'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Определяем путь к базе данных
if getattr(sys, 'frozen', False):
    # Если запущено как EXE, база рядом с EXE файлом
    database_path = os.path.join(os.path.dirname(sys.executable), 'task_chat.db')
else:
    # Если запущено как скрипт, база в текущей папке
    database_path = 'task_chat.db'

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print(f"База данных: {database_path}")

# Инициализация расширений
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = ''  # Empty message to prevent automatic flashing
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Мидлварь для обновления времени последней активности
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.update_last_seen()

# Создание таблиц и администратора по умолчанию
def init_database():
    with app.app_context():
        db.create_all()
        # Создание администратора по умолчанию, если его нет
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Создан администратор по умолчанию: admin / admin123")

# Вызов инициализации базы данных
init_database()

# Главная страница
@app.route('/')
def index():
    if not current_user.is_authenticated:
        # When accessing root directly, don't show the login message
        return redirect(url_for('login'))
    
    if current_user.role == 'doctor':
        tasks = Task.query.filter_by(doctor_id=current_user.id).order_by(Task.created_at.desc()).all()
    elif current_user.role == 'physicist':
        tasks = Task.query.filter_by(physicist_id=current_user.id).order_by(Task.created_at.desc()).all()
    else:
        tasks = Task.query.order_by(Task.created_at.desc()).all()
    
    return render_template('index.html', tasks=tasks)

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role != 'admin':
        flash('Только администратор может регистрировать пользователей')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов')
            return redirect(url_for('register'))
        
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash(f'Пользователь {username} успешно зарегистрирован')
        return redirect(url_for('admin_panel'))
    
    return render_template('register.html')

# Авторизация
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Check if this is a redirect from a protected page by looking for 'next' in the URL
    # Only show the login message if the 'next' parameter is for a page other than the root
    next_url = request.args.get('next')
    if next_url:
        # Compare the next URL with the root URL to see if it's the same
        root_url = request.url_root.rstrip('/')
        next_clean = next_url.rstrip('/')
        
        # Don't show the message if redirecting from the root path
        if next_clean != root_url and next_clean != root_url + '/':
            flash('Пожалуйста, войдите для доступа к этой странице', 'info')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.update_last_seen()
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль')
    
    return render_template('login.html')

# Override the default login message behavior
@login_manager.unauthorized_handler
def custom_unauthorized_handler():
    # Always redirect to login with the next parameter
    # The login route itself will handle whether to show the message
    return redirect(url_for('login', next=request.url))

# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Создание задачи
@app.route('/create_task', methods=['POST'])
@login_required
def create_task():
    if current_user.role != 'doctor':
        flash('Только врачи могут создавать задачи')
        return redirect(url_for('index'))
    
    title = request.form['title']
    description = request.form['description']
    physicist_id = request.form['physicist_id']
    priority = request.form.get('priority', 'medium')
    
    task = Task(
        title=title,
        description=description,
        doctor_id=current_user.id,
        physicist_id=physicist_id,
        priority=priority
    )
    
    db.session.add(task)
    db.session.commit()
    
    flash('Задача успешно создана')
    return redirect(url_for('index'))

# Обновление статуса задачи
@app.route('/update_task/<int:task_id>', methods=['POST'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    if current_user.role != 'physicist' or current_user.id != task.physicist_id:
        flash('Вы не можете обновить эту задачу')
        return redirect(url_for('index'))
    
    task.status = request.form['status']
    task.updated_at = datetime.utcnow()
    
    if task.status == 'completed':
        task.completed_at = datetime.utcnow()
    
    db.session.commit()
    flash('Статус задачи обновлен')
    return redirect(url_for('index'))

# Страница чата для задачи
@app.route('/task/<int:task_id>/chat')
@login_required
def task_chat(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Проверяем, имеет ли пользователь доступ к чату этой задачи
    if current_user.id not in [task.doctor_id, task.physicist_id] and current_user.role != 'admin':
        flash('У вас нет доступа к чату этой задачи')
        return redirect(url_for('index'))
    
    # Определяем собеседника
    if current_user.id == task.doctor_id:
        chat_partner = task.physicist
    else:
        chat_partner = task.doctor
    
    messages = ChatMessage.query.filter_by(task_id=task_id).order_by(ChatMessage.created_at).all()
    
    # Помечаем непрочитанные сообщения как прочитанные
    unread_messages = ChatMessage.query.filter_by(
        task_id=task_id, 
        receiver_id=current_user.id,
        is_read=False
    ).all()
    
    for message in unread_messages:
        message.is_read = True
    db.session.commit()
    
    return render_template('chat.html', task=task, chat_partner=chat_partner, messages=messages)

# Отправка сообщения в чат
@app.route('/task/<int:task_id>/send_message', methods=['POST'])
@login_required
def send_message(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Проверяем, имеет ли пользователь доступ к чату этой задачи
    if current_user.id not in [task.doctor_id, task.physicist_id]:
        return jsonify({'error': 'Нет доступа'}), 403
    
    data = request.get_json()
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Сообщение не может быть пустым'}), 400
    
    # Определяем получателя
    if current_user.id == task.doctor_id:
        receiver_id = task.physicist_id
    else:
        receiver_id = task.doctor_id
    
    # Создаем сообщение
    message = ChatMessage(
        content=content,
        task_id=task_id,
        sender_id=current_user.id,
        receiver_id=receiver_id
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'sender': current_user.username,
            'sender_id': current_user.id,
            'created_at': message.created_at.strftime('%H:%M %d.%m.%Y'),
            'is_own': True
        }
    })

# Получение новых сообщений
@app.route('/task/<int:task_id>/get_messages')
@login_required
def get_messages(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Проверяем, имеет ли пользователь доступ к чату этой задачи
    if current_user.id not in [task.doctor_id, task.physicist_id]:
        return jsonify({'error': 'Нет доступа'}), 403
    
    # Получаем все сообщения задачи
    messages = ChatMessage.query.filter_by(task_id=task_id).order_by(ChatMessage.created_at).all()
    
    # Помечаем непрочитанные сообщения как прочитанные
    unread_messages = ChatMessage.query.filter_by(
        task_id=task_id, 
        receiver_id=current_user.id,
        is_read=False
    ).all()
    
    for message in unread_messages:
        message.is_read = True
    db.session.commit()
    
    # Форматируем сообщения для JSON
    messages_data = []
    for message in messages:
        messages_data.append({
            'id': message.id,
            'content': message.content,
            'sender': message.sender.username,
            'sender_id': message.sender_id,
            'created_at': moscow_time(message.created_at).strftime('%H:%M %d.%m.%Y') if message.created_at else None,
            'is_own': message.sender_id == current_user.id,
            'is_read': message.is_read
        })
    
    # Получаем информацию о собеседнике
    if current_user.id == task.doctor_id:
        chat_partner = task.physicist
    else:
        chat_partner = task.doctor
    
    return jsonify({
        'messages': messages_data,
        'chat_partner': {
            'id': chat_partner.id,
            'username': chat_partner.username,
            'role': chat_partner.role,
            'is_online': chat_partner.is_online()
        },
        'task': {
            'id': task.id,
            'title': task.title,
            'status': task.status
        }
    })

# Получение списка непрочитанных сообщений
@app.route('/unread_messages')
@login_required
def get_unread_messages():
    # Получаем все задачи, где у пользователя есть непрочитанные сообщения
    tasks_with_unread = db.session.query(Task).join(ChatMessage).filter(
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.is_read == False
    ).distinct().all()
    
    result = []
    for task in tasks_with_unread:
        unread_count = ChatMessage.query.filter_by(
            task_id=task.id,
            receiver_id=current_user.id,
            is_read=False
        ).count()
        
        # Определяем отправителя последнего сообщения
        last_message = ChatMessage.query.filter_by(task_id=task.id).order_by(ChatMessage.created_at.desc()).first()
        
        result.append({
            'task_id': task.id,
            'task_title': task.title,
            'unread_count': unread_count,
            'last_sender': last_message.sender.username if last_message else None,
            'last_message_time': moscow_time(last_message.created_at).strftime('%H:%M') if last_message else None
        })
    
    total_unread = sum(item['unread_count'] for item in result)
    
    return jsonify({
        'tasks_with_unread': result,
        'total_unread': total_unread
    })

# Панель администратора
@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    
    users = User.query.all()
    tasks = Task.query.all()
    
    # Статистика
    total_messages = ChatMessage.query.count()
    active_chats = db.session.query(ChatMessage.task_id).distinct().count()
    
    return render_template('admin.html', 
                          users=users, 
                          tasks=tasks,
                          total_messages=total_messages,
                          active_chats=active_chats)

# Панель управления пользователями
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin_users.html', users=users)

# Смена пароля пользователя администратором
@app.route('/admin/change_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_change_password(user_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Пароли не совпадают')
            return redirect(url_for('admin_change_password', user_id=user_id))
        
        if len(new_password) < 6:
            flash('Пароль должен содержать минимум 6 символов')
            return redirect(url_for('admin_change_password', user_id=user_id))
        
        user.set_password(new_password)
        db.session.commit()
        
        flash(f'Пароль для пользователя {user.username} успешно изменен')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_change_password.html', user=user)

# Страница управления задачами для администратора
@app.route('/admin/tasks')
@login_required
def admin_tasks():
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    users = User.query.all()
    
    return render_template('admin_tasks.html', tasks=tasks, users=users)

# Страница редактирования задачи
@app.route('/admin/tasks/<int:task_id>/edit')
@login_required
def admin_edit_task(task_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    
    task = Task.query.get_or_404(task_id)
    doctors = User.query.filter_by(role='doctor').all()
    physicists = User.query.filter_by(role='physicist').all()
    
    # Статистика чата
    chat_messages = ChatMessage.query.filter_by(task_id=task_id).all()
    chat_stats = {
        'total_messages': len(chat_messages),
        'doctor_messages': len([m for m in chat_messages if m.sender.role == 'doctor']),
        'physicist_messages': len([m for m in chat_messages if m.sender.role == 'physicist']),
        'last_message': max([m.created_at for m in chat_messages], default=None)
    }
    
    return render_template('admin_task_edit.html', 
                          task=task, 
                          doctors=doctors, 
                          physicists=physicists,
                          chat_stats=chat_stats)

# Обновление задачи администратором
@app.route('/admin/tasks/<int:task_id>/update', methods=['POST'])
@login_required
def admin_update_task(task_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    
    task = Task.query.get_or_404(task_id)
    
    task.title = request.form['title']
    task.description = request.form['description']
    task.status = request.form['status']
    task.priority = request.form['priority']
    task.doctor_id = request.form['doctor_id']
    task.physicist_id = request.form['physicist_id']
    task.updated_at = datetime.utcnow()
    
    # Если задача завершена, обновляем completed_at
    if task.status == 'completed' and not task.completed_at:
        task.completed_at = datetime.utcnow()
    elif task.status != 'completed':
        task.completed_at = None
    
    db.session.commit()
    flash('Задача успешно обновлена')
    return redirect(url_for('admin_tasks'))

# Удаление задачи
@app.route('/admin/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def admin_delete_task(task_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    
    flash('Задача успешно удалена')
    return redirect(url_for('admin_tasks'))

# API endpoint для получения всех пользователей
@app.route('/api/users')
@login_required
def api_get_users():
    users = User.query.all()
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'is_online': user.is_online(),
            'last_seen': user.last_seen.isoformat() if user.last_seen else None
        })
    
    return jsonify(users_data)

# API endpoint для обновления профиля пользователя
@app.route('/api/profile', methods=['PUT'])
@login_required
def api_update_profile():
    data = request.get_json()
    current_user.username = data.get('username', current_user.username)
    
    # Проверяем, что новый пароль задан и соответствует требованиям
    new_password = data.get('password')
    if new_password:
        if len(new_password) < 6:
            return jsonify({'error': 'Пароль должен содержать минимум 6 символов'}), 400
        current_user.set_password(new_password)
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Профиль успешно обновлен'})

# API endpoint для сброса пароля (только для администратора)
@app.route('/api/users/<int:user_id>/reset_password', methods=['POST'])
@login_required
def api_reset_password(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    new_password = data.get('new_password', '')
    
    if len(new_password) < 6:
        return jsonify({'error': 'Пароль должен содержать минимум 6 символов'}), 400
    
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Пароль для {user.username} успешно изменен'})

# API endpoint для получения статистики
@app.route('/api/stats')
@login_required
def api_get_stats():
    stats = {
        'total_users': User.query.count(),
        'total_tasks': Task.query.count(),
        'total_messages': ChatMessage.query.count(),
        'active_users_today': User.query.filter(
            User.last_seen >= datetime.utcnow().date()
        ).count()
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True)