from django import forms
from django.contrib.auth.models import User
from .models import Profile
from django import forms
from .models import Car, ParkingSpot
from .models import ParkingSpot

class UserRegisterForm(forms.ModelForm):
    phone = forms.CharField(label="Телефон (+375 (29) XXX-XX-XX)")
    birth_date = forms.DateField(label="Дата рождения", widget=forms.SelectDateWidget(years=range(1950, 2010)))
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class AddCarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['brand', 'model', 'plate_number']
        labels = {
            'brand': 'Марка',
            'model': 'Модель',
            'plate_number': 'Гос. номер (например, 1234-AB7)'
        }

class AddParkingSpotForm(forms.ModelForm):
    class Meta:
        model = ParkingSpot
        fields = ['number', 'price']
        labels = {
            'number': 'Номер места',
            'price': 'Цена (руб/мес)'
        }