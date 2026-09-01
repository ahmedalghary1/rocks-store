from django import forms
from core.models import SiteSettings
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("customer_name", "phone", "email", "second_phone", "governorate", "city", "address", "notes", "payment_method")
        labels = {"customer_name": "الاسم بالكامل", "phone": "رقم الهاتف", "email": "البريد الإلكتروني (اختياري)", "second_phone": "رقم إضافي", "governorate": "المحافظة", "city": "المدينة", "address": "العنوان بالتفصيل", "notes": "ملاحظات الطلب", "payment_method": "طريقة الدفع"}
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        site = SiteSettings.objects.first()
        if not site or not site.bank_instructions.strip():
            self.fields["payment_method"].choices = [("cod", "الدفع عند الاستلام")]
        else:
            self.fields["payment_method"].help_text = site.bank_instructions

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
