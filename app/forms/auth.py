from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional
from sqlalchemy import func

# Относительные импорты для работы как пакета
try:
    from ..models import User
except ImportError:
    from models import User


class LoginForm(FlaskForm):
    """Форма входа"""
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Введите имя пользователя'),
        Length(min=2, max=80, message='Имя должно быть от 2 до 80 символов')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Введите пароль'),
        Length(min=3, message='Пароль должен быть не менее 3 символов')
    ])
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    """Форма регистрации нового пользователя"""
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Введите имя пользователя'),
        Length(min=2, max=80, message='Имя должно быть от 2 до 80 символов')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Введите пароль'),
        Length(min=3, message='Пароль должен быть не менее 3 символов')
    ])
    confirm_password = PasswordField('Подтверждение пароля', validators=[
        DataRequired(message='Подтвердите пароль'),
        EqualTo('password', message='Пароли должны совпадать')
    ])
    
    # Новые поля: ФИО
    first_name = StringField('Фамилия', validators=[
        DataRequired(message='Введите фамилию'),
        Length(max=80, message='Фамилия не более 80 символов')
    ])
    last_name = StringField('Имя', validators=[
        DataRequired(message='Введите имя'),
        Length(max=80, message='Имя не более 80 символов')
    ])
    middle_name = StringField('Отчество', validators=[
        Optional(),
        Length(max=80, message='Отчество не более 80 символов')
    ])
    
    role = SelectField('Роль', choices=[
        ('doctor', 'Врач'),
        ('physicist', 'Физик')
    ], validators=[DataRequired()])
    
    # Отделение (заполняется динамически в зависимости от роли)
    department = SelectField('Отделение', choices=[], validators=[DataRequired()])
    
    submit = SubmitField('Зарегистрировать')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        # Устанавливаем варианты отделений в зависимости от роли
        if self.role.data == 'doctor':
            self.department.choices = [
                ('РО1', 'РО1'),
                ('РО2', 'РО2'),
                ('РО3', 'РО3'),
                ('РО4', 'РО4'),
                ('РО5', 'РО5')
            ]
        elif self.role.data == 'physicist':
            self.department.choices = [('ФРО', 'ФРО')]
        else:
            self.department.choices = [('ТП', 'ТП')]

    def validate_username(self, username):
        # Проверка на уникальность (case-insensitive)
        user = User.query.filter(func.lower(User.username) == func.lower(username.data)).first()
        if user:
            raise ValidationError('Пользователь с таким именем уже существует')


class PasswordChangeForm(FlaskForm):
    """Форма смены пароля"""
    new_password = PasswordField('Новый пароль', validators=[
        DataRequired(message='Введите новый пароль'),
        Length(min=3, message='Пароль должен быть не менее 3 символов')
    ])
    confirm_password = PasswordField('Подтверждение пароля', validators=[
        DataRequired(message='Подтвердите пароль'),
        EqualTo('new_password', message='Пароли должны совпадать')
    ])
    submit = SubmitField('Изменить пароль')
