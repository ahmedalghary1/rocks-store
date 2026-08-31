from django.db import migrations


def create_missing_core_tables(apps, schema_editor):
    """Repair databases whose 0001 migration was recorded before all tables existed."""
    existing_tables = set(schema_editor.connection.introspection.table_names())

    for model_name in ("SiteSettings", "ContactMessage"):
        model = apps.get_model("core", model_name)
        if model._meta.db_table not in existing_tables:
            schema_editor.create_model(model)
            existing_tables.add(model._meta.db_table)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_missing_core_tables,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
