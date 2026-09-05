from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0006_translate_store_content_to_english")]

    operations = [
        migrations.AddField(model_name="sitesettings", name="address_ar", field=models.CharField(blank=True, max_length=255, verbose_name="العنوان بالعربية")),
        migrations.AddField(model_name="sitesettings", name="footer_text_ar", field=models.CharField(blank=True, max_length=255, verbose_name="نص التذييل بالعربية")),
        migrations.AddField(model_name="sitesettings", name="shipping_message_ar", field=models.CharField(blank=True, max_length=160, verbose_name="رسالة الشحن بالعربية")),
    ]
