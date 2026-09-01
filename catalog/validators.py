from django.core.exceptions import ValidationError


MAX_IMAGE_SIZE = 5 * 1024 * 1024


def validate_image_size(image):
    if image.size > MAX_IMAGE_SIZE:
        raise ValidationError("حجم الصورة يجب ألا يتجاوز 5 ميجابايت.")
