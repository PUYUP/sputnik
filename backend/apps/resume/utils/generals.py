import os

from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _

ALLOWED_EXTENSIONS = ['.jpeg', '.jpg', '.png', '.pdf', '.docx']


def handle_upload_attachment(instance, file):
    if instance and file:
        name, ext = os.path.splitext(file.name)
        filename_slug = slugify(name)
        model_name = instance.content_type.model

        instance.attach_type = ext
        instance.attach_file.save('%s-%s%s' % (model_name, filename_slug, ext), file, save=False)
        instance.label = instance.attach_file.name
        instance.save(update_fields=['label', 'attach_file', 'attach_type'])
