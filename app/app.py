import os
import sys
import uuid
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

# Относительные импорты для работы как пакета
try:
    from .config import config
    from .models import db, User, Task, ChatMessage, TaskFile, TypingStatus, PersonalChat, PersonalMessage, PersonalChatFile
    from .forms.auth import LoginForm, RegistrationForm, PasswordChangeForm
    from .forms.task import TaskForm, TaskEditForm, CommentForm, MassActionForm
except ImportError:
    # Для прямого запуска (не как пакет)
    from config import config
    from models import db, User, Task, ChatMessage, TaskFile, TypingStatus, PersonalChat, PersonalMessage, PersonalChatFile
    from forms.auth import LoginForm, RegistrationForm, PasswordChangeForm
    from forms.task import TaskForm, TaskEditForm, CommentForm, MassActionForm


def create_app(config_name='development'):
    """Factory-функция создания Flask-приложения"""
    # Проверяем переменные окружения для путей (из GUI)
    templates_folder = os.environ.get('FLASK_TEMPLATES_FOLDER', 'templates')
    static_folder = os.environ.get('FLASK_STATIC_FOLDER', 'static')
    
    app = Flask(__name__, template_folder=templates_folder, static_folder=static_folder)
    app.config.from_object(config[config_name])

    # Маршрут для раздачи загруженных файлов из data/uploads/
    @app.route('/static/uploads/<path:filename>')
    def serve_uploaded_file(filename):
        # Путь к файлу в data/uploads/
        from pathlib import Path
        if getattr(sys, 'frozen', False):
            upload_base = Path(sys.executable).parent / 'data' / 'uploads'
        else:
            upload_base = Path(__file__).parent.parent / 'data' / 'uploads'

        return send_from_directory(str(upload_base), filename)

    # Настройка логирования
    from logging_config import get_logger
    try:
        logger = get_logger(log_dir=config.LOG_DIR if hasattr(config, 'LOG_DIR') else 'logs')
        app.logger.handlers = logger.logger.handlers
        app.logger.setLevel(logging.INFO)
    except Exception as e:
        print(f"Logging setup error: {e}")
        # Fallback к стандартному логированию
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)
        print('Flask app created')

    # Инициализация расширений
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Создание таблиц БД и пользователя admin по умолчанию
    with app.app_context():
        db.create_all()
        if not User.query.first():
            admin = User(username='admin', role='admin', first_name='Админ', last_name='Админов', department='ТП')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Создан пользователь admin / admin123")
    
    # ==================== УТИЛИТЫ ====================
    @app.context_processor
    def utility_processor():
        def moscow_time(dt):
            if dt is None:
                return None
            return dt + timedelta(hours=3)
        return dict(moscow_time=moscow_time)
    
    @app.before_request
    def before_request():
        if current_user.is_authenticated:
            current_user.update_last_seen()
    
    # ==================== АВТОРИЗАЦИЯ ====================
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
                next_page = request.args.get('next')
                app.logger.info(f'User {user.username} logged in', extra={'category': 'auth', 'user_id': user.id, 'username': user.username})
                flash('Вы успешно вошли в систему', 'success')
                return redirect(next_page if next_page else url_for('index'))
            else:
                app.logger.warning(f'Failed login attempt for {form.username.data}', extra={'category': 'auth', 'username': form.username.data})
                flash('Неверное имя пользователя или пароль', 'danger')

        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        username = current_user.username
        logout_user()
        app.logger.info(f'User {username} logged out', extra={'category': 'auth', 'username': username})
        flash('Вы вышли из системы', 'info')
        return redirect(url_for('login'))
    
    @app.route('/register', methods=['GET', 'POST'])
    @login_required
    def register():
        if current_user.role != 'admin':
            flash('Только администратор может регистрировать пользователей', 'danger')
            return redirect(url_for('index'))

        # Если запрос AJAX (из модального окна)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            role = request.form.get('role', 'doctor')
            first_name = request.form.get('first_name', 'Пользователь').strip() or 'Пользователь'
            last_name = request.form.get('last_name', '').strip() or 'Пользователь'
            middle_name = request.form.get('middle_name', '').strip()
            department = request.form.get('department', 'РО1').strip() or 'РО1'

            if not username or not password:
                return jsonify({'error': 'Заполните все поля', 'success': False}), 400

            if len(password) < 3:
                return jsonify({'error': 'Пароль должен быть не менее 3 символов', 'success': False}), 400

            if User.query.filter_by(username=username).first():
                return jsonify({'error': 'Пользователь с таким именем уже существует', 'success': False}), 400

            user = User(username=username, role=role, first_name=first_name, last_name=last_name, middle_name=middle_name, department=department)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': f'Пользователь {username} успешно зарегистрирован',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role
                }
            })

        # Обычный POST из формы
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                role=form.role.data,
                first_name='Пользователь',
                last_name='Пользователь',
                middle_name='',
                department='РО1'
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash(f'Пользователь {form.username.data} успешно зарегистрирован', 'success')
            return redirect(url_for('admin_users'))

        return render_template('register.html', form=form)
    
    # ==================== ГЛАВНАЯ СТРАНИЦА ====================
    @app.route('/')
    @login_required
    def index():
        form = TaskForm()

        if current_user.role == 'doctor':
            # Врачи видят только свои задачи
            tasks = Task.query.filter_by(doctor_id=current_user.id).order_by(Task.created_at.desc()).all()
        elif current_user.role == 'physicist':
            # Физики видят все задачи (убрали фильтрацию по physicist_id)
            tasks = Task.query.order_by(Task.created_at.desc()).all()
        else:
            # Админы видят все задачи
            tasks = Task.query.order_by(Task.created_at.desc()).all()

        return render_template('index.html', tasks=tasks, form=form)

    # ==================== ПОЛЬЗОВАТЕЛИ ОНЛАЙН ====================
    @app.route('/online_users')
    @login_required
    def online_users():
        """Страница с пользователями онлайн, сгруппированными по отделениям"""
        return render_template('online_users.html')

    # ==================== API ЗАДАЧ ====================
    @app.route('/api/tasks')
    @login_required
    def api_tasks():
        if current_user.role == 'doctor':
            # Врач видит только свои задачи
            tasks = Task.query.filter_by(doctor_id=current_user.id).order_by(Task.created_at.desc()).all()
        elif current_user.role == 'physicist':
            # Физик видит все задачи
            tasks = Task.query.order_by(Task.created_at.desc()).all()
        else:
            # Админ видит все задачи
            tasks = Task.query.order_by(Task.created_at.desc()).all()

        result = []
        active_chats_count = 0  # Считаем только задачи где пользователь является участником
        
        for task in tasks:
            unread_count = ChatMessage.query.filter_by(
                task_id=task.id,
                receiver_id=current_user.id,
                is_read=False
            ).count()

            # Проверяем, является ли пользователь участником этого чата
            # Участник чата = врач-создатель ИЛИ любой, кто писал сообщения в чат
            is_participant = False
            
            # Врач-создатель всегда участник
            if task.doctor_id == current_user.id:
                is_participant = True
            else:
                # Проверяем, писал ли пользователь сообщения в этот чат
                message_count = ChatMessage.query.filter_by(
                    task_id=task.id,
                    sender_id=current_user.id
                ).count()
                if message_count > 0:
                    is_participant = True
            
            # Считаем активный чат только если пользователь участник и задача не завершена/не отменена
            if is_participant and task.status not in ['completed', 'cancelled']:
                active_chats_count += 1

            result.append({
                'id': task.id,
                'title': task.title,
                'description': task.description or '',
                'status': task.status,
                'status_display': task.get_status_display(),
                'priority': task.priority,
                'priority_display': task.get_priority_display(),
                'doctor': task.doctor.get_full_name(),  # Краткое имя
                'doctor_full_name': task.doctor.get_full_name_with_dept(),  # Полное имя с отделением для title
                'created_at': (task.created_at + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M'),  # Формат даты как в оригинале
                'updated_at': (task.updated_at + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M') if task.updated_at else None,
                'unread_count': unread_count,
                # Файлы для отображения в карточке
                'files': [
                    {
                        'id': f.id,
                        'original_filename': f.original_filename,
                        'is_image': f.is_image,
                        'is_pdf': f.is_pdf,
                        'icon_class': f.get_icon_class(),
                        'download_url': f.download_url,
                        'view_url': f.view_url if (f.is_image or f.is_pdf) else None
                    }
                    for f in task.files
                ],
                # Все поля для real-time обновления (всё что редактируется в админке)
                'patient_card': task.patient_card,
                'aria_availability': task.aria_availability,
                'research_type': task.research_type,
                'expert_group': task.expert_group,
                'ct_diagnostic': task.ct_diagnostic,
                'treatment': task.treatment,
                'breath_control': task.breath_control,
                'mr_diagnostic': task.mr_diagnostic,
                'pet_diagnostic': task.pet_diagnostic
            })

        # Добавляем статистику по статусам
        stats = {
            'total': len(result),
            'pending': sum(1 for t in result if t['status'] == 'pending'),
            'in_progress': sum(1 for t in result if t['status'] == 'in_progress'),
            'completed': sum(1 for t in result if t['status'] == 'completed'),
            'cancelled': sum(1 for t in result if t['status'] == 'cancelled'),
            'active_chats': active_chats_count  # Активные чаты только где пользователь участник
        }

        return jsonify({'tasks': result, 'stats': stats})
    
    @app.route('/api/users/<role>')
    @login_required
    def api_users(role):
        users = User.query.filter_by(role=role).all()
        return jsonify([{
            'id': u.id,
            'username': u.username,
            'role': u.role,
            'is_online': u.is_online()
        } for u in users])

    @app.route('/api/users/all')
    @login_required
    def api_all_users():
        """Получить всех пользователей для выбора собеседника"""
        users = User.query.all()
        return jsonify([{
            'id': u.id,
            'username': u.username,
            'full_name': u.get_full_name_full(),
            'department': u.department,
            'role': u.get_role_display(),
            'is_online': u.is_online()
        } for u in users])

    @app.route('/api/online_users')
    @login_required
    def api_online_users():
        """Получить всех онлайн-пользователей, сгруппированных по отделениям"""
        all_users = User.query.all()

        # Группируем по отделениям
        departments = {}
        for user in all_users:
            if user.is_online():
                dept = user.department
                if dept not in departments:
                    departments[dept] = []
                departments[dept].append({
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.get_full_name_full(),
                    'role': user.get_role_display(),
                    'role_short': user.get_role_short(),
                    'department': user.department,
                    'last_seen': (user.last_seen + timedelta(hours=3)).strftime('%H:%M') if user.last_seen else ''
                })

        # Сортируем отделения по названию
        sorted_departments = dict(sorted(departments.items()))

        return jsonify(sorted_departments)

    @app.route('/api/stats')
    def api_stats():
        """Получить статистику системы для GUI лаунчера (публичный endpoint)"""
        from pathlib import Path
        
        # Пользователи
        users_total = User.query.count()
        users_online = sum(1 for u in User.query.all() if u.is_online())
        
        # Задачи по статусам
        tasks_total = Task.query.count()
        tasks_pending = Task.query.filter_by(status='pending').count()
        tasks_in_progress = Task.query.filter_by(status='in_progress').count()
        tasks_completed = Task.query.filter_by(status='completed').count()
        tasks_cancelled = Task.query.filter_by(status='cancelled').count()
        
        # Сообщения
        messages_total = ChatMessage.query.count()
        today = datetime.utcnow().date()
        messages_today = ChatMessage.query.filter(
            db.func.date(ChatMessage.created_at) == today
        ).count()
        
        # Файлы
        files_total = TaskFile.query.count()
        files_size = 0
        try:
            if getattr(sys, 'frozen', False):
                uploads_dir = Path(sys.executable).parent / 'data' / 'uploads'
            else:
                uploads_dir = Path(__file__).parent.parent / 'data' / 'uploads'
            
            if uploads_dir.exists():
                files_size = sum(f.stat().st_size for f in uploads_dir.rglob('*') if f.is_file())
        except:
            pass
        
        # Время работы сервера (с момента запуска процесса)
        import psutil
        try:
            process = psutil.Process(os.getpid())
            uptime = int(process.create_time())
            uptime = int(datetime.utcnow().timestamp() - uptime)
        except:
            uptime = 0
        
        return jsonify({
            'users': {
                'total': users_total,
                'online': users_online
            },
            'tasks': {
                'total': tasks_total,
                'pending': tasks_pending,
                'in_progress': tasks_in_progress,
                'completed': tasks_completed,
                'cancelled': tasks_cancelled
            },
            'messages': {
                'total': messages_total,
                'today': messages_today
            },
            'files': {
                'total': files_total,
                'size_bytes': files_size
            },
            'uptime': uptime
        })


    @app.route('/api/task/<int:task_id>')
    @login_required
    def api_task(task_id):
        task = Task.query.get_or_404(task_id)

        # Проверяем доступ к задаче
        # Доступ имеют: врач-создатель, любой физик, админ
        if current_user.role == 'doctor' and current_user.id != task.doctor_id:
            return jsonify({'error': 'Нет доступа'}), 403

        # Считаем сообщения
        messages_count = ChatMessage.query.filter_by(task_id=task.id).count()

        # Получаем участников - всех, кто писал в этом чате + врач-создатель
        # Получаем уникальных user_id из сообщений (sender_id и receiver_id)
        user_ids = set()
        user_ids.add(task.doctor_id)  # Всегда добавляем врача-создателя

        # Добавляем всех отправителей сообщений
        sender_ids = db.session.query(ChatMessage.sender_id).filter_by(task_id=task.id).distinct().all()
        for (sid,) in sender_ids:
            user_ids.add(sid)

        # Получаем пользователей
        participants_users = User.query.filter(User.id.in_(user_ids)).all()

        # Сортируем: сначала врач, потом остальные по имени
        participants = []
        doctor = None
        others = []

        for user in participants_users:
            if user.id == task.doctor_id:
                doctor = {
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.get_full_name_full(),
                    'full_name_with_dept': user.get_full_name_with_dept(),
                    'role': user.get_role_display(),
                    'is_online': user.is_online()
                }
            else:
                others.append({
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.get_full_name_full(),
                    'full_name_with_dept': user.get_full_name_with_dept(),
                    'role': user.get_role_display(),
                    'is_online': user.is_online()
                })

        # Сортируем остальных по имени
        others.sort(key=lambda x: x['full_name'])

        if doctor:
            participants.append(doctor)
        participants.extend(others)

        return jsonify({
            'id': task.id,
            'title': task.title,
            'status': task.status,
            'status_display': task.get_status_display(),
            'priority': task.priority,
            'updated_at': (task.updated_at + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M') if task.updated_at else None,
            'completed_at': (task.completed_at + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M') if task.completed_at else None,
            'messages_count': messages_count,
            'participants': participants,
            # Поля исследования для real-time обновления
            'patient_card': task.patient_card,
            'research_type': task.research_type,
            'expert_group': task.expert_group,
            'ct_diagnostic': task.ct_diagnostic,
            'treatment': task.treatment,
            'breath_control': task.breath_control,
            'mr_diagnostic': task.mr_diagnostic,
            'pet_diagnostic': task.pet_diagnostic
        })

    @app.route('/admin/api/task/<int:task_id>')
    @login_required
    def admin_api_task(task_id):
        if current_user.role != 'admin':
            return jsonify({'error': 'Доступ запрещен'}), 403

        task = Task.query.get_or_404(task_id)

        # Считаем сообщения
        messages_count = ChatMessage.query.filter_by(task_id=task.id).count()

        return jsonify({
            'id': task.id,
            'title': task.title,
            'status': task.status,
            'status_display': task.get_status_display(),
            'updated_at': (task.updated_at + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M') if task.updated_at else None,
            'completed_at': (task.completed_at + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M') if task.completed_at else None,
            'messages_count': messages_count,
            # Поля исследования для real-time обновления
            'patient_card': task.patient_card,
            'research_type': task.research_type,
            'expert_group': task.expert_group,
            'ct_diagnostic': task.ct_diagnostic,
            'treatment': task.treatment,
            'mr_diagnostic': task.mr_diagnostic,
            'pet_diagnostic': task.pet_diagnostic
        })
    
    @app.route('/create_task', methods=['POST'])
    @login_required
    def create_task():
        if current_user.role != 'doctor':
            flash('Только врачи могут создавать задачи', 'danger')
            return redirect(url_for('index'))

        # Получаем данные из формы (новые поля из оригинала)
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        study_type = request.form.get('study_type', '').strip()
        patient_card = request.form.get('patient_card', '').strip()
        aria_availability = request.form.get('aria_availability', '').strip() or None

        # Поля для CT
        ct_building = request.form.get('ct_building', '').strip()
        ct_equipment = request.form.get('ct_equipment', '').strip()
        treatment_building = request.form.get('treatment_building', '').strip()
        treatment_device = request.form.get('treatment_device', '').strip()
        breath_control = request.form.get('breath_control', '').strip()
        
        # Формируем ct_diagnostic и treatment из новых полей
        ct_diagnostic = f"{ct_equipment} ({ct_building})" if ct_equipment and ct_building else ''
        
        # Формируем treatment БЕЗ контроля по дыханию (он отображается отдельным полем)
        treatment = f"{treatment_device} ({treatment_building})" if treatment_device and treatment_building else ''
        
        # Сохраняем контроль по дыханию отдельно
        saved_breath_control = breath_control if breath_control and breath_control != 'no' else None

        # Проверка обязательных полей
        if not patient_card or not study_type:
            flash('Заполните обязательные поля (номер карты пациента и тип исследования)', 'danger')
            return redirect(url_for('index'))

        # Автоматическое название если не заполнено
        if not title:
            title = 'Задача'  # ID добавится после создания

        # Создаем задачу
        task = Task(
            title=title,
            description=description,
            research_type=study_type,
            patient_card=patient_card,
            aria_availability=aria_availability,
            ct_diagnostic=ct_diagnostic,
            treatment=treatment,
            breath_control=saved_breath_control,
            doctor_id=current_user.id,
            physicist_id=1  # Назначаем первого физика по умолчанию (задачу видят все физики)
        )
        db.session.add(task)
        db.session.flush()  # Получаем ID задачи
        
        # Явно устанавливаем updated_at при создании
        task.updated_at = datetime.utcnow()

        # Обновляем название с ID если оно было автоматическим
        if not request.form.get('title', '').strip():
            task.title = f'Задача #{task.id}'

        # Обработка загруженных файлов
        if 'files' in request.files:
            upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(task.id))
            os.makedirs(upload_dir, exist_ok=True)
            
            for file in request.files.getlist('files'):
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    if filename:
                        import uuid
                        unique_filename = f"{uuid.uuid4().hex}_{filename}"
                        file_path = os.path.join(upload_dir, unique_filename)
                        
                        try:
                            file.save(file_path)
                            file_size = os.path.getsize(file_path)
                            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                            
                            task_file = TaskFile(
                                task_id=task.id,
                                uploader_id=current_user.id,
                                original_filename=filename,
                                stored_filename=unique_filename,
                                file_size=file_size,
                                is_image=ext in app.config['ALLOWED_IMAGE_EXTENSIONS'],
                                is_pdf=ext in app.config['ALLOWED_PDF_EXTENSIONS'],
                                is_dicom=ext in app.config['ALLOWED_DICOM_EXTENSIONS'],
                                is_archive=ext in app.config['ALLOWED_ARCHIVE_EXTENSIONS']
                            )
                            db.session.add(task_file)
                        except Exception as e:
                            print(f"Error uploading file {filename}: {e}")

        db.session.commit()
        app.logger.info(f'Task #{task.id} created by {current_user.username}', extra={'category': 'tasks', 'task_id': task.id, 'user_id': current_user.id, 'username': current_user.username})
        flash('Задача успешно создана', 'success')
        return redirect(url_for('index'))
    
    @app.route('/update_task/<int:id>', methods=['POST'])
    @login_required
    def update_task(id):
        task = Task.query.get_or_404(id)
        
        if current_user.role not in ['physicist', 'admin']:
            flash('У вас нет прав для обновления этой задачи', 'danger')
            return redirect(url_for('index'))
        
        new_status = request.form.get('status')
        if new_status:
            task.status = new_status
            if new_status == 'completed':
                task.completed_at = datetime.utcnow()
            else:
                task.completed_at = None
            task.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Статус задачи обновлен', 'success')
        
        return redirect(url_for('index'))
    
    # ==================== ЧАТ ====================
    @app.route('/task/<int:id>/chat')
    @login_required
    def chat(id):
        task = Task.query.get_or_404(id)

        # Проверяем доступ: врач-создатель, любой физик или админ
        if current_user.role == 'admin':
            pass  # Админ имеет доступ ко всем задачам
        elif current_user.role == 'doctor':
            # Врач имеет доступ только к своим задачам
            if current_user.id != task.doctor_id:
                flash('У вас нет доступа к чату этой задачи', 'danger')
                return redirect(url_for('index'))
        elif current_user.role == 'physicist':
            # Физик имеет доступ ко всем задачам
            pass
        else:
            flash('У вас нет доступа к чату этой задачи', 'danger')
            return redirect(url_for('index'))

        # Определяем собеседника (для отображения в чате)
        if current_user.id == task.doctor_id:
            # Если врач - показываем любого физика (первого из базы)
            chat_partner = User.query.filter_by(role='physicist').first()
            if not chat_partner:
                chat_partner = task.physicist  # fallback
        else:
            # Если физик - показываем врача-создателя
            chat_partner = task.doctor

        messages = ChatMessage.query.filter_by(task_id=id).order_by(ChatMessage.created_at).all()

        # Помечаем сообщения как прочитанные
        for msg in messages:
            if msg.receiver_id == current_user.id and not msg.is_read:
                msg.is_read = True
        db.session.commit()

        return render_template('chat.html', task=task, chat_partner=chat_partner, messages=messages)
    
    @app.route('/task/<int:id>/get_messages')
    @login_required
    def get_messages(id):
        task = Task.query.get_or_404(id)
        last_id = request.args.get('last_id', 0, type=int)
        
        messages = ChatMessage.query.filter(
            ChatMessage.task_id == id,
            ChatMessage.id > last_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        # Помечаем сообщения как прочитанные
        for msg in messages:
            if msg.receiver_id == current_user.id:
                msg.is_read = True
        db.session.commit()
        
        return jsonify([{
            'id': m.id,
            'content': m.content,
            'sender_id': m.sender_id,
            'sender_name': m.sender.username,
            'created_at': (m.created_at + timedelta(hours=3)).strftime('%H:%M'),
            'created_at_iso': (m.created_at + timedelta(hours=3)).isoformat(),
            'is_read': m.is_read
        } for m in messages])
    
    @app.route('/task/<int:id>/send_message', methods=['POST'])
    @login_required
    def send_message(id):
        task = Task.query.get_or_404(id)
        data = request.get_json()
        content = data.get('content', '').strip()

        if not content:
            return jsonify({'error': 'Пустое сообщение', 'success': False}), 400

        # Проверяем доступ к задаче
        # Врач может писать только в свои задачи
        if current_user.role == 'doctor' and current_user.id != task.doctor_id:
            return jsonify({'error': 'Нет доступа', 'success': False}), 403

        # Определяем получателя
        if current_user.role == 'admin':
            # Админ может писать в любой чат - получает врач
            receiver_id = task.doctor_id
        elif current_user.role == 'physicist':
            # Физик может отправлять сообщения во все задачи
            # Получатель - врач-создатель
            receiver_id = task.doctor_id
        elif current_user.id == task.doctor_id:
            # Врач отправляет - получают все физики
            # Для совместимости указываем первого физика
            physicist = User.query.filter_by(role='physicist').first()
            receiver_id = physicist.id if physicist else task.physicist_id
        else:
            return jsonify({'error': 'Нет доступа', 'success': False}), 403

        message = ChatMessage(
            content=content,
            task_id=id,
            sender_id=current_user.id,
            receiver_id=receiver_id
        )
        db.session.add(message)
        
        # Обновляем updated_at задачи при отправке сообщения
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        app.logger.info(f'Message sent in task #{id} by {current_user.username}', extra={'category': 'chat', 'task_id': id, 'user_id': current_user.id, 'username': current_user.username})

        return jsonify({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender_id': current_user.id,
                'created_at': (message.created_at + timedelta(hours=3)).isoformat()
            }
        })
    
    @app.route('/unread_messages')
    @login_required
    def unread_messages():
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
            
            last_message = ChatMessage.query.filter_by(task_id=task.id).order_by(ChatMessage.created_at.desc()).first()
            
            result.append({
                'task_id': task.id,
                'task_title': task.title,
                'unread_count': unread_count,
                'last_sender': last_message.sender.username if last_message else None
            })
        
        total_unread = sum(item['unread_count'] for item in result)
        
        return jsonify({
            'tasks_with_unread': result,
            'total_unread': total_unread
        })
    
    # ==================== СТАТУС "ПЕЧАТАЕТ" ====================
    @app.route('/task/<int:id>/typing', methods=['POST'])
    @login_required
    def set_typing(id):
        data = request.get_json() or {}
        
        status = TypingStatus.query.filter_by(task_id=id, user_id=current_user.id).first()
        if not status:
            status = TypingStatus(
                task_id=id,
                user_id=current_user.id,
                is_typing=data.get('is_typing', True)
            )
            db.session.add(status)
        else:
            status.is_typing = data.get('is_typing', True)
            status.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True})
    
    @app.route('/task/<int:id>/typing_status')
    @login_required
    def get_typing_status(id):
        task = Task.query.get(id)
        if not task:
            return jsonify({'is_typing': False, 'username': None})

        # Получаем всех пользователей, которые могут участвовать в чате задачи
        # Врач-создатель + все физики + все админы (так как все они имеют доступ к задачам)
        participant_ids = {task.doctor_id}
        physicists = User.query.filter_by(role='physicist').all()
        for p in physicists:
            participant_ids.add(p.id)
        admins = User.query.filter_by(role='admin').all()
        for a in admins:
            participant_ids.add(a.id)

        # Исключаем текущего пользователя
        participant_ids.discard(current_user.id)

        # Ищем всех, кто печатает в этой задаче
        typing_statuses = TypingStatus.query.filter(
            TypingStatus.task_id == id,
            TypingStatus.user_id.in_(participant_ids),
            TypingStatus.is_typing == True
        ).all()

        is_typing = False
        username = None

        for status in typing_statuses:
            # Проверяем не истекло ли время (5 секунд)
            if datetime.utcnow() - status.updated_at < timedelta(seconds=5):
                is_typing = True
                typing_user = User.query.get(status.user_id)
                username = typing_user.username if typing_user else None
                break  # Показываем первого, кто печатает
            else:
                # Сбрасываем истёкший статус
                status.is_typing = False
                db.session.commit()

        return jsonify({'is_typing': is_typing, 'username': username})

    # ==================== ЛИЧНЫЕ ЧАТЫ ====================
    @app.route('/chats')
    @login_required
    def chats_list():
        """Список личных чатов пользователя"""
        from datetime import timezone
        
        user_chats = PersonalChat.query.filter(
            (PersonalChat.user1_id == current_user.id) | 
            (PersonalChat.user2_id == current_user.id)
        ).order_by(PersonalChat.updated_at.desc()).all()
        
        chats_data = []
        for chat in user_chats:
            partner_id = chat.user2_id if chat.user1_id == current_user.id else chat.user1_id
            partner = User.query.get(partner_id)
            
            unread_count = PersonalMessage.query.filter_by(
                chat_id=chat.id,
                is_read=False
            ).filter(PersonalMessage.sender_id != current_user.id).count()
            
            last_message = PersonalMessage.query.filter_by(
                chat_id=chat.id
            ).order_by(PersonalMessage.created_at.desc()).first()
            
            # Определяем тип последнего сообщения
            last_message_content = None
            last_message_is_file = False
            last_message_file_type = 'other'
            last_message_date = None
            last_message_time = None
            
            if last_message:
                # Конвертируем время в МСК (UTC+3)
                moscow_time = last_message.created_at + timedelta(hours=3)
                last_message_date = moscow_time.strftime('%d.%m')
                last_message_time = moscow_time.strftime('%H:%M')
                
                if last_message.files:
                    last_message_is_file = True
                    file = last_message.files[0]
                    if file.is_image:
                        last_message_file_type = 'image'
                        last_message_content = f"Изображение: {file.original_filename}"
                    elif file.is_pdf:
                        last_message_file_type = 'pdf'
                        last_message_content = f"PDF: {file.original_filename}"
                    elif file.is_archive:
                        last_message_file_type = 'archive'
                        last_message_content = f"Архив: {file.original_filename}"
                    else:
                        last_message_file_type = 'other'
                        last_message_content = f"Файл: {file.original_filename}"
                else:
                    last_message_content = last_message.content
            
            # Сокращённое имя для мобильных (Фамилия И.О.)
            partner_full_name_short = partner.get_full_name()
            
            chats_data.append({
                'chat_id': chat.id,
                'partner_id': partner.id,
                'partner_username': partner.username,
                'partner_full_name': partner.get_full_name_full(),
                'partner_full_name_short': partner_full_name_short,
                'partner_role': partner.get_role_display(),
                'partner_department': partner.department,
                'partner_is_online': partner.is_online(),
                'unread_count': unread_count,
                'last_message_content': last_message_content,
                'last_message_is_file': last_message_is_file,
                'last_message_file_type': last_message_file_type,
                'last_message_date': last_message_date,
                'last_message_time': last_message_time
            })
        
        return render_template('chats_list.html', chats=chats_data)
    
    @app.route('/chat/<int:chat_id>')
    @login_required
    def personal_chat(chat_id):
        """Страница личного чата"""
        chat = PersonalChat.query.get_or_404(chat_id)
        
        # Проверяем, что пользователь участвует в чате
        if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
            flash('У вас нет доступа к этому чату', 'danger')
            return redirect(url_for('chats_list'))
        
        # Определяем собеседника
        partner_id = chat.user2_id if chat.user1_id == current_user.id else chat.user1_id
        partner = User.query.get(partner_id)
        
        messages = PersonalMessage.query.filter_by(chat_id=chat_id).order_by(PersonalMessage.created_at).all()
        
        # Помечаем сообщения как прочитанные
        for msg in messages:
            if msg.sender_id != current_user.id and not msg.is_read:
                msg.is_read = True
        db.session.commit()
        
        return render_template('personal_chat.html', chat=chat, partner=partner, messages=messages)
    
    @app.route('/chat/start/<int:user_id>', methods=['POST'])
    @login_required
    def start_chat(user_id):
        """Начать чат с пользователем или получить существующий"""
        if user_id == current_user.id:
            return jsonify({'error': 'Нельзя начать чат с самим собой'}), 400
        
        partner = User.query.get_or_404(user_id)
        
        # Ищем существующий чат
        existing_chat = PersonalChat.query.filter(
            ((PersonalChat.user1_id == current_user.id) & (PersonalChat.user2_id == user_id)) |
            ((PersonalChat.user1_id == user_id) & (PersonalChat.user2_id == current_user.id))
        ).first()
        
        if existing_chat:
            return jsonify({'chat_id': existing_chat.id, 'created': False})
        
        # Создаём новый чат
        new_chat = PersonalChat(
            user1_id=min(current_user.id, user_id),
            user2_id=max(current_user.id, user_id)
        )
        db.session.add(new_chat)
        db.session.commit()
        
        return jsonify({'chat_id': new_chat.id, 'created': True})

    @app.route('/chat/<int:chat_id>/upload_file', methods=['POST'])
    @login_required
    def upload_personal_file(chat_id):
        """Загрузить файл в личный чат"""
        try:
            chat = PersonalChat.query.get_or_404(chat_id)

            if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
                return jsonify({'error': 'Нет доступа'}), 403

            if 'file' not in request.files:
                return jsonify({'error': 'Нет файла'}), 400

            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'Пустой файл'}), 400

            # Сохраняем файл
            original_filename = secure_filename(file.filename)
            stored_filename = f"{uuid.uuid4().hex}_{original_filename}"
            upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'personal_chats')
            
            # Создаём директорию
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, stored_filename)

            file.save(file_path)

            # Получаем размер и тип файла
            file_size = os.path.getsize(file_path)
            mime_type = file.content_type

            # Создаём запись о файле
            chat_file = PersonalChatFile(
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_size=file_size,
                mime_type=mime_type,
                is_image=mime_type.startswith('image/') if mime_type else original_filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
            )
            db.session.add(chat_file)
            db.session.commit()

            return jsonify({
                'success': True,
                'file': {
                    'id': chat_file.id,
                    'original_filename': chat_file.original_filename,
                    'file_size_mb': chat_file.file_size_mb,
                    'is_image': chat_file.is_image,
                    'url': f'/chat/{chat_id}/files/{chat_file.id}/download'
                }
            })
        except Exception as e:
            print(f"Upload error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/chat/<int:chat_id>/files/<int:file_id>/download')
    @login_required
    def download_personal_file(chat_id, file_id):
        """Скачать файл из личного чата"""
        chat = PersonalChat.query.get_or_404(chat_id)
        
        if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
            flash('Нет доступа', 'danger')
            return redirect(url_for('chats_list'))
        
        chat_file = PersonalChatFile.query.get_or_404(file_id)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'personal_chats', chat_file.stored_filename)
        
        return send_from_directory(
            os.path.dirname(file_path),
            os.path.basename(file_path),
            as_attachment=True,
            download_name=chat_file.original_filename
        )
    
    @app.route('/chat/<int:chat_id>/files/<int:file_id>/view')
    @login_required
    def view_personal_file(chat_id, file_id):
        """Просмотреть файл (для изображений)"""
        chat = PersonalChat.query.get_or_404(chat_id)
        
        if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
            flash('Нет доступа', 'danger')
            return redirect(url_for('chats_list'))
        
        chat_file = PersonalChatFile.query.get_or_404(file_id)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'personal_chats', chat_file.stored_filename)
        
        return send_from_directory(
            os.path.dirname(file_path),
            os.path.basename(file_path)
        )

    @app.route('/chat/<int:chat_id>/send_message', methods=['POST'])
    @login_required
    def send_personal_message(chat_id):
        """Отправить сообщение в личный чат (с поддержкой файлов)"""
        chat = PersonalChat.query.get_or_404(chat_id)

        # Проверяем участие в чате
        if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
            return jsonify({'error': 'Нет доступа'}), 403

        data = request.get_json()
        content = data.get('content', '').strip()
        file_ids = data.get('file_ids', [])

        if not content and not file_ids:
            return jsonify({'error': 'Пустое сообщение'}), 400

        message = PersonalMessage(
            chat_id=chat_id,
            sender_id=current_user.id,
            content=content
        )
        db.session.add(message)

        # Привязываем файлы к сообщению
        for file_id in file_ids:
            chat_file = PersonalChatFile.query.get(file_id)
            if chat_file:
                chat_file.message_id = message.id
        
        # Обновляем время чата
        chat.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender_id': message.sender_id,
                'created_at_iso': (message.created_at + timedelta(hours=3)).isoformat(),
                'files': [
                    {
                        'id': f.id,
                        'original_filename': f.original_filename,
                        'file_size_mb': f.file_size_mb,
                        'is_image': f.is_image,
                        'url': f'/chat/{chat_id}/files/{f.id}/view' if f.is_image else f'/chat/{chat_id}/files/{f.id}/download'
                    }
                    for f in message.files
                ]
            }
        })
    
    @app.route('/chat/<int:chat_id>/get_messages')
    @login_required
    def get_personal_messages(chat_id):
        """Получить новые сообщения"""
        chat = PersonalChat.query.get_or_404(chat_id)

        # Проверяем участие
        if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
            return jsonify({'error': 'Нет доступа'}), 403

        last_id = request.args.get('last_id', 0, type=int)

        messages = PersonalMessage.query.filter_by(
            chat_id=chat_id
        ).filter(
            PersonalMessage.id > last_id
        ).order_by(PersonalMessage.created_at).all()

        result = []
        for msg in messages:
            # Помечаем сообщения как прочитанные, если они адресованы текущему пользователю
            if msg.sender_id != current_user.id and not msg.is_read:
                msg.is_read = True
            
            result.append({
                'id': msg.id,
                'content': msg.content,
                'sender_id': msg.sender_id,
                'is_read': msg.is_read,
                'created_at_iso': (msg.created_at + timedelta(hours=3)).isoformat(),
                'files': [
                    {
                        'id': f.id,
                        'original_filename': f.original_filename,
                        'file_size_mb': f.file_size_mb,
                        'is_image': f.is_image,
                        'url': f'/chat/{chat_id}/files/{f.id}/view' if f.is_image else f'/chat/{chat_id}/files/{f.id}/download'
                    }
                    for f in msg.files
                ]
            })

        db.session.commit()
        return jsonify(result)
    
    @app.route('/chat/<int:chat_id>/typing', methods=['POST'])
    @login_required
    def personal_chat_typing(chat_id):
        """Статус 'печатает' для личного чата"""
        data = request.get_json() or {}

        chat = PersonalChat.query.get_or_404(chat_id)

        # Проверяем доступ к чату
        if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
            return jsonify({'error': 'Нет доступа', 'success': False}), 403

        status = TypingStatus.query.filter_by(chat_id=chat_id, user_id=current_user.id).first()
        if not status:
            status = TypingStatus(
                chat_id=chat_id,
                user_id=current_user.id,
                is_typing=data.get('is_typing', True)
            )
            db.session.add(status)
        else:
            status.is_typing = data.get('is_typing', True)
            status.updated_at = datetime.utcnow()

        db.session.commit()
        return jsonify({'success': True})

    @app.route('/chat/<int:chat_id>/typing_status')
    @login_required
    def get_personal_typing_status(chat_id):
        """Получить статус 'печатает' для личного чата"""
        chat = PersonalChat.query.get_or_404(chat_id)

        # Проверяем доступ к чату
        if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
            return jsonify({'is_typing': False, 'username': None})

        # Определяем ID собеседника
        partner_id = chat.user2_id if chat.user1_id == current_user.id else chat.user1_id

        status = TypingStatus.query.filter_by(chat_id=chat_id, user_id=partner_id).first()
        is_typing = False
        username = None

        if status and status.is_typing:
            # Проверяем не истекло ли время (5 секунд)
            if datetime.utcnow() - status.updated_at < timedelta(seconds=5):
                is_typing = True
                partner = User.query.get(partner_id)
                username = partner.username if partner else None
            else:
                status.is_typing = False
                db.session.commit()

        return jsonify({'is_typing': is_typing, 'username': username})

    @app.route('/chat/<int:chat_id>/mark_read/<int:message_id>', methods=['POST'])
    @login_required
    def mark_personal_message_read(chat_id, message_id):
        """Отметить сообщение как прочитанное"""
        chat = PersonalChat.query.get_or_404(chat_id)
        
        if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
            return jsonify({'error': 'Нет доступа'}), 403
        
        message = PersonalMessage.query.get_or_404(message_id)
        if message.sender_id != current_user.id:
            message.is_read = True
            db.session.commit()
        
        return jsonify({'success': True, 'is_read': True})
    
    @app.route('/chat/<int:chat_id>/mark_all_read', methods=['POST'])
    @login_required
    def mark_all_personal_messages_read(chat_id):
        """Отметить все сообщения в чате как прочитанные"""
        chat = PersonalChat.query.get_or_404(chat_id)
        
        if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
            return jsonify({'error': 'Нет доступа'}), 403
        
        # Помечаем все непрочитанные сообщения от другого пользователя как прочитанные
        messages = PersonalMessage.query.filter_by(
            chat_id=chat_id,
            is_read=False
        ).filter(PersonalMessage.sender_id != current_user.id).all()
        
        for msg in messages:
            msg.is_read = True
        
        db.session.commit()
        return jsonify({'success': True, 'marked_count': len(messages)})
    
    @app.route('/chat/<int:chat_id>/get_message_status/<int:message_id>')
    @login_required
    def get_personal_message_status(chat_id, message_id):
        """Получить статус прочтения сообщения"""
        chat = PersonalChat.query.get_or_404(chat_id)
        
        if chat.user1_id != current_user.id and chat.user2_id != current_user.id:
            return jsonify({'error': 'Нет доступа'}), 403
        
        message = PersonalMessage.query.get_or_404(message_id)
        return jsonify({'is_read': message.is_read})
    
    @app.route('/api/chat/partner/<int:user_id>')
    @login_required
    def get_chat_with_partner(user_id):
        """Получить ID чата с пользователем или создать новый"""
        if user_id == current_user.id:
            return jsonify({'error': 'Нельзя начать чат с самим собой'}), 400

        partner = User.query.get_or_404(user_id)

        existing_chat = PersonalChat.query.filter(
            ((PersonalChat.user1_id == current_user.id) & (PersonalChat.user2_id == user_id)) |
            ((PersonalChat.user1_id == user_id) & (PersonalChat.user2_id == current_user.id))
        ).first()

        if existing_chat:
            return jsonify({'chat_id': existing_chat.id, 'exists': True})

        return jsonify({'chat_id': None, 'exists': False})

    @app.route('/api/personal_chats/unread_count')
    @login_required
    def get_personal_chats_unread_count():
        """Получить количество непрочитанных личных сообщений"""
        # Получаем все чаты пользователя
        user_chats = PersonalChat.query.filter(
            (PersonalChat.user1_id == current_user.id) | 
            (PersonalChat.user2_id == current_user.id)
        ).all()
        
        chat_ids = [chat.id for chat in user_chats]
        
        if not chat_ids:
            return jsonify({'total_unread': 0})
        
        # Считаем непрочитанные сообщения от других пользователей
        total_unread = PersonalMessage.query.filter(
            PersonalMessage.chat_id.in_(chat_ids),
            PersonalMessage.sender_id != current_user.id,
            PersonalMessage.is_read == False
        ).count()
        
        return jsonify({'total_unread': total_unread})

    @app.route('/api/chats/list')
    @login_required
    def api_chats_list():
        """Получить список чатов для real-time обновления"""
        user_chats = PersonalChat.query.filter(
            (PersonalChat.user1_id == current_user.id) | 
            (PersonalChat.user2_id == current_user.id)
        ).order_by(PersonalChat.updated_at.desc()).all()
        
        chats_data = []
        for chat in user_chats:
            partner_id = chat.user2_id if chat.user1_id == current_user.id else chat.user1_id
            partner = User.query.get(partner_id)
            
            unread_count = PersonalMessage.query.filter_by(
                chat_id=chat.id,
                is_read=False
            ).filter(PersonalMessage.sender_id != current_user.id).count()
            
            last_message = PersonalMessage.query.filter_by(
                chat_id=chat.id
            ).order_by(PersonalMessage.created_at.desc()).first()
            
            # Определяем тип последнего сообщения
            last_message_content = None
            last_message_is_file = False
            last_message_file_type = 'other'
            last_message_date = None
            last_message_time = None
            
            if last_message:
                # Конвертируем время в МСК (UTC+3)
                moscow_time = last_message.created_at + timedelta(hours=3)
                last_message_date = moscow_time.strftime('%d.%m')
                last_message_time = moscow_time.strftime('%H:%M')
                
                if last_message.files:
                    last_message_is_file = True
                    file = last_message.files[0]
                    if file.is_image:
                        last_message_file_type = 'image'
                        last_message_content = f"Изображение: {file.original_filename}"
                    elif file.is_pdf:
                        last_message_file_type = 'pdf'
                        last_message_content = f"PDF: {file.original_filename}"
                    elif file.is_archive:
                        last_message_file_type = 'archive'
                        last_message_content = f"Архив: {file.original_filename}"
                    else:
                        last_message_file_type = 'other'
                        last_message_content = f"Файл: {file.original_filename}"
                else:
                    last_message_content = last_message.content
            
            chats_data.append({
                'chat_id': chat.id,
                'partner_id': partner.id,
                'partner_is_online': partner.is_online(),
                'unread_count': unread_count,
                'last_message_content': last_message_content,
                'last_message_is_file': last_message_is_file,
                'last_message_file_type': last_message_file_type,
                'last_message_date': last_message_date,
                'last_message_time': last_message_time
            })
        
        return jsonify(chats_data)

    # ==================== ФАЙЛЫ ====================
    @app.route('/task/<int:id>/files')
    @login_required
    def get_files(id):
        task = Task.query.get_or_404(id)
        files = TaskFile.query.filter_by(task_id=id).all()
        
        result = []
        for f in files:
            result.append({
                'id': f.id,
                'original_filename': f.original_filename,
                'file_size_mb': f.file_size_mb,
                'uploaded_at': f.uploaded_at.strftime('%Y-%m-%d %H:%M'),
                'uploader_name': f.uploader.username,
                'uploader_id': f.uploader_id,
                'is_image': f.is_image,
                'is_pdf': f.is_pdf,
                'download_url': f.download_url,
                'view_url': f.view_url,
                'icon_class': f.get_icon_class()
            })
        
        # Статистика
        stats = {
            'images': sum(1 for f in files if f.is_image),
            'pdfs': sum(1 for f in files if f.is_pdf),
            'dicom': sum(1 for f in files if f.is_dicom),
            'archives': sum(1 for f in files if f.is_archive),
            'other': sum(1 for f in files if not any([f.is_image, f.is_pdf, f.is_dicom, f.is_archive]))
        }
        
        return jsonify({
            'files': result,
            'stats': stats,
            'task_title': task.title
        })
    
    @app.route('/task/<int:id>/files/<int:file_id>/download')
    @login_required
    def download_file(id, file_id):
        file = TaskFile.query.get_or_404(file_id)
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(id))
        return send_from_directory(
            upload_dir,
            file.stored_filename,
            as_attachment=True,
            download_name=file.original_filename
        )
    
    @app.route('/task/<int:id>/files/<int:file_id>/view')
    @login_required
    def view_file(id, file_id):
        file = TaskFile.query.get_or_404(file_id)
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(id))
        return send_from_directory(upload_dir, file.stored_filename)
    
    @app.route('/task/<int:id>/files/<int:file_id>', methods=['DELETE'])
    @login_required
    def delete_file(id, file_id):
        file = TaskFile.query.get_or_404(file_id)
        
        if file.task_id != id:
            return jsonify({'error': 'Файл не принадлежит задаче', 'success': False}), 400
        
        # Проверяем права на удаление
        if current_user.role != 'admin' and file.uploader_id != current_user.id:
            return jsonify({'error': 'Нет прав на удаление', 'success': False}), 403
        
        # Удаляем файл с диска
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(id), file.stored_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        db.session.delete(file)
        db.session.commit()
        
        return jsonify({'success': True})
    
    @app.route('/task/<int:id>/add_files', methods=['POST'])
    @login_required
    def add_files(id):
        task = Task.query.get_or_404(id)

        if 'files' not in request.files:
            return jsonify({'error': 'Нет файлов', 'success': False}), 400

        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(id))
        os.makedirs(upload_dir, exist_ok=True)

        uploaded = []
        errors = []

        for file in request.files.getlist('files'):
            if file.filename == '':
                continue

            filename = secure_filename(file.filename)
            if not filename:
                errors.append(f'Недопустимое имя файла')
                continue

            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(upload_dir, unique_filename)

            try:
                file.save(file_path)
                file_size = os.path.getsize(file_path)
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

                task_file = TaskFile(
                    task_id=id,
                    uploader_id=current_user.id,
                    original_filename=filename,
                    stored_filename=unique_filename,
                    file_size=file_size,
                    is_image=ext in app.config['ALLOWED_IMAGE_EXTENSIONS'],
                    is_pdf=ext in app.config['ALLOWED_PDF_EXTENSIONS'],
                    is_dicom=ext in app.config['ALLOWED_DICOM_EXTENSIONS'],
                    is_archive=ext in app.config['ALLOWED_ARCHIVE_EXTENSIONS']
                )
                db.session.add(task_file)
                uploaded.append({'id': task_file.id, 'filename': filename})
            except Exception as e:
                errors.append(f'Ошибка загрузки {filename}: {str(e)}')

        # Обновляем updated_at задачи при добавлении файла
        task.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': len(errors) == 0,
            'uploaded_files': uploaded,
            'errors': errors
        })
    
    # ==================== АДМИН ПАНЕЛЬ ====================
    @app.route('/admin')
    @login_required
    def admin():
        if current_user.role != 'admin':
            flash('Доступ запрещен', 'danger')
            return redirect(url_for('index'))

        # Статистика
        total_users = User.query.count()
        total_tasks = Task.query.count()
        total_messages = ChatMessage.query.count()
        total_files = TaskFile.query.count()

        # Статистика по статусам задач
        tasks_by_status = db.session.query(
            Task.status,
            db.func.count(Task.id)
        ).group_by(Task.status).all()

        # Статистика по ролям пользователей
        users_by_role = db.session.query(
            User.role,
            db.func.count(User.id)
        ).group_by(User.role).all()

        # Активные чаты (задачи с сообщениями за последние 7 дней)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_chats = db.session.query(Task).join(ChatMessage).filter(
            ChatMessage.created_at >= seven_days_ago
        ).distinct().count()

        # Статистика личных чатов
        total_personal_chats = PersonalChat.query.count()
        active_personal_chats = db.session.query(PersonalChat).join(PersonalMessage).filter(
            PersonalMessage.created_at >= seven_days_ago
        ).distinct().count()
        total_personal_messages = PersonalMessage.query.count()

        # Статистика файлов
        total_file_size = db.session.query(db.func.sum(TaskFile.file_size)).scalar() or 0
        total_file_size_mb = round(total_file_size / (1024 * 1024), 2)

        # Последние задачи (с последними изменениями - создание или редактирование)
        # Сортируем по updated_at если есть, иначе по created_at
        recent_tasks = Task.query.order_by(
            db.case(
                (Task.updated_at.isnot(None), Task.updated_at),
                else_=Task.created_at
            ).desc()
        ).limit(5).all()

        # Последние пользователи
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

        return render_template('admin.html',
                             total_users=total_users,
                             total_tasks=total_tasks,
                             total_messages=total_messages,
                             total_files=total_files,
                             total_file_size_mb=total_file_size_mb,
                             tasks_by_status=dict(tasks_by_status),
                             users_by_role=dict(users_by_role),
                             active_chats=active_chats,
                             total_personal_chats=total_personal_chats,
                             active_personal_chats=active_personal_chats,
                             total_personal_messages=total_personal_messages,
                             recent_tasks=recent_tasks,
                             recent_users=recent_users)
    
    @app.route('/admin/api/stats')
    @login_required
    def admin_api_stats():
        if current_user.role != 'admin':
            return jsonify({'error': 'Доступ запрещен'}), 403

        # Статистика
        total_users = User.query.count()
        total_tasks = Task.query.count()
        total_messages = ChatMessage.query.count()
        total_files = TaskFile.query.count()

        # Статистика по статусам задач
        tasks_by_status = db.session.query(
            Task.status,
            db.func.count(Task.id)
        ).group_by(Task.status).all()

        # Статистика по ролям пользователей
        users_by_role = db.session.query(
            User.role,
            db.func.count(User.id)
        ).group_by(User.role).all()

        # Активные чаты задач (7 дней)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_chats = db.session.query(Task).join(ChatMessage).filter(
            ChatMessage.created_at >= seven_days_ago
        ).distinct().count()

        # Статистика личных чатов
        total_personal_chats = PersonalChat.query.count()
        active_personal_chats = db.session.query(PersonalChat).join(PersonalMessage).filter(
            PersonalMessage.created_at >= seven_days_ago
        ).distinct().count()
        total_personal_messages = PersonalMessage.query.count()

        # Статистика файлов
        total_file_size = db.session.query(db.func.sum(TaskFile.file_size)).scalar() or 0
        
        # Группировка по типам файлов
        all_files = TaskFile.query.all()
        files_by_type_dict = {}
        for f in all_files:
            if f.is_image:
                ftype = 'images'
            elif f.is_pdf:
                ftype = 'pdf'
            elif f.is_dicom:
                ftype = 'dicom'
            elif f.is_archive:
                ftype = 'archives'
            else:
                ftype = 'other'
            
            if ftype not in files_by_type_dict:
                files_by_type_dict[ftype] = {'count': 0, 'size': 0}
            files_by_type_dict[ftype]['count'] += 1
            files_by_type_dict[ftype]['size'] += f.file_size
        
        files_by_type = [
            {'type': k, 'count': v['count'], 'size_mb': round(v['size'] / (1024 * 1024), 2)}
            for k, v in files_by_type_dict.items()
        ]

        return jsonify({
            'total_users': total_users,
            'total_tasks': total_tasks,
            'total_messages': total_messages,
            'total_files': total_files,
            'total_file_size_mb': round(total_file_size / (1024 * 1024), 2),
            'tasks_by_status': dict(tasks_by_status),
            'users_by_role': dict(users_by_role),
            'active_chats': active_chats,
            'total_personal_chats': total_personal_chats,
            'active_personal_chats': active_personal_chats,
            'total_personal_messages': total_personal_messages,
            'files_by_type': files_by_type
        })
    
    @app.route('/admin/api/users')
    @login_required
    def admin_api_users():
        if current_user.role != 'admin':
            return jsonify({'error': 'Доступ запрещен'}), 403

        users = User.query.order_by(User.created_at.desc()).all()

        result = []
        for user in users:
            result.append({
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'role_display': user.get_role_display(),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'middle_name': user.middle_name or '',
                'full_name': user.get_full_name(),
                'department': user.department,
                'created_at': (user.created_at + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M'),
                'last_seen': (user.last_seen + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M') if user.last_seen else 'Никогда',
                'is_online': user.is_online()
            })

        return jsonify(result)
    
    @app.route('/admin/api/tasks')
    @login_required
    def admin_api_tasks():
        if current_user.role != 'admin':
            return jsonify({'error': 'Доступ запрещен'}), 403

        # Сортируем по последнему изменению (updated_at или created_at)
        # Используем execution_options для избежания кэширования
        tasks = Task.query.order_by(
            db.case(
                (Task.updated_at.isnot(None), Task.updated_at),
                else_=Task.created_at
            ).desc()
        ).execution_options(populate_existing=True).all()

        result = []
        for task in tasks:
            result.append({
                'id': task.id,
                'title': task.title,
                'status': task.status,
                'status_display': task.get_status_display(),
                'doctor': task.doctor.get_full_name(),
                'doctor_full_name': task.doctor.get_full_name_with_dept(),
                'research_type': task.research_type,
                'patient_card': task.patient_card,
                'created_at': (task.created_at + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M'),
                'updated_at': (task.updated_at + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M') if task.updated_at else None
            })

        return jsonify(result)
    
    @app.route('/admin/api/doctors')
    @login_required
    def admin_api_doctors():
        if current_user.role != 'admin':
            return jsonify({'error': 'Доступ запрещен'}), 403
        
        doctors = User.query.filter_by(role='doctor').all()
        
        return jsonify([{
            'id': d.id,
            'username': d.username
        } for d in doctors])
    
    @app.route('/admin/users')
    @login_required
    def admin_users():
        if current_user.role != 'admin':
            flash('Доступ запрещен', 'danger')
            return redirect(url_for('index'))

        users = User.query.all()
        return render_template('admin_users.html', users=users)
    
    @app.route('/admin/tasks')
    @login_required
    def admin_tasks():
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        
        tasks = Task.query.order_by(Task.created_at.desc()).all()
        doctors = User.query.filter_by(role='doctor').all()
        physicists = User.query.filter_by(role='physicist').all()
        
        return render_template('admin_tasks.html', tasks=tasks, doctors=doctors, physicists=physicists)
    
    @app.route('/admin/tasks/<int:id>/edit')
    @login_required
    def admin_edit_task(id):
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        
        task = Task.query.get_or_404(id)
        doctors = User.query.filter_by(role='doctor').all()
        physicists = User.query.filter_by(role='physicist').all()
        
        return render_template('admin_task_edit.html',
                             task=task,
                             doctors=doctors,
                             physicists=physicists)
    
    @app.route('/admin/tasks/<int:id>/update', methods=['POST'])
    @login_required
    def admin_update_task(id):
        if current_user.role != 'admin':
            return redirect(url_for('index'))

        task = Task.query.get_or_404(id)
        task.title = request.form.get('title', task.title)
        task.description = request.form.get('description', task.description)
        task.status = request.form.get('status', task.status)
        task.priority = request.form.get('priority', task.priority)
        task.doctor_id = request.form.get('doctor_id', task.doctor_id)
        task.physicist_id = request.form.get('physicist_id', task.physicist_id)
        
        # Обновляем поля исследования
        task.research_type = request.form.get('research_type', task.research_type)
        task.patient_card = request.form.get('patient_card', task.patient_card)
        task.aria_availability = request.form.get('aria_availability', '').strip() or None
        task.expert_group = request.form.get('expert_group', '').strip() or None
        
        # Получаем отдельные поля для CT и лечения
        ct_building = request.form.get('ct_building', '').strip()
        ct_equipment = request.form.get('ct_equipment', '').strip()
        treatment_building = request.form.get('treatment_building', '').strip()
        treatment_device = request.form.get('treatment_device', '').strip()
        breath_control = request.form.get('breath_control', '').strip()
        
        print(f'=== ADMIN UPDATE TASK ===', flush=True)
        print(f'ct_building={ct_building}, ct_equipment={ct_equipment}', flush=True)
        print(f'treatment_building={treatment_building}, treatment_device={treatment_device}, breath_control={breath_control}', flush=True)

        # Формируем ct_diagnostic и treatment из отдельных полей
        task.ct_diagnostic = f"{ct_equipment} ({ct_building})" if ct_equipment and ct_building else None
        task.mr_diagnostic = request.form.get('mr_diagnostic', '').strip() or None
        task.pet_diagnostic = request.form.get('pet_diagnostic', '').strip() or None

        # Формируем treatment БЕЗ контроля по дыханию (он отображается отдельным полем)
        task.treatment = f"{treatment_device} ({treatment_building})" if treatment_device and treatment_building else None

        task.breath_control = breath_control if breath_control and breath_control != 'no' else None
        
        print(f'RESULT: ct_diagnostic={task.ct_diagnostic}', flush=True)
        print(f'RESULT: treatment={task.treatment}', flush=True)
        print(f'RESULT: breath_control={task.breath_control}', flush=True)
        print(f'===========================', flush=True)
        
        task.updated_at = datetime.utcnow()

        if task.status == 'completed' and not task.completed_at:
            task.completed_at = datetime.utcnow()
        elif task.status != 'completed':
            task.completed_at = None

        db.session.commit()
        flash(f'Задача #{task.id} обновлена', 'success')
        return redirect(url_for('admin_tasks'))
    
    @app.route('/admin/tasks/<int:id>/delete', methods=['POST'])
    @login_required
    def admin_delete_task(id):
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        
        task = Task.query.get_or_404(id)
        
        # Удаляем сообщения и файлы
        ChatMessage.query.filter_by(task_id=id).delete()
        TaskFile.query.filter_by(task_id=id).delete()
        
        db.session.delete(task)
        db.session.commit()
        
        flash(f'Задача #{task.id} удалена', 'success')
        return redirect(url_for('admin_tasks'))
    
    @app.route('/admin/tasks/mass_update', methods=['POST'])
    @login_required
    def admin_mass_update():
        if current_user.role != 'admin':
            return jsonify({'error': 'Доступ запрещен', 'success': False}), 403

        data = request.get_json()
        task_ids = data.get('task_ids', [])
        action = data.get('action')

        if not task_ids:
            return jsonify({'error': 'Не выбрано задач', 'success': False}), 400

        tasks = Task.query.filter(Task.id.in_(task_ids)).all()

        if action == 'change_status':
            new_status = data.get('new_status')
            for task in tasks:
                task.status = new_status
                task.updated_at = datetime.utcnow()
                if new_status == 'completed':
                    task.completed_at = datetime.utcnow()
                elif task.completed_at:
                    task.completed_at = None
                    
        elif action == 'change_doctor':
            new_doctor = data.get('new_doctor')
            for task in tasks:
                task.doctor_id = new_doctor
                task.updated_at = datetime.utcnow()

        elif action == 'delete':
            # Удаляем сообщения и файлы
            for task in tasks:
                ChatMessage.query.filter_by(task_id=task.id).delete()
                TaskFile.query.filter_by(task_id=task.id).delete()
            
            Task.query.filter(Task.id.in_(task_ids)).delete(synchronize_session=False)
            db.session.commit()
            return jsonify({'success': True, 'deleted_count': len(task_ids)})

        db.session.commit()
        return jsonify({'success': True, 'updated_count': len(tasks)})

    @app.route('/admin/tasks/mass_delete', methods=['POST'])
    @login_required
    def admin_mass_delete():
        # Удалено - теперь удаление через mass_update с action='delete'
        return admin_mass_update()
    
    @app.route('/admin/change_password/<int:user_id>', methods=['GET', 'POST'])
    @login_required
    def admin_change_password(user_id):
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        
        user = User.query.get_or_404(user_id)
        
        if request.method == 'POST':
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password != confirm_password:
                flash('Пароли не совпадают', 'danger')
                return redirect(url_for('admin_change_password', user_id=user_id))

            if len(new_password) < 3:
                flash('Пароль должен быть не менее 3 символов', 'danger')
                return redirect(url_for('admin_change_password', user_id=user_id))
            
            user.set_password(new_password)
            db.session.commit()
            
            flash(f'Пароль для {user.username} изменен', 'success')
            return redirect(url_for('admin_users'))
        
        return render_template('admin_change_password.html', user=user)
    
    @app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
    @login_required
    def admin_delete_user(user_id):
        if current_user.role != 'admin':
            return redirect(url_for('index'))
        
        user = User.query.get_or_404(user_id)
        
        if user.id == current_user.id:
            flash('Нельзя удалить себя', 'danger')
            return redirect(url_for('admin_users'))
        
        admin_count = User.query.filter_by(role='admin').count()
        if user.role == 'admin' and admin_count <= 1:
            flash('Нельзя удалить последнего администратора', 'danger')
            return redirect(url_for('admin_users'))
        
        db.session.delete(user)
        db.session.commit()
        
        flash(f'Пользователь {user.username} удален', 'success')
        return redirect(url_for('admin_users'))
    
    # ==================== ОБРАБОТКА ОШИБОК ====================
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    return app


# Создаем приложение при запуске файла напрямую
if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000, debug=True)
