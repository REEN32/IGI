# tests/test_urls.py
from django.test import SimpleTestCase
from django.urls import reverse, resolve
from parking import views


class UrlsTest(SimpleTestCase):
    """Тесты URL маршрутов"""

    def test_home_url_resolves(self):
        """Тест - URL главной страницы разрешается"""
        url = reverse('home')
        self.assertEqual(resolve(url).func, views.home_view)

    def test_services_url_resolves(self):
        """Тест - URL услуг разрешается"""
        url = reverse('services')
        self.assertEqual(resolve(url).func, views.services_view)

    def test_dashboard_url_resolves(self):
        """Тест - URL дашборда разрешается"""
        url = reverse('dashboard')
        self.assertEqual(resolve(url).func, views.dashboard_view)

    def test_register_url_resolves(self):
        """Тест - URL регистрации разрешается"""
        url = reverse('register')
        self.assertEqual(resolve(url).func, views.register_view)

    def test_login_url_resolves(self):
        """Тест - URL логина разрешается"""
        url = reverse('login')
        self.assertEqual(resolve(url).func.view_class.__name__, 'LoginView')

    def test_logout_url_resolves(self):
        """Тест - URL логаута разрешается"""
        url = reverse('logout')
        self.assertEqual(resolve(url).func.view_class.__name__, 'LogoutView')

    def test_add_car_url_resolves(self):
        """Тест - URL добавления авто разрешается"""
        url = reverse('add_car')
        self.assertEqual(resolve(url).func, views.add_car_view)

    def test_employee_dashboard_url_resolves(self):
        """Тест - URL панели сотрудника разрешается"""
        url = reverse('employee_dashboard')
        self.assertEqual(resolve(url).func, views.employee_dashboard_view)

    def test_about_url_resolves(self):
        """Тест - URL 'О компании' разрешается"""
        url = reverse('about')
        self.assertEqual(resolve(url).func, views.about_view)

    def test_contacts_url_resolves(self):
        """Тест - URL контактов разрешается"""
        url = reverse('contacts')
        self.assertEqual(resolve(url).func, views.contacts_view)

    def test_faq_url_resolves(self):
        """Тест - URL FAQ разрешается"""
        url = reverse('faq')
        self.assertEqual(resolve(url).func, views.faq_view)

    def test_vacancies_url_resolves(self):
        """Тест - URL вакансий разрешается"""
        url = reverse('vacancies')
        self.assertEqual(resolve(url).func, views.vacancies_view)

    def test_check_promocode_url_resolves(self):
        """Тест - URL проверки промокода разрешается"""
        url = reverse('check_promocode')
        self.assertEqual(resolve(url).func, views.check_promocode_view)