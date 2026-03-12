from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, SelectMultipleField, FileField
from wtforms.validators import DataRequired, Length, Optional

# Относительные импорты для работы как пакета
try:
    from ..models import User
except ImportError:
    from models import User


class TaskForm(FlaskForm):
    """Форма создания/редактирования задачи"""
    # Основные поля
    title = StringField('Заголовок', validators=[
        Optional(),  # Необязательно - авто-генерация
        Length(max=200, message='Заголовок не более 200 символов')
    ])
    description = TextAreaField('Описание', validators=[
        Optional(),
        Length(max=5000, message='Описание не более 5000 символов')
    ])
    
    # Тип исследования
    research_type = SelectField('Тип исследования', choices=[
        ('import_ct', 'Импорт CT'),
        ('import_ct_diag', 'Импорт CT-диагностики'),
        ('mr', 'Импорт MR'),
        ('pet', 'Импорт PET')
    ], validators=[DataRequired()])
    
    # Экспертная группа (только для CT)
    expert_group = SelectField('Экспертная группа', choices=[
        ('', 'Выберите экспертную группу'),
        ('ПГШ', 'ПГШ'),
        ('Молочная железа', 'Молочная железа'),
        ('Предстательная железа / мочевой пузырь', 'Предстательная железа / мочевой пузырь'),
        ('Прямая кишка', 'Прямая кишка'),
        ('Лёгкое', 'Лёгкое'),
        ('Матка / вульва', 'Матка / вульва'),
        ('Шейка матки', 'Шейка матки'),
        ('Головной мозг', 'Головной мозг'),
        ('Печень / поджелудочная железа', 'Печень / поджелудочная железа'),
        ('Лимфома', 'Лимфома')
    ], validators=[Optional()])
    
    # Карта пациента
    patient_card = StringField('Карта пациента', validators=[
        DataRequired(message='Введите номер карты пациента'),
        Length(max=100, message='Не более 100 символов')
    ])
    
    # Поля для CT
    ct_building = StringField('Корпус для CT', validators=[Optional()])
    ct_equipment = StringField('Аппарат CT', validators=[Optional()])
    treatment_building = StringField('Корпус для лечения', validators=[Optional()])
    treatment_device = StringField('Аппарат для лечения', validators=[Optional()])
    breath_control = StringField('Контроль по дыханию', validators=[Optional()])
    
    # Для MR/PET
    data_source = SelectField('Источник данных', choices=[
        ('', 'Выберите источник'),
        ('disc', 'Диск'),
        ('server', 'Сервер')
    ], validators=[Optional()])
    server_location = StringField('Корпус сервера', validators=[Optional()])
    
    # Приоритет (оставляем для совместимости, но скрываем в UI)
    priority = SelectField('Приоритет', choices=[
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочно')
    ], default='medium')
    
    # Файлы
    files = FileField('Прикрепить файлы', validators=[Optional()])
    
    submit = SubmitField('Создать задачу')


class TaskEditForm(TaskForm):
    """Форма редактирования задачи (с расширенными возможностями)"""
    status = SelectField('Статус', choices=[
        ('pending', 'Ожидает'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнена'),
        ('cancelled', 'Отменена')
    ])
    
    doctor_id = SelectField('Врач', coerce=int)
    
    submit = SubmitField('Сохранить изменения')


class CommentForm(FlaskForm):
    """Форма комментария к задаче"""
    content = TextAreaField('Комментарий', validators=[
        DataRequired(message='Введите текст комментария'),
        Length(max=2000, message='Комментарий не более 2000 символов')
    ])
    submit = SubmitField('Отправить')


class MassActionForm(FlaskForm):
    """Форма массовых действий"""
    action = SelectField('Действие', choices=[
        ('change_status', 'Изменить статус'),
        ('change_doctor', 'Изменить врача'),
        ('delete', 'Удалить задачи')
    ])
    new_status = SelectField('Новый статус', choices=[
        ('pending', 'Ожидает'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнена'),
        ('cancelled', 'Отменена')
    ])
    new_doctor = SelectField('Новый врач', coerce=int)
    submit = SubmitField('Выполнить')
