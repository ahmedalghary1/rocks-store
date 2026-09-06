from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.forms import modelform_factory

from .registry import FIELD_LABELS


class StaffAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError("هذا الحساب لا يملك صلاحية دخول لوحة الإدارة.", code="not_staff")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "اسم المستخدم"
        self.fields["password"].label = "كلمة المرور"
        for field in self.fields.values():
            field.widget.attrs["class"] = "cp-input"


class DashboardModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.label = FIELD_LABELS.get(name, field.label)
            widget = field.widget
            current = widget.attrs.get("class", "")
            widget.attrs["class"] = f"cp-input {current}".strip()
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("rows", 5)
            if field.required:
                widget.attrs["aria-required"] = "true"


class UserControlForm(DashboardModelForm):
    new_password = forms.CharField(
        label="كلمة مرور جديدة",
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "cp-input"}),
        help_text="اتركها فارغة للاحتفاظ بكلمة المرور الحالية.",
    )
    confirm_password = forms.CharField(
        label="تأكيد كلمة المرور",
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "cp-input"}),
    )

    class Meta:
        model = User
        fields = (
            "username", "email", "first_name", "last_name", "is_active", "is_staff", "is_superuser",
            "groups", "user_permissions",
        )
        widgets = {
            "groups": forms.CheckboxSelectMultiple,
            "user_permissions": forms.SelectMultiple(attrs={"size": 14}),
        }

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("new_password")
        if not self.instance.pk and not password:
            self.add_error("new_password", "كلمة المرور مطلوبة عند إنشاء مستخدم جديد.")
        if password != cleaned.get("confirm_password"):
            self.add_error("confirm_password", "كلمتا المرور غير متطابقتين.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("new_password"):
            user.set_password(self.cleaned_data["new_password"])
        if commit:
            user.save()
            self.save_m2m()
        return user


def _formfield_callback(db_field, **kwargs):
    formfield = db_field.formfield(**kwargs)
    if not formfield:
        return formfield
    formfield.label = FIELD_LABELS.get(db_field.name, formfield.label)
    if isinstance(db_field, models.JSONField):
        formfield.widget = forms.Textarea(attrs={"rows": 7, "dir": "ltr", "class": "cp-input cp-code"})
    elif isinstance(db_field, models.DateTimeField):
        formfield.widget = forms.DateTimeInput(attrs={"type": "datetime-local", "class": "cp-input"}, format="%Y-%m-%dT%H:%M")
        formfield.input_formats = ("%Y-%m-%dT%H:%M",)
    return formfield


def form_for(config):
    if config["model"] is User:
        return UserControlForm
    base_form = modelform_factory(config["model"], form=DashboardModelForm, fields="__all__", formfield_callback=_formfield_callback)
    return base_form
