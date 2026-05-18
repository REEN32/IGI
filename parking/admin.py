from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Sum, Min, F
from django.utils.html import format_html
from .models import Profile, Car, ParkingSpot, Invoice, ServiceCategory, Service, PromoCode, Review, Article, FAQ
from .models import EmployeeContact, Vacancy

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Дополнительная информация (Профиль)'
    fields = ('phone', 'birth_date', 'is_employee', 'balance')


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = BaseUserAdmin.list_display + ('get_is_employee',)

    def get_is_employee(self, instance):
        return instance.profile.is_employee

    get_is_employee.short_description = 'Сотрудник'
    get_is_employee.boolean = True


admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.site_header = "Управление Автостоянкой 'AutoCar'"
admin.site.index_title = "Панель управления"


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'plate_number', 'display_owners')
    search_fields = ('brand', 'model', 'plate_number')
    filter_horizontal = ('owners',)

    def display_owners(self, obj):
        return ", ".join([owner.user.get_full_name() or owner.user.username for owner in obj.owners.all()])

    display_owners.short_description = 'Владельцы'


@admin.register(ParkingSpot)
class ParkingSpotAdmin(admin.ModelAdmin):
    list_display = ('number', 'price', 'is_occupied', 'current_car')
    list_filter = ('is_occupied',)
    search_fields = ('number',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'car', 'accrual_date', 'payment_date', 'accrued_amount', 'paid_amount', 'get_debt')
    list_filter = ('accrual_date', 'payment_date')
    search_fields = ('car__plate_number',)

    def get_debt(self, obj):
        debt = obj.debt
        if debt > 0:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', debt)
        elif debt < 0:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', debt)
        return debt

    get_debt.short_description = 'Долг'

from .models import AboutCompany

@admin.register(AboutCompany)
class AboutCompanyAdmin(admin.ModelAdmin):
    list_display = ('title', 'founded_year')

    def has_add_permission(self, request):
        return AboutCompany.objects.count() == 0


admin.site.register(ServiceCategory)
admin.site.register(Service)
admin.site.register(PromoCode)
admin.site.register(Review)
admin.site.register(Article)
admin.site.register(FAQ)
admin.site.register(EmployeeContact)
admin.site.register(Vacancy)

