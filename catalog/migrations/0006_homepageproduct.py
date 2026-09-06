import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0005_bilingual_catalog_content")]

    operations = [
        migrations.CreateModel(
            name="HomepageProduct",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("product", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="homepage_placement", to="catalog.product")),
            ],
            options={"verbose_name": "Homepage product", "verbose_name_plural": "Homepage products", "ordering": ("sort_order", "pk")},
        ),
    ]
