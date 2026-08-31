from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("customer_name", "phone", "second_phone", "governorate", "city", "address", "notes", "payment_method")
        labels = {"customer_name": "الاسم بالكامل", "phone": "رقم الهاتف", "second_phone": "رقم إضافي", "governorate": "المحافظة", "city": "المدينة", "address": "العنوان بالتفصيل", "notes": "ملاحظات الطلب", "payment_method": "طريقة الدفع"}
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def clean_phone(self):
        phone = self.cleaned_data["phone"].replace(" ", "")
        if len(phone) < 10 or not phone.lstrip("+").isdigit():
            raise forms.ValidationError("أدخل رقم هاتف صحيحًا.")
        return phone
