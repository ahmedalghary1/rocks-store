from django.db import migrations


ARABIC_FOOTER_TEXT = "نقود الطريق نحو المستقبل."
ENGLISH_FOOTER_TEXT = "Powering a cleaner tomorrow."


def fix_bilingual_footer_text(apps, schema_editor):
    SiteSettings = apps.get_model("core", "SiteSettings")
    for site_settings in SiteSettings.objects.filter(footer_text=ARABIC_FOOTER_TEXT):
        site_settings.footer_text = ENGLISH_FOOTER_TEXT
        update_fields = ["footer_text"]
        if not site_settings.footer_text_ar:
            site_settings.footer_text_ar = ARABIC_FOOTER_TEXT
            update_fields.append("footer_text_ar")
        site_settings.save(update_fields=update_fields)


class Migration(migrations.Migration):
    dependencies = [("core", "0007_bilingual_site_settings")]

    operations = [migrations.RunPython(fix_bilingual_footer_text, migrations.RunPython.noop)]
