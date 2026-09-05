from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0006_alter_coupon_discount_type_and_more")]

    operations = [
        migrations.AddField(model_name="orderitem", name="product_name_ar", field=models.CharField(blank=True, max_length=180)),
        migrations.AddField(model_name="shippingzone", name="name_ar", field=models.CharField(blank=True, max_length=80, verbose_name="اسم المحافظة بالعربية")),
    ]
