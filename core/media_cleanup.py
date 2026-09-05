from django.db.models.signals import post_delete
from django.dispatch import receiver


def _delete_file(field_file):
    if field_file and field_file.name and field_file.storage.exists(field_file.name):
        field_file.storage.delete(field_file.name)


def register_media_cleanup(model, field_names):
    @receiver(post_delete, sender=model, weak=False, dispatch_uid=f"delete_{model._meta.label_lower}_media")
    def delete_model_media(sender, instance, **kwargs):
        for field_name in field_names:
            _delete_file(getattr(instance, field_name, None))

    return delete_model_media
