from django import forms
from .models import Order, ShippingZone


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("customer_name", "phone", "email", "second_phone", "governorate", "city", "address", "notes")
        labels = {"customer_name": "الاسم بالكامل", "phone": "رقم الهاتف", "email": "البريد الإلكتروني (اختياري)", "second_phone": "رقم إضافي", "governorate": "المحافظة", "city": "المدينة", "address": "العنوان بالتفصيل", "notes": "ملاحظات الطلب"}
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        zones = list(ShippingZone.objects.filter(is_active=True).values_list("name", "name"))
        self.fields["governorate"].widget = forms.Select(choices=[("", "اختر المحافظة")] + zones)

    def clean_phone(self):
        phone = self.cleaned_data["phone"].replace(" ", "")
        if len(phone) < 10 or not phone.lstrip("+").isdigit():
            raise forms.ValidationError("أدخل رقم هاتف صحيحًا.")
        return phone

    def clean_second_phone(self):
        phone = self.cleaned_data.get("second_phone", "").replace(" ", "")
        if phone and (len(phone) < 10 or not phone.lstrip("+").isdigit()):
            raise forms.ValidationError("أدخل رقم هاتف إضافيًا صحيحًا.")
        return phone

    def clean_governorate(self):
        governorate = self.cleaned_data["governorate"]
        if not ShippingZone.objects.filter(name=governorate, is_active=True).exists():
            raise forms.ValidationError("اختر محافظة متاحة للشحن.")
        return governorate


class TrackOrderForm(forms.Form):
    order_number = forms.CharField(max_length=40, label="رقم الطلب")
    phone = forms.CharField(max_length=30, label="رقم الهاتف")

    def clean_phone(self):
        return self.cleaned_data["phone"].replace(" ", "")
