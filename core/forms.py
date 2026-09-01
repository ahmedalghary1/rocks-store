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
            raise forms.ValidationError("أدخل رقم هاتف صحيحًا.")
        return phone

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("website"):
            raise forms.ValidationError("تعذر إرسال الرسالة.")
        return cleaned


class NewsletterForm(forms.Form):
    email = forms.EmailField(label="البريد الإلكتروني", max_length=254)
