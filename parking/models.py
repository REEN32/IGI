from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import date


def validate_age_18_plus(born):
    today = date.today()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    if age < 18:
        raise ValidationError('Клиенты и сотрудники должны быть старше 18 лет.')


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_regex = RegexValidator(
        regex=r'^\+375 \(29\) \d{3}-\d{2}-\d{2}$',
        message="Номер телефона должен быть в формате: +375 (29) XXX-XX-XX"
    )
    phone = models.CharField(validators=[phone_regex], max_length=20)
    birth_date = models.DateField(validators=[validate_age_18_plus], verbose_name="Дата рождения")

    is_employee = models.BooleanField(default=False, verbose_name="Сотрудник")

    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Авансовый счет")

    def __str__(self):
        return f"Профиль: {self.user.username} (Баланс: {self.balance})"


class Car(models.Model):
    brand = models.CharField(max_length=50, verbose_name="Марка")
    model = models.CharField(max_length=50, verbose_name="Модель")
    plate_number = models.CharField(max_length=15, unique=True, verbose_name="Номер авто")
    owners = models.ManyToManyField(Profile, related_name='cars', verbose_name="Владельцы")

    def __str__(self):
        return f"{self.brand} {self.model} [{self.plate_number}]"


class ParkingSpot(models.Model):
    number = models.PositiveIntegerField(
        validators=[MaxValueValidator(999)],
        unique=True,
        verbose_name="Номер места"
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена в месяц")
    is_occupied = models.BooleanField(default=False, verbose_name="Занято")
    current_car = models.OneToOneField(
        Car, on_delete=models.SET_NULL, null=True, blank=True, related_name='parking_spot'
    )

    def __str__(self):
        return f"Место №{self.number} (Цена: {self.price})"


class Invoice(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='invoices')
    spot = models.ForeignKey(ParkingSpot, on_delete=models.SET_NULL, null=True, verbose_name="Место")
    accrual_date = models.DateField(verbose_name="Дата начисления")
    payment_date = models.DateField(null=True, blank=True, verbose_name="Дата оплаты")
    accrued_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Начислено")
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Оплачено")

    @property
    def debt(self):
        return self.accrued_amount - self.paid_amount

    def __str__(self):
        return f"Счет {self.id} | Авто: {self.car.plate_number} | Долг: {self.debt}"


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")

    def __str__(self):
        return self.name


class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=150, verbose_name="Название услуги")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена")

    def __str__(self):
        return self.name


class PromoCode(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name="Промокод")
    discount_percent = models.PositiveIntegerField(verbose_name="Скидка (%)")
    is_active = models.BooleanField(default=True, verbose_name="Действует")

    def __str__(self):
        return self.code


class Review(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], verbose_name="Оценка")
    text = models.TextField(verbose_name="Текст отзыва")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")

    def __str__(self):
        return f"Отзыв от {self.author.username} ({self.rating}/5)"


class Article(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    summary = models.CharField(max_length=255, verbose_name="Краткое содержание")
    content = models.TextField(verbose_name="Полный текст")
    image_url = models.URLField(blank=True, null=True, verbose_name="Ссылка на картинку")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField(max_length=255, verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    added_at = models.DateField(auto_now_add=True, verbose_name="Дата добавления")

    def __str__(self):
        return self.question


class EmployeeContact(models.Model):
    name = models.CharField(max_length=100, verbose_name="ФИО сотрудника")
    position = models.CharField(max_length=100, verbose_name="Должность / Выполняемые работы")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Электронная почта")
    photo_url = models.URLField(blank=True, null=True, verbose_name="Ссылка на фото сотрудника")

    def __str__(self):
        return f"{self.name} — {self.position}"


class Vacancy(models.Model):
    title = models.CharField(max_length=100, verbose_name="Название вакансии")
    description = models.TextField(verbose_name="Описание обязанностей и требований")
    salary = models.CharField(max_length=50, blank=True, null=True, verbose_name="Заработная плата")
    is_active = models.BooleanField(default=True, verbose_name="Вакансии открыта")

    def __str__(self):
        return self.title



class AboutCompany(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок страницы", default="О нашей компании")
    description = models.TextField(verbose_name="Основной текст / Описание")
    founded_year = models.PositiveIntegerField(verbose_name="Год основания", blank=True, null=True)
    history_text = models.TextField(verbose_name="История компании", blank=True, null=True)

    class Meta:
        verbose_name = "О компании"
        verbose_name_plural = "О компании"

    def __str__(self):
        return self.title