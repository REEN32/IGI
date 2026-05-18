# tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from decimal import Decimal
from datetime import date, timedelta
from parking.models import (
    Profile, Car, ParkingSpot, Invoice, Review,
    Article, FAQ, PromoCode, EmployeeContact, Vacancy, AboutCompany
)


class HomeViewTest(TestCase):
    """Тесты главной страницы"""

    def setUp(self):
        self.client = Client()
        self.article = Article.objects.create(
            title='Тестовая статья',
            summary='Краткое содержание',
            content='Полный текст'
        )

    def test_home_page_loads(self):
        """Тест загрузки главной страницы"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'parking/home.html')

    def test_home_page_displays_latest_article(self):
        """Тест отображения последней статьи на главной"""
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Тестовая статья')


class ServicesViewTest(TestCase):
    """Тесты страницы услуг"""

    def test_services_page_loads(self):
        """Тест загрузки страницы услуг"""
        response = self.client.get(reverse('services'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'parking/services.html')


    def test_price_filter(self):
        """Тест фильтрации по цене"""
        response = self.client.get(reverse('services'), {'max_price': 80})
        self.assertEqual(response.status_code, 200)


class RegisterViewTest(TestCase):
    """Тесты регистрации пользователя"""

    def setUp(self):
        self.client = Client()

    def test_register_page_loads(self):
        """Тест загрузки страницы регистрации"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'parking/register.html')

    def test_successful_registration(self):
        """Тест успешной регистрации"""
        post_data = {
            'username': 'newuser123',
            'first_name': 'Иван',
            'last_name': 'Петров',
            'email': 'ivan@example.com',
            'password': 'securepass123',
            'phone': '+375 (29) 123-45-67',
            'birth_date': '1990-01-01'
        }
        response = self.client.post(reverse('register'), post_data)

        self.assertTrue(User.objects.filter(username='newuser123').exists())
        user = User.objects.get(username='newuser123')
        self.assertTrue(Profile.objects.filter(user=user).exists())

        self.assertRedirects(response, reverse('dashboard'))

    def test_registration_with_invalid_data(self):
        """Тест регистрации с неверными данными"""
        post_data = {
            'username': 'newuser',
            'email': 'invalid-email'
        }
        response = self.client.post(reverse('register'), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())


class DashboardViewTest(TestCase):
    """Тесты личного кабинета"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            phone='+375 (29) 123-45-67',
            birth_date=date(1990, 1, 1),
            balance=100.00
        )
        self.car = Car.objects.create(
            brand='Toyota',
            model='Camry',
            plate_number='TEST123'
        )
        self.car.owners.add(self.profile)

    def test_dashboard_requires_login(self):
        """Тест - дашборд требует авторизации"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_dashboard_loads_for_authenticated_user(self):
        """Тест загрузки дашборда для авторизованного пользователя"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'parking/dashboard.html')

    def test_dashboard_displays_user_cars(self):
        """Тест отображения автомобилей пользователя"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Toyota Camry')


class AddCarViewTest(TestCase):
    """Тесты добавления автомобиля"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            phone='+375 (29) 123-45-67',
            birth_date=date(1990, 1, 1)
        )
        self.spot = ParkingSpot.objects.create(number=1, price=100, is_occupied=False)
        self.client.login(username='testuser', password='testpass123')

    def test_add_car_with_valid_data(self):
        """Тест добавления автомобиля с корректными данными"""
        post_data = {
            'brand': 'Toyota',
            'model': 'Camry',
            'plate_number': 'NEW123',
            'spot_id': self.spot.id
        }
        response = self.client.post(reverse('add_car'), post_data)

        car = Car.objects.filter(plate_number='NEW123').first()
        self.assertIsNotNone(car)
        self.assertIn(self.profile, car.owners.all())

        self.spot.refresh_from_db()
        self.assertTrue(self.spot.is_occupied)

        self.assertRedirects(response, reverse('dashboard'))


class PayInvoiceViewTest(TestCase):
    """Тесты оплаты счета"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            phone='+375 (29) 123-45-67',
            birth_date=date(1990, 1, 1),
            balance=200.00
        )
        self.car = Car.objects.create(
            brand='Toyota',
            model='Camry',
            plate_number='TEST123'
        )
        self.car.owners.add(self.profile)
        self.spot = ParkingSpot.objects.create(number=1, price=100)
        self.client.login(username='testuser', password='testpass123')


    def test_cannot_pay_others_invoice(self):
        """Тест - нельзя оплатить чужой счет"""
        other_user = User.objects.create_user(username='other', password='otherpass')
        other_profile = Profile.objects.create(
            user=other_user,
            phone='+375 (29) 999-99-99',
            birth_date=date(1995, 1, 1)
        )
        other_car = Car.objects.create(
            brand='Honda',
            model='Civic',
            plate_number='OTHER123'
        )
        other_car.owners.add(other_profile)
        other_invoice = Invoice.objects.create(
            car=other_car,
            spot=self.spot,
            accrual_date=date.today(),
            accrued_amount=50.00,
            paid_amount=0
        )

        post_data = {'payment_amount': '50'}
        response = self.client.post(
            reverse('pay_invoice', args=[other_invoice.id]),
            post_data
        )

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('чужой' in str(m) for m in messages))


class EmployeeDashboardViewTest(TestCase):
    """Тесты панели сотрудника"""

    def setUp(self):
        self.client = Client()
        self.employee_user = User.objects.create_user(
            username='employee',
            password='employeepass'
        )
        self.employee_profile = Profile.objects.create(
            user=self.employee_user,
            phone='+375 (29) 111-11-11',
            birth_date=date(1985, 1, 1),
            is_employee=True
        )

        self.regular_user = User.objects.create_user(
            username='regular',
            password='regularpass'
        )
        self.regular_profile = Profile.objects.create(
            user=self.regular_user,
            phone='+375 (29) 222-22-22',
            birth_date=date(1995, 1, 1),
            is_employee=False
        )

    def test_employee_dashboard_requires_employee_status(self):
        """Тест - панель сотрудника требует статус сотрудника"""
        self.client.login(username='regular', password='regularpass')
        response = self.client.get(reverse('employee_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_employee_dashboard_loads_for_employee(self):
        """Тест загрузки панели для сотрудника"""
        self.client.login(username='employee', password='employeepass')
        response = self.client.get(reverse('employee_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'parking/employee_dashboard.html')

    def test_employee_dashboard_displays_clients(self):
        """Тест отображения клиентов в панели сотрудника"""
        self.client.login(username='employee', password='employeepass')
        response = self.client.get(reverse('employee_dashboard'))
        self.assertContains(response, 'regular')



class DeleteCarViewTest(TestCase):
    """Тесты удаления автомобиля"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            phone='+375 (29) 123-45-67',
            birth_date=date(1990, 1, 1)
        )
        self.car = Car.objects.create(
            brand='Toyota',
            model='Camry',
            plate_number='DELETE123'
        )
        self.car.owners.add(self.profile)
        self.spot = ParkingSpot.objects.create(
            number=1,
            price=100,
            is_occupied=True,
            current_car=self.car
        )
        self.client.login(username='testuser', password='testpass123')

    def test_delete_car(self):
        """Тест удаления автомобиля"""
        response = self.client.post(reverse('delete_car', args=[self.car.id]))

        self.assertFalse(Car.objects.filter(id=self.car.id).exists())

        self.spot.refresh_from_db()
        self.assertFalse(self.spot.is_occupied)
        self.assertIsNone(self.spot.current_car)

        self.assertRedirects(response, reverse('dashboard'))


class ReviewsViewTest(TestCase):
    """Тесты страницы отзывов"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_reviews_page_loads(self):
        """Тест загрузки страницы отзывов"""
        response = self.client.get(reverse('reviews'))
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_can_post_review(self):
        """Тест - авторизованный пользователь может оставить отзыв"""
        self.client.login(username='testuser', password='testpass123')
        post_data = {
            'rating': '5',
            'text': 'Отличная стоянка!'
        }
        response = self.client.post(reverse('reviews'), post_data)

        self.assertTrue(Review.objects.filter(author=self.user).exists())

    def test_unauthenticated_user_cannot_post_review(self):
        """Тест - неавторизованный пользователь не может оставить отзыв"""
        post_data = {
            'rating': '5',
            'text': 'Отличная стоянка!'
        }
        response = self.client.post(reverse('reviews'), post_data)

        self.assertFalse(Review.objects.filter(text='Отличная стоянка!').exists())


class CheckPromoCodeViewTest(TestCase):
    """Тесты проверки промокода"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
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
        self.spot = ParkingSpot.objects.create(number=1, price=100)
        self.invoice = Invoice.objects.create(
            car=self.car,
            spot=self.spot,
            accrual_date=date.today(),
            accrued_amount=100.00,
            paid_amount=0
        )
        self.promo = PromoCode.objects.create(
            code='TEST20',
            discount_percent=20,
            is_active=True
        )
        self.client.login(username='testuser', password='testpass123')

    def test_check_valid_promo_code(self):
        """Тест проверки валидного промокода"""
        response = self.client.get(
            reverse('check_promocode'),
            {'promo_code': 'TEST20', 'invoice_id': self.invoice.id}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['discount_percent'], 20)
        self.assertLess(data['final_amount'], 100)

    def test_check_invalid_promo_code(self):
        """Тест проверки невалидного промокода"""
        response = self.client.get(
            reverse('check_promocode'),
            {'promo_code': 'INVALID', 'invoice_id': self.invoice.id}
        )

        data = response.json()
        self.assertFalse(data['success'])


class AdminStatisticsViewTest(TestCase):
    """Тесты административной статистики"""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            email='admin@example.com'
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            password='regularpass'
        )

    def test_admin_stats_requires_staff_status(self):
        """Тест - статистика требует прав персонала"""
        self.client.login(username='regular', password='regularpass')
        response = self.client.get(reverse('admin_statistics'))
        self.assertEqual(response.status_code, 302)

    def test_admin_stats_loads_for_admin(self):
        """Тест загрузки статистики для администратора"""
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('admin_statistics'))
        self.assertEqual(response.status_code, 200)


class ParkingSpotManagementTest(TestCase):
    """Тесты управления парковочными местами"""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass'
        )
        self.spot = ParkingSpot.objects.create(number=1, price=100)
        self.client.login(username='admin', password='adminpass')

    def test_add_parking_spot(self):
        """Тест добавления парковочного места"""
        post_data = {
            'number': 10,
            'price': 150.00
        }
        response = self.client.post(reverse('add_parking_spot'), post_data)

        self.assertTrue(ParkingSpot.objects.filter(number=10).exists())

    def test_edit_parking_spot_price(self):
        """Тест изменения цены парковочного места"""
        post_data = {'price': '200.00'}
        response = self.client.post(
            reverse('edit_parking_spot_price', args=[self.spot.id]),
            post_data
        )

        self.spot.refresh_from_db()
        self.assertEqual(self.spot.price, Decimal('200.00'))

    def test_delete_parking_spot(self):
        """Тест удаления парковочного места"""
        response = self.client.post(reverse('delete_parking_spot', args=[self.spot.id]))

        self.assertFalse(ParkingSpot.objects.filter(id=self.spot.id).exists())


class AdditionalPageViewsTest(TestCase):
    """Тесты дополнительных страниц"""

    def setUp(self):
        self.client = Client()

    def test_about_page_loads(self):
        """Тест загрузки страницы 'О компании'"""
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)

    def test_contacts_page_loads(self):
        """Тест загрузки страницы контактов"""
        response = self.client.get(reverse('contacts'))
        self.assertEqual(response.status_code, 200)

    def test_faq_page_loads(self):
        """Тест загрузки страницы FAQ"""
        response = self.client.get(reverse('faq'))
        self.assertEqual(response.status_code, 200)

    def test_privacy_policy_page_loads(self):
        """Тест загрузки страницы политики конфиденциальности"""
        response = self.client.get(reverse('privacy_policy'))
        self.assertEqual(response.status_code, 200)

    def test_vacancies_page_loads(self):
        """Тест загрузки страницы вакансий"""
        response = self.client.get(reverse('vacancies'))
        self.assertEqual(response.status_code, 200)