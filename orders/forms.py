from django import forms
from .models import Order, ShippingZone


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("customer_name", "phone", "email", "second_phone", "governorate", "city", "address", "notes")
        labels = {"customer_name": "Full name", "phone": "Phone number", "email": "Email address (optional)", "second_phone": "Alternative phone", "governorate": "Governorate", "city": "City", "address": "Full address", "notes": "Order notes"}
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        zones = list(ShippingZone.objects.filter(is_active=True).values_list("name", "name"))
        self.fields["governorate"].widget = forms.Select(choices=[("", "Select a governorate")] + zones)

    def clean_phone(self):
        phone = self.cleaned_data["phone"].replace(" ", "")
        if len(phone) < 10 or not phone.lstrip("+").isdigit():
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean_second_phone(self):
        phone = self.cleaned_data.get("second_phone", "").replace(" ", "")
        if phone and (len(phone) < 10 or not phone.lstrip("+").isdigit()):
            raise forms.ValidationError("Enter a valid alternative phone number.")
        return phone

    def clean_governorate(self):
        governorate = self.cleaned_data["governorate"]
        if not ShippingZone.objects.filter(name=governorate, is_active=True).exists():
            raise forms.ValidationError("Select a governorate available for delivery.")
        return governorate


class TrackOrderForm(forms.Form):
    order_number = forms.CharField(max_length=40, label="Order number")
    phone = forms.CharField(max_length=30, label="Phone number")

    def clean_phone(self):
        return self.cleaned_data["phone"].replace(" ", "")
