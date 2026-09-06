from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("marketing", "0004_alter_banner_location")]

    operations = [
        migrations.AddField(model_name="banner", name="title_ar", field=models.CharField(blank=True, max_length=160, verbose_name="العنوان بالعربية")),
        migrations.AddField(model_name="banner", name="subtitle_ar", field=models.CharField(blank=True, max_length=255, verbose_name="العنوان الفرعي بالعربية")),
        migrations.AddField(model_name="banner", name="button_text_ar", field=models.CharField(blank=True, max_length=60, verbose_name="نص الزر بالعربية")),
    ]
