from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput, label="")

    class Meta:
        model = ContactMessage
        fields = ("name", "phone", "email", "subject", "message")

    def clean_phone(self):
        phone = self.cleaned_data["phone"].replace(" ", "")
        if len(phone) < 10 or not phone.lstrip("+").isdigit():
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("website"):
            raise forms.ValidationError("The message could not be sent.")
        return cleaned


class NewsletterForm(forms.Form):
    email = forms.EmailField(label="Email address", max_length=254)
