# tests/test_models.py
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta
from parking.models import (
    Profile, Car, ParkingSpot, Invoice, ServiceCategory, Service,
    PromoCode, Review, Article, FAQ, EmployeeContact, Vacancy, AboutCompany
)


class ProfileModelTest(TestCase):
    """Тесты модели Profile"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_create_profile_with_valid_data(self):
        """Тест создания профиля с корректными данными"""
        profile = Profile.objects.create(
            user=self.user,
            phone='+375 (29) 123-45-67',
            birth_date=date(1990, 1, 1),
            is_employee=False,
            balance=100.00
        )

        self.assertEqual(profile.user.username, 'testuser')
        self.assertEqual(profile.phone, '+375 (29) 123-45-67')
        self.assertEqual(profile.balance, Decimal('100.00'))
        self.assertFalse(profile.is_employee)


    def test_phone_validation_invalid_format(self):
        """Тест валидации телефона - неверный формат"""
        profile = Profile(
            user=self.user,
            phone='123456789',
            birth_date=date(1990, 1, 1)
        )
        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_age_validation_under_18(self):
        """Тест валидации возраста - младше 18 лет"""
        today = date.today()
        under_18_date = date(today.year - 17, today.month, today.day)

        profile = Profile(
            user=self.user,
            phone='+375 (29) 123-45-67',
            birth_date=under_18_date
        )
        with self.assertRaises(ValidationError):
            profile.full_clean()


class CarModelTest(TestCase):
    """Тесты модели Car"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.profile = Profile.objects.create(
            user=self.user,
            phone='+375 (29) 123-45-67',
            birth_date=date(1990, 1, 1)
        )

    def test_create_car_with_owners(self):
        """Тест создания автомобиля с владельцами"""
        car = Car.objects.create(
            brand='Toyota',
            model='Camry',
            plate_number='1234-AB7'
        )
        car.owners.add(self.profile)

        self.assertEqual(car.brand, 'Toyota')
        self.assertEqual(car.model, 'Camry')
        self.assertEqual(car.plate_number, '1234-AB7')
        self.assertEqual(car.owners.count(), 1)
        self.assertIn(self.profile, car.owners.all())

    def test_car_str_method(self):
        """Тест строкового представления автомобиля"""
        car = Car.objects.create(
            brand='BMW',
            model='X5',
            plate_number='5678-CD9'
        )
        self.assertEqual(str(car), 'BMW X5 [5678-CD9]')

    def test_car_plate_number_unique(self):
        """Тест уникальности номера автомобиля"""
        Car.objects.create(brand='Toyota', model='Camry', plate_number='UNIQUE123')

        with self.assertRaises(Exception):
            Car.objects.create(brand='Honda', model='Civic', plate_number='UNIQUE123')


class ParkingSpotModelTest(TestCase):
    """Тесты модели ParkingSpot"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.profile = Profile.objects.create(
            user=self.user,
            phone='+375 (29) 123-45-67',
            birth_date=date(1990, 1, 1)
        )
        self.car = Car.objects.create(
            brand='Toyota',
            model='Camry',
            plate_number='TEST123'
        )
        self.car.owners.add(self.profile)

    def test_create_parking_spot(self):
        """Тест создания парковочного места"""
        spot = ParkingSpot.objects.create(
            number=1,
            price=100.00,
            is_occupied=False
        )

        self.assertEqual(spot.number, 1)
        self.assertEqual(spot.price, Decimal('100.00'))
        self.assertFalse(spot.is_occupied)

    def test_parking_spot_occupation(self):
        """Тест занятия парковочного места"""
        spot = ParkingSpot.objects.create(
            number=2,
            price=150.00,
            is_occupied=False,
            current_car=None
        )

        spot.is_occupied = True
        spot.current_car = self.car
        spot.save()

        spot.refresh_from_db()
        self.assertTrue(spot.is_occupied)
        self.assertEqual(spot.current_car, self.car)



class InvoiceModelTest(TestCase):
    """Тесты модели Invoice"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.profile = Profile.objects.create(
            user=self.user,
            phone='+375 (29) 123-45-67',
            birth_date=date(1990, 1, 1),
            balance=500.00
        )
        self.car = Car.objects.create(
            brand='Toyota',
            model='Camry',
            plate_number='TEST123'
        )
        self.car.owners.add(self.profile)
        self.spot = ParkingSpot.objects.create(number=1, price=100.00)


class ServiceCategoryModelTest(TestCase):
    """Тесты модели ServiceCategory"""

    def test_create_service_category(self):
        category = ServiceCategory.objects.create(name='Ремонт')
        self.assertEqual(category.name, 'Ремонт')
        self.assertEqual(str(category), 'Ремонт')


class ServiceModelTest(TestCase):
    """Тесты модели Service"""

    def setUp(self):
        self.category = ServiceCategory.objects.create(name='Ремонт')

    def test_create_service(self):
        service = Service.objects.create(
            category=self.category,
            name='Замена масла',
            price=50.00
        )
        self.assertEqual(service.name, 'Замена масла')
        self.assertEqual(service.price, Decimal('50.00'))
        self.assertEqual(str(service), 'Замена масла')


class PromoCodeModelTest(TestCase):
    """Тесты модели PromoCode"""

    def test_create_promo_code(self):
        promo = PromoCode.objects.create(
            code='DISCOUNT20',
            discount_percent=20,
            is_active=True
        )
        self.assertEqual(promo.code, 'DISCOUNT20')
        self.assertEqual(promo.discount_percent, 20)
        self.assertTrue(promo.is_active)
        self.assertEqual(str(promo), 'DISCOUNT20')


class ReviewModelTest(TestCase):
    """Тесты модели Review"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_create_review(self):
        review = Review.objects.create(
            author=self.user,
            rating=5,
            text='Отличная автостоянка!'
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.text, 'Отличная автостоянка!')
        self.assertIn('testuser', str(review))


class ArticleModelTest(TestCase):
    """Тесты модели Article"""

    def test_create_article(self):
        article = Article.objects.create(
            title='Новости стоянки',
            summary='Краткое содержание',
            content='Полный текст статьи...'
        )
        self.assertEqual(article.title, 'Новости стоянки')
        self.assertEqual(str(article), 'Новости стоянки')


class FAQModelTest(TestCase):
    """Тесты модели FAQ"""

    def test_create_faq(self):
        faq = FAQ.objects.create(
            question='Как забронировать место?',
            answer='Позвоните по телефону...'
        )
        self.assertEqual(faq.question, 'Как забронировать место?')
        self.assertEqual(str(faq), 'Как забронировать место?')


class EmployeeContactModelTest(TestCase):
    """Тесты модели EmployeeContact"""

    def test_create_employee_contact(self):
        employee = EmployeeContact.objects.create(
            name='Иван Иванов',
            position='Администратор',
            phone='+375 (29) 123-45-67',
            email='ivan@example.com'
        )
        self.assertEqual(employee.name, 'Иван Иванов')
        self.assertEqual(str(employee), 'Иван Иванов — Администратор')


class VacancyModelTest(TestCase):
    """Тесты модели Vacancy"""

    def test_create_vacancy(self):
        vacancy = Vacancy.objects.create(
            title='Охранник',
            description='Охрана территории',
            salary='1000 руб',
            is_active=True
        )
        self.assertEqual(vacancy.title, 'Охранник')
        self.assertTrue(vacancy.is_active)
        self.assertEqual(str(vacancy), 'Охранник')


class AboutCompanyModelTest(TestCase):
    """Тесты модели AboutCompany"""

    def test_create_about_company(self):
        about = AboutCompany.objects.create(
            title='О нашей компании',
            description='Мы лучшие!',
            founded_year=2020
        )
        self.assertEqual(about.title, 'О нашей компании')
        self.assertEqual(about.founded_year, 2020)
        self.assertEqual(str(about), 'О нашей компании')