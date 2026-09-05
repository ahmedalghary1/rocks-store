from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0004_alter_category_options")]

    operations = [
        migrations.AddField(model_name="category", name="name_ar", field=models.CharField(blank=True, max_length=120, verbose_name="الاسم بالعربية")),
        migrations.AddField(model_name="category", name="description_ar", field=models.TextField(blank=True, verbose_name="الوصف بالعربية")),
        migrations.AddField(model_name="product", name="name_ar", field=models.CharField(blank=True, max_length=180, verbose_name="الاسم بالعربية")),
        migrations.AddField(model_name="product", name="short_description_ar", field=models.CharField(blank=True, max_length=260, verbose_name="الوصف المختصر بالعربية")),
        migrations.AddField(model_name="product", name="description_ar", field=models.TextField(blank=True, verbose_name="الوصف بالعربية")),
        migrations.AddField(model_name="product", name="meta_title_ar", field=models.CharField(blank=True, max_length=180, verbose_name="عنوان محركات البحث بالعربية")),
        migrations.AddField(model_name="product", name="meta_description_ar", field=models.CharField(blank=True, max_length=260, verbose_name="وصف محركات البحث بالعربية")),
        migrations.AddField(model_name="productimage", name="alt_text_ar", field=models.CharField(blank=True, max_length=180, verbose_name="النص البديل بالعربية")),
        migrations.AddField(model_name="productspecification", name="name_ar", field=models.CharField(blank=True, max_length=100, verbose_name="اسم الخاصية بالعربية")),
        migrations.AddField(model_name="productspecification", name="value_ar", field=models.CharField(blank=True, max_length=180, verbose_name="القيمة بالعربية")),
        migrations.AddField(model_name="productattribute", name="name_ar", field=models.CharField(blank=True, max_length=80, verbose_name="الاسم بالعربية")),
        migrations.AddField(model_name="productvariant", name="label_ar", field=models.CharField(blank=True, max_length=120, verbose_name="اسم الخيار بالعربية")),
    ]
