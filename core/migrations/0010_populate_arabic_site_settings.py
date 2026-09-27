from django.db import migrations


def populate_arabic_site_settings(apps, schema_editor):
    SiteSettings = apps.get_model("core", "SiteSettings")
    known_values = {
        "address": ("Cairo, Egypt", "address_ar", "القاهرة، مصر"),
        "footer_text": ("Powering a cleaner tomorrow.", "footer_text_ar", "نقود الطريق نحو المستقبل."),
        "shipping_message": ("Fast delivery across Egypt", "shipping_message_ar", "توصيل سريع إلى جميع أنحاء مصر"),
    }
    for english_field, (english_value, arabic_field, arabic_value) in known_values.items():
        SiteSettings.objects.filter(
            **{english_field: english_value, arabic_field: ""}
        ).update(**{arabic_field: arabic_value})


class Migration(migrations.Migration):
    dependencies = [("core", "0009_populate_arabic_catalog_content")]

    operations = [migrations.RunPython(populate_arabic_site_settings, migrations.RunPython.noop)]
