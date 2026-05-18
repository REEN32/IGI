# tests/test_utils.py
from django.test import TestCase
from parking.models import validate_age_18_plus
from django.core.exceptions import ValidationError
from datetime import date, timedelta


class ValidationUtilsTest(TestCase):
    """Тесты утилит валидации"""

    def test_age_validation_passes_for_adult(self):
        """Тест - валидация проходит для взрослого"""
        adult_date = date(1990, 1, 1)
        # Не должно вызывать исключение
        validate_age_18_plus(adult_date)

    def test_age_validation_fails_for_minor(self):
        """Тест - валидация не проходит для несовершеннолетнего"""
        today = date.today()
        minor_date = date(today.year - 17, today.month, today.day)

        with self.assertRaises(ValidationError):
            validate_age_18_plus(minor_date)

    def test_age_validation_passes_for_exactly_18(self):
        """Тест - валидация проходит для ровно 18 лет"""
        today = date.today()
        exactly_18 = date(today.year - 18, today.month, today.day)

        validate_age_18_plus(exactly_18)