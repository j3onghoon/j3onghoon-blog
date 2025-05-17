def set_image(instance, image_field, file, **kwargs):
    from .models import FileType
    image = getattr(instance, image_field)
    if image:
        image.delete()

    return instance.add_attachment(file, file_type=FileType.IMAGE, **kwargs)
