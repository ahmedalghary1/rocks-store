from django import forms
from config.translations import translate_text
from .models import Order, ShippingZone


def resolve_shipping_zone(value):
    """Resolve stable IDs plus legacy English/Arabic option values."""
    submitted = str(value or "").strip()
    zones = ShippingZone.objects.filter(is_active=True)
    if submitted.isdigit():
        zone = zones.filter(pk=int(submitted)).first()
        if zone:
            return zone
    submitted_folded = submitted.casefold()
    return next((
        zone for zone in zones
        if submitted_folded in {
            zone.name.casefold(),
            (zone.name_ar or "").casefold(),
            translate_text(zone.name).casefold(),
        }
    ), None)


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("customer_name", "phone", "email", "second_phone", "governorate", "city", "address", "notes")
        labels = {"customer_name": "Full name", "phone": "Phone number", "email": "Email address (optional)", "second_phone": "Alternative phone", "governorate": "Governorate", "city": "City", "address": "Full address", "notes": "Order notes"}
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        zones = [(str(zone.pk), zone.display_name) for zone in ShippingZone.objects.filter(is_active=True)]
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
        submitted = self.cleaned_data["governorate"].strip()
        zone = resolve_shipping_zone(submitted)
        if not zone:
            raise forms.ValidationError("Select a governorate available for delivery.")
        self.shipping_zone = zone
        return zone.name


class TrackOrderForm(forms.Form):
    order_number = forms.CharField(max_length=40, label="Order number")
    phone = forms.CharField(max_length=30, label="Phone number")

    def clean_phone(self):
        return self.cleaned_data["phone"].replace(" ", "")
