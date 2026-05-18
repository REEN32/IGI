# tests/test_forms.py
from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from parking.forms import UserRegisterForm, AddCarForm, AddParkingSpotForm
from parking.models import Profile


class UserRegisterFormTest(TestCase):
    """Тесты формы регистрации пользователя"""

    def test_valid_form(self):
        """Тест валидной формы"""
        form_data = {
            'username': 'newuser',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'ivan@example.com',
            'password': 'securepass123',
            'phone': '+375 (29) 123-45-67',
            'birth_date': '1990-01-01'
        }
        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_required_fields(self):
        """Тест отсутствия обязательных полей"""
        form_data = {
            'username': 'newuser',
            'email': 'ivan@example.com'
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_form_saves_user_with_password_hash(self):
        """Тест сохранения пользователя с хэшированным паролем"""
        form_data = {
            'username': 'newuser',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'ivan@example.com',
            'password': 'securepass123',
            'phone': '+375 (29) 123-45-67',
            'birth_date': '1990-01-01'
        }
        form = UserRegisterForm(data=form_data)
        if form.is_valid():
            user = form.save()
            self.assertIsNotNone(user.password)
            self.assertNotEqual(user.password, 'securepass123')


class AddCarFormTest(TestCase):
    """Тесты формы добавления автомобиля"""

    def test_valid_form(self):
        """Тест валидной формы"""
        form_data = {
            'brand': 'Toyota',
            'model': 'Camry',
            'plate_number': '1234-AB7'
        }
        form = AddCarForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_brand_field(self):
        """Тест отсутствия марки автомобиля"""
        form_data = {
            'model': 'Camry',
            'plate_number': '1234-AB7'
        }
        form = AddCarForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('brand', form.errors)

    def test_duplicate_plate_number(self):
        """Тест дублирования номера автомобиля"""
        from parking.models import Car
        Car.objects.create(brand='Honda', model='Civic', plate_number='DUPLICATE123')

        form_data = {
            'brand': 'Toyota',
            'model': 'Camry',
            'plate_number': 'DUPLICATE123'
        }
        form = AddCarForm(data=form_data)
        self.assertFalse(form.is_valid())


class AddParkingSpotFormTest(TestCase):
    """Тесты формы добавления парковочного места"""

    def test_valid_form(self):
        """Тест валидной формы"""
        form_data = {
            'number': 10,
            'price': 150.50
        }
        form = AddParkingSpotForm(data=form_data)
        self.assertTrue(form.is_valid())


    def test_duplicate_spot_number(self):
        """Тест дублирования номера места"""
        from parking.models import ParkingSpot
        ParkingSpot.objects.create(number=5, price=100)

        form_data = {
            'number': 5,
            'price': 120
        }
        form = AddParkingSpotForm(data=form_data)
        self.assertFalse(form.is_valid())