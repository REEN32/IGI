import logging
logger = logging.getLogger('parking')
from django.db.models import Max, Case, When, Value, BooleanField
from .models import Service, Review
from django.contrib.auth import login
from .forms import UserRegisterForm
from .models import FAQ
from django.db import transaction
from django.shortcuts import render
from .models import Car
from .forms import AddCarForm
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from .models import PromoCode
from decimal import Decimal
import statistics
from django.db.models import Count, Sum, F, Q
from django.core.exceptions import PermissionDenied
from datetime import date
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.contrib.auth.decorators import login_required
from .models import Profile, Invoice, ParkingSpot
import requests
import calendar
from datetime import datetime, timezone as dt_timezone
from django.utils import timezone as django_timezone
from .models import Article
from .models import EmployeeContact, Vacancy
from .models import AboutCompany
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from .forms import AddParkingSpotForm


@staff_member_required
def admin_statistics_view(request):
    """Кастомное представление для вывода сложной статистики админу"""
    logger.info(f"Администратор {request.user.username} открыл страницу статистики")

    try:
        cars_with_multiple_owners = Car.objects.annotate(owner_count=Count('owners')).filter(owner_count__gt=1)
        logger.debug(f"Найдено автомобилей с несколькими владельцами: {cars_with_multiple_owners.count()}")

        profiles_with_debt = Profile.objects.annotate(
            total_debt=Sum(F('cars__invoices__accrued_amount') - F('cars__invoices__paid_amount'))
        ).order_by('-total_debt')

        top_debtor = profiles_with_debt.first() if profiles_with_debt else None

        last_payment_date = None
        if top_debtor:
            last_payment = Invoice.objects.filter(
                car__owners=top_debtor,
                payment_date__isnull=False
            ).aggregate(Max('payment_date'))['payment_date__max']
            last_payment_date = last_payment
            logger.info(f"Главный должник: {top_debtor.user.username}, долг: {top_debtor.total_debt}")

        cars_with_debt = Car.objects.annotate(
            total_debt=Sum(F('invoices__accrued_amount') - F('invoices__paid_amount'))
        ).order_by('total_debt')
        car_min_debt = cars_with_debt.first() if cars_with_debt else None
        if car_min_debt:
            logger.debug(f"Автомобиль с минимальным долгом: {car_min_debt.plate_number}, долг: {car_min_debt.total_debt}")

        total_system_debt = Invoice.objects.aggregate(
            total=Sum(F('accrued_amount') - F('paid_amount'))
        )['total'] or 0
        logger.info(f"Общий долг по системе: {total_system_debt}")

        context = {
            'cars_with_multiple_owners': cars_with_multiple_owners,
            'top_debtor': top_debtor,
            'last_payment_date': last_payment_date,
            'car_min_debt': car_min_debt,
            'total_system_debt': total_system_debt,
        }

        return render(request, 'admin/custom_statistics.html', context)
    except Exception as e:
        logger.error(f"Ошибка при формировании статистики администратора: {str(e)}", exc_info=True)
        raise


def services_view(request):
    """Отображается для User без регистрации: Инфо о парковочных местах и услугах с фильтрацией по цене"""
    logger.debug("Загрузка страницы услуг")
    try:
        spots = ParkingSpot.objects.all()
        services = Service.objects.all()
        promocodes = PromoCode.objects.filter(is_active=True)

        max_price = request.GET.get('max_price')
        if max_price:
            logger.debug(f"Применен фильтр по максимальной цене: {max_price}")
            spots = spots.filter(price__lte=max_price)
            services = services.filter(price__lte=max_price)

        context = {
            'spots': spots,
            'services': services,
            'promocodes': promocodes,
            'max_price': max_price
        }
        return render(request, 'parking/services.html', context)
    except Exception as e:
        logger.error(f"Ошибка при загрузке страницы услуг: {str(e)}")
        raise


def reviews_view(request):
    """Отзывы: список отзывов и возможность добавить свой (только для авторизованных)"""
    logger.debug("Загрузка страницы отзывов")
    try:
        reviews = Review.objects.order_by('-created_at')

        if request.method == 'POST' and request.user.is_authenticated:
            rating = request.POST.get('rating')
            text = request.POST.get('text')
            if rating and text:
                review = Review.objects.create(author=request.user, rating=rating, text=text)
                logger.info(f"Пользователь {request.user.username} оставил отзыв с рейтингом {rating}")
                return redirect('reviews')
            else:
                logger.warning(f"Пользователь {request.user.username} попытался оставить пустой отзыв")

        return render(request, 'parking/reviews.html', {'reviews': reviews})
    except Exception as e:
        logger.error(f"Ошибка при работе со страницей отзывов: {str(e)}")
        raise


@login_required
def dashboard_view(request):
    profile = request.user.profile
    logger.info(f"Пользователь {request.user.username} открыл личный кабинет. Баланс: {profile.balance}")

    try:
        if profile.balance > 0:
            logger.debug(f"Запуск авто-погашения для пользователя {request.user.username}")
            unpaid_invoices = Invoice.objects.filter(
                car__owners=profile,
                paid_amount__lt=F('accrued_amount')
            ).order_by('accrual_date')

            for inv in unpaid_invoices:
                if profile.balance <= 0:
                    break

                needed = inv.debt
                if profile.balance >= needed:
                    inv.paid_amount += needed
                    profile.balance -= needed
                    inv.payment_date = date.today()
                    logger.info(f"Авто-погашение: счет #{inv.id} полностью оплачен. Сумма: {needed}")
                else:
                    inv.paid_amount += profile.balance
                    logger.info(f"Авто-погашение: счет #{inv.id} частично оплачен. Сумма: {profile.balance}")
                    profile.balance = 0
                inv.save()
            profile.save()

        my_invoices = Invoice.objects.filter(car__in=profile.cars.all()).annotate(
            is_unpaid=Case(
                When(accrued_amount__gt=F('paid_amount'), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        ).order_by('-is_unpaid', '-accrual_date')

        free_spots = ParkingSpot.objects.filter(is_occupied=False)
        logger.debug(f"Найдено свободных мест: {free_spots.count()}")

        return render(request, 'parking/dashboard.html', {
            'my_cars': profile.cars.all(),
            'my_invoices': my_invoices,
            'free_spots': free_spots
        })
    except Exception as e:
        logger.error(f"Ошибка в личном кабинете пользователя {request.user.username}: {str(e)}", exc_info=True)
        raise


def register_view(request):
    logger.debug("Загрузка страницы регистрации")
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                Profile.objects.create(
                    user=user,
                    birth_date=form.cleaned_data.get('birth_date'),
                    phone=form.cleaned_data.get('phone')
                )
                login(request, user)
                messages.success(request, "Регистрация прошла успешно!")
                logger.info(f"Зарегистрирован новый пользователь: {user.username}")
                return redirect('dashboard')
            except Exception as e:
                logger.error(f"Ошибка при регистрации пользователя: {str(e)}", exc_info=True)
                messages.error(request, "Ошибка при регистрации. Попробуйте позже.")
        else:
            logger.warning(f"Неудачная попытка регистрации. Ошибки формы: {form.errors}")
    else:
        form = UserRegisterForm()
    return render(request, 'parking/register.html', {'form': form})

def about_view(request):
    logger.debug("Загрузка страницы 'О компании'")
    return render(request, 'parking/about.html')

def faq_view(request):
    logger.debug("Загрузка страницы FAQ")
    try:
        questions = FAQ.objects.all()
        logger.debug(f"Загружено {questions.count()} вопросов FAQ")
        return render(request, 'parking/faq.html', {'questions': questions})
    except Exception as e:
        logger.error(f"Ошибка при загрузке FAQ: {str(e)}")
        raise

def custom_404(request, exception):
    logger.warning(f"Страница не найдена: {request.path}")
    return render(request, '404.html', status=404)

@login_required
def add_car_view(request):
    logger.info(f"Пользователь {request.user.username} добавляет автомобиль")
    if request.method == 'POST':
        form = AddCarForm(request.POST)
        spot_id = request.POST.get('spot_id')

        if form.is_valid() and spot_id:
            try:
                with transaction.atomic():
                    car = form.save()
                    car.owners.add(request.user.profile)
                    logger.info(f"Добавлен автомобиль {car.plate_number} для пользователя {request.user.username}")

                    spot = get_object_or_404(ParkingSpot, id=spot_id)
                    if not spot.is_occupied:
                        spot.is_occupied = True
                        spot.current_car = car
                        spot.save()
                        messages.success(request, f"Авто добавлено и припарковано на место №{spot.number}")
                        logger.info(f"Автомобиль {car.plate_number} припаркован на место №{spot.number}")
                    else:
                        messages.error(request, "Это место уже занято!")
                        logger.warning(f"Попытка занять уже занятое место №{spot.number}")
                return redirect('dashboard')
            except Exception as e:
                logger.error(f"Ошибка при добавлении автомобиля: {str(e)}", exc_info=True)
                messages.error(request, "Ошибка при добавлении автомобиля")
        else:
            logger.warning(f"Невалидная форма добавления автомобиля. Ошибки: {form.errors}")
    return redirect('dashboard')


@login_required
def pay_invoice_view(request, invoice_id):
    logger.info(f"Пользователь {request.user.username} пытается оплатить счет #{invoice_id}")
    if request.method == 'POST':
        try:
            invoice = get_object_or_404(Invoice, id=invoice_id)
            profile = request.user.profile

            if not invoice.car.owners.filter(id=profile.id).exists():
                logger.warning(f"Пользователь {request.user.username} попытался оплатить чужой счет #{invoice_id}")
                messages.error(request, "Вы не можете оплатить чужой счет.")
                return redirect('dashboard')

            current_accrued = Decimal(str(invoice.accrued_amount))
            current_paid = Decimal(str(invoice.paid_amount))
            current_debt = current_accrued - current_paid

            if current_debt <= 0:
                logger.debug(f"Счет #{invoice_id} уже оплачен")
                messages.warning(request, "Этот счет уже оплачен.")
                return redirect('dashboard')

            raw_payment_amount = request.POST.get('payment_amount', '').strip()
            try:
                payment_amount = Decimal(raw_payment_amount)
                if payment_amount <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                logger.warning(f"Некорректная сумма оплаты: {raw_payment_amount}")
                messages.error(request, "Введите корректную сумму оплаты больше нуля.")
                return redirect('dashboard')

            promo_code_text = request.POST.get('promo_code', '').strip()
            discount_multiplier = Decimal('1')
            discount_message = ""

            if promo_code_text:
                try:
                    promo = PromoCode.objects.get(code__iexact=promo_code_text, is_active=True)
                    discount_percent = Decimal(str(promo.discount_percent))
                    discount_multiplier = (Decimal('100') - discount_percent) / Decimal('100')
                    discount_message = f" Применен промокод {promo.code} (Скидка {promo.discount_percent}%)."
                    logger.info(f"Применен промокод {promo.code} со скидкой {promo.discount_percent}%")
                except PromoCode.DoesNotExist:
                    logger.warning(f"Недействительный промокод: {promo_code_text}")
                    messages.error(request, "Промокод не существует или он не действителен")
                    return redirect('dashboard')

            effective_debt = (current_debt * discount_multiplier).quantize(Decimal('0.01'))

            if payment_amount >= effective_debt:
                invoice.paid_amount = invoice.accrued_amount
                invoice.payment_date = date.today()

                overpayment = payment_amount - effective_debt
                if overpayment > 0:
                    profile.balance += overpayment
                    profile.save()
                    logger.info(f"Счет #{invoice_id} оплачен полностью с переплатой {overpayment}")
                    messages.success(
                        request,
                        f"Счет успешно оплачен полностью! Долг {effective_debt} руб. закрыт. "
                        f"Переплата в размере {overpayment} руб. зачислена на ваш авансовый счет!{discount_message}"
                    )
                else:
                    logger.info(f"Счет #{invoice_id} оплачен полностью. Сумма: {payment_amount}")
                    messages.success(request,
                                     f"Счет успешно оплачен полностью! Внесено: {payment_amount} руб.{discount_message}")
            else:
                credited_to_debt = (payment_amount / discount_multiplier).quantize(Decimal('0.01'))
                invoice.paid_amount += credited_to_debt

                if invoice.paid_amount > invoice.accrued_amount:
                    invoice.paid_amount = invoice.accrued_amount

                invoice.payment_date = date.today()

                logger.info(f"Счет #{invoice_id} частично оплачен. Внесено: {payment_amount}, засчитано: {credited_to_debt}")
                messages.success(request,
                                 f"Частичная оплата счета! Внесено: {payment_amount} руб. В счет долга засчитано: {credited_to_debt} руб.{discount_message}")

            invoice.save()
        except Exception as e:
            logger.error(f"Ошибка при оплате счета #{invoice_id}: {str(e)}", exc_info=True)
            messages.error(request, "Произошла ошибка при оплате счета")

    return redirect('dashboard')


@login_required
def delete_car_view(request, car_id):
    profile = request.user.profile
    logger.info(f"Пользователь {request.user.username} пытается удалить автомобиль #{car_id}")
    try:
        car = get_object_or_404(Car, id=car_id, owners=profile)

        if request.method == 'POST':
            with transaction.atomic():
                spot = ParkingSpot.objects.filter(current_car=car).first()
                if spot:
                    spot.is_occupied = False
                    spot.current_car = None
                    spot.save()
                    logger.info(f"Освобождено парковочное место №{spot.number}")

                car.delete()
                messages.success(request, "Автомобиль успешно удален, парковочное место освобождено.")
                logger.info(f"Автомобиль #{car_id} ({car.plate_number}) успешно удален")
    except Exception as e:
        logger.error(f"Ошибка при удалении автомобиля #{car_id}: {str(e)}", exc_info=True)
        messages.error(request, "Ошибка при удалении автомобиля")

    return redirect('dashboard')

@login_required
def employee_dashboard_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = None

    if not (request.user.is_superuser or (profile and profile.is_employee)):
        logger.warning(f"Пользователь {request.user.username} попытался получить доступ к панели сотрудника без прав")
        raise PermissionDenied("Доступ только для сотрудников.")

    logger.info(f"Сотрудник {request.user.username} открыл панель управления")

    try:
        search_query = request.GET.get('search', '').strip()
        sort_by = request.GET.get('sort', 'username')

        clients_qs = Profile.objects.filter(is_employee=False).select_related('user')

        if search_query:
            clients_qs = clients_qs.filter(
                Q(user__username__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
            logger.debug(f"Поиск клиентов по запросу: '{search_query}', найдено: {clients_qs.count()}")

        if sort_by == 'username_desc':
            clients_qs = clients_qs.order_by('-user__username')
        elif sort_by == 'balance_asc':
            clients_qs = clients_qs.order_by('balance')
        elif sort_by == 'balance_desc':
            clients_qs = clients_qs.order_by('-balance')
        else:
            clients_qs = clients_qs.order_by('user__username')

        total_sales = Invoice.objects.aggregate(total=Sum('paid_amount'))['total'] or 0

        all_payments = list(Invoice.objects.filter(paid_amount__gt=0).values_list('paid_amount', flat=True))
        sales_metrics = {'mean': 0, 'median': 0, 'mode': 0}
        if all_payments:
            all_payments_float = [float(x) for x in all_payments]
            sales_metrics['mean'] = round(statistics.mean(all_payments_float), 2)
            sales_metrics['median'] = round(statistics.median(all_payments_float), 2)
            try:
                sales_metrics['mode'] = round(statistics.mode(all_payments_float), 2)
            except statistics.StatisticsError:
                sales_metrics['mode'] = "Все уникальны"

        client_birth_dates = Profile.objects.filter(is_employee=False).values_list('birth_date', flat=True)
        ages = []
        today = date.today()
        for b_date in client_birth_dates:
            if b_date:
                age = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
                ages.append(age)

        age_metrics = {'mean': 0, 'median': 0}
        if ages:
            age_metrics['mean'] = round(statistics.mean(ages), 1)
            age_metrics['median'] = round(statistics.median(ages), 1)

        popular_spot = ParkingSpot.objects.annotate(usage_count=Count('invoice')).order_by('-usage_count').first()
        profitable_spot = ParkingSpot.objects.annotate(revenue=Sum('invoice__paid_amount')).order_by('-revenue').first()

        sales_stats = Invoice.objects.aggregate(
            total_revenue=Sum('paid_amount'),
            total_accrued=Sum('accrued_amount'),
            total_debt=Sum(F('accrued_amount') - F('paid_amount'))
        )
        recent_payments = Invoice.objects.filter(paid_amount__gt=0).order_by('-payment_date')[:10]

        chart_age_base64 = ""
        chart_sales_base64 = ""

        try:
            if ages:
                fig, ax = plt.subplots(figsize=(5, 3.5))
                ax.hist(ages, bins=5, color='skyblue', edgecolor='black')
                ax.set_title('Распределение клиентов по возрастам')
                ax.set_xlabel('Возраст (лет)')
                ax.set_ylabel('Кол-во клиентов')
                fig.tight_layout()

                buffer = io.BytesIO()
                fig.savefig(buffer, format='png')
                buffer.seek(0)
                chart_age_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                plt.close(fig)
                logger.debug("График распределения возрастов сгенерирован")

            sales_by_date = Invoice.objects.filter(paid_amount__gt=0, payment_date__isnull=False) \
                .values('payment_date') \
                .annotate(daily_total=Sum('paid_amount')) \
                .order_by('payment_date')

            if sales_by_date:
                dates_list = [item['payment_date'].strftime('%d/%m') for item in sales_by_date]
                amounts_list = [float(item['daily_total']) for item in sales_by_date]

                fig, ax = plt.subplots(figsize=(5, 3.5))
                ax.plot(dates_list, amounts_list, marker='o', color='green', linestyle='-', linewidth=2)
                ax.set_title('Динамика доходов по датам')
                ax.set_xlabel('Дата')
                ax.set_ylabel('Сумма (руб)')
                ax.grid(True, linestyle='--', alpha=0.6)
                fig.tight_layout()

                buffer = io.BytesIO()
                fig.savefig(buffer, format='png')
                buffer.seek(0)
                chart_sales_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                plt.close(fig)
                logger.debug("График динамики доходов сгенерирован")

        except Exception as e:
            logger.error(f"Ошибка генерации графиков: {str(e)}", exc_info=True)

        context = {
            'sales_stats': sales_stats,
            'recent_payments': recent_payments,
            'clients_alphabetical': clients_qs,
            'total_sales': total_sales,
            'sales_metrics': sales_metrics,
            'age_metrics': age_metrics,
            'popular_spot': popular_spot,
            'profitable_spot': profitable_spot,
            'chart_age': chart_age_base64,
            'chart_sales': chart_sales_base64,
            'search_query': search_query,
            'sort_by': sort_by
        }
        return render(request, 'parking/employee_dashboard.html', context)
    except Exception as e:
        logger.error(f"Ошибка в панели сотрудника: {str(e)}", exc_info=True)
        raise

def home_view(request):
    logger.debug("Загрузка главной страницы с дополнительными данными")
    try:
        latest_article = Article.objects.order_by('-created_at').first()

        joke = "Шутка загружается"
        api_key = 'YVepLoH8VLrdmp1e9i1WUHc1BAYmKJXEFHxfRPr8'
        joke_url = 'https://api.api-ninjas.com/v1/dadjokes'
        try:
            response = requests.get(joke_url, headers={'X-Api-Key': api_key}, timeout=5)
            if response.status_code == 200:
                joke = response.json()[0]['joke']
                logger.debug("Шутка успешно загружена")
        except Exception as e:
            logger.warning(f"Не удалось загрузить шутку: {str(e)}")
            joke = "Не удалось загрузить шутку."

        weather = {}
        weather_url = 'https://api.open-meteo.com/v1/forecast?latitude=53.9&longitude=27.5&current_weather=true'
        try:
            w_response = requests.get(weather_url, timeout=5)
            if w_response.status_code == 200:
                data = w_response.json()['current_weather']
                weather = {
                    'temp': data['temperature'],
                    'wind': data['windspeed']
                }
                logger.debug(f"Погода загружена: {weather['temp']}°C")
        except Exception as e:
            logger.warning(f"Не удалось загрузить погоду: {str(e)}")
            weather = None

        utc_now = datetime.now(dt_timezone.utc)
        user_now = django_timezone.localtime(utc_now)

        now = datetime.now()
        cal = calendar.TextCalendar(calendar.MONDAY)
        html_cal = cal.formatmonth(now.year, now.month)

        context = {
            'article': latest_article,
            'joke': joke,
            'weather': weather,
            'utc_time': utc_now.strftime("%d/%m/%Y %H:%M:%S"),
            'user_time': user_now.strftime("%d/%m/%Y %H:%M:%S"),
            'user_tz': django_timezone.get_current_timezone_name(),
            'html_cal': html_cal,
            'current_date': now.strftime("%d/%m/%Y")
        }
        return render(request, 'parking/home.html', context)
    except Exception as e:
        logger.error(f"Ошибка при загрузке главной страницы: {str(e)}", exc_info=True)
        raise


def contacts_view(request):
    logger.debug("Загрузка страницы контактов")
    try:
        employees = EmployeeContact.objects.all()
        logger.debug(f"Загружено {employees.count()} контактов сотрудников")
        return render(request, 'parking/contacts.html', {'employees': employees})
    except Exception as e:
        logger.error(f"Ошибка при загрузке контактов: {str(e)}")
        raise


def privacy_policy_view(request):
    logger.debug("Загрузка страницы политики конфиденциальности")
    return render(request, 'parking/privacy_policy.html')


def vacancies_view(request):
    logger.debug("Загрузка страницы вакансий")
    try:
        vacancies = Vacancy.objects.filter(is_active=True)
        logger.debug(f"Загружено {vacancies.count()} активных вакансий")
        return render(request, 'parking/vacancies.html', {'vacancies': vacancies})
    except Exception as e:
        logger.error(f"Ошибка при загрузке вакансий: {str(e)}")
        raise

def about_view(request):
    logger.debug("Загрузка страницы 'О компании'")
    try:
        about_info = AboutCompany.objects.first()
        if about_info:
            logger.debug("Информация о компании загружена")
        context = {
            'about_info': about_info
        }
        return render(request, 'parking/about.html', context)
    except Exception as e:
        logger.error(f"Ошибка при загрузке информации о компании: {str(e)}")
        raise

@login_required
def check_promocode_view(request):
    promo_code_text = request.GET.get('promo_code', '').strip()
    invoice_id = request.GET.get('invoice_id')

    logger.debug(f"Проверка промокода '{promo_code_text}' для счета #{invoice_id}")

    if not invoice_id:
        logger.warning("Не указан ID счета при проверке промокода")
        return JsonResponse({'success': False, 'message': 'Не указан ID счета.'})

    try:
        invoice = Invoice.objects.get(id=invoice_id)
    except Invoice.DoesNotExist:
        logger.error(f"Счет #{invoice_id} не найден при проверке промокода")
        return JsonResponse({'success': False, 'message': 'Счет не найден.'})

    current_debt = Decimal(str(invoice.accrued_amount)) - Decimal(str(invoice.paid_amount))

    if not promo_code_text:
        return JsonResponse({
            'success': True,
            'discount_percent': 0,
            'final_amount': float(current_debt)
        })

    try:
        promo = PromoCode.objects.get(code__iexact=promo_code_text, is_active=True)
        discount_percent = Decimal(str(promo.discount_percent))
        discount_multiplier = (Decimal('100') - discount_percent) / Decimal('100')
        final_amount = current_debt * discount_multiplier
        final_amount = final_amount.quantize(Decimal('0.01'))

        logger.info(f"Промокод {promo.code} применен, скидка {discount_percent}%, итоговая сумма: {final_amount}")
        return JsonResponse({
            'success': True,
            'discount_percent': promo.discount_percent,
            'final_amount': float(final_amount)
        })
    except PromoCode.DoesNotExist:
        logger.warning(f"Промокод '{promo_code_text}' не найден или неактивен")
        return JsonResponse({
            'success': False,
            'message': 'Промокод не существует или он не действителен'
        })


@staff_member_required
def add_parking_spot_view(request):
    logger.info(f"Администратор {request.user.username} добавляет парковочное место")
    if request.method == 'POST':
        form = AddParkingSpotForm(request.POST)
        if form.is_valid():
            spot = form.save()
            messages.success(request, f"Парковочное место №{form.cleaned_data['number']} успешно добавлено!")
            logger.info(f"Добавлено новое парковочное место №{spot.number}, цена: {spot.price}")
        else:
            messages.error(request, "Ошибка при добавлении места. Проверьте правильность заполнения полей.")
            logger.warning(f"Ошибка при добавлении парковочного места. Ошибки формы: {form.errors}")

    return redirect('services')


@staff_member_required
def edit_parking_spot_price_view(request, spot_id):
    logger.info(f"Администратор {request.user.username} изменяет цену места #{spot_id}")
    if request.method == 'POST':
        try:
            spot = get_object_or_404(ParkingSpot, id=spot_id)
            raw_price = request.POST.get('price', '').strip()

            new_price = Decimal(raw_price)
            if new_price <= 0:
                raise ValueError

            old_price = spot.price
            spot.price = new_price
            spot.save()
            messages.success(request, f"Цена для места №{spot.number} успешно изменена на {new_price} руб/мес.")
            logger.info(f"Цена места №{spot.number} изменена с {old_price} на {new_price}")
        except (ValueError, TypeError):
            logger.warning(f"Некорректная цена: {raw_price}")
            messages.error(request, "Введите корректную цену больше нуля.")
        except Exception as e:
            logger.error(f"Ошибка при изменении цены места #{spot_id}: {str(e)}")
            messages.error(request, "Ошибка при изменении цены")

    return redirect('services')


@staff_member_required
def delete_parking_spot_view(request, spot_id):
    logger.info(f"Администратор {request.user.username} удаляет парковочное место #{spot_id}")
    if request.method == 'POST':
        try:
            spot = get_object_or_404(ParkingSpot, id=spot_id)
            spot_number = spot.number
            spot.delete()
            messages.success(request, f"Парковочное место №{spot_number} успешно удалено из системы.")
            logger.info(f"Парковочное место №{spot_number} успешно удалено")
        except Exception as e:
            logger.error(f"Ошибка при удалении места #{spot_id}: {str(e)}")
            messages.error(request, "Ошибка при удалении парковочного места")

    return redirect('services')