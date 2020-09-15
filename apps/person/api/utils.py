import os

from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

ALLOWED_EXTENSIONS = ['.jpeg', '.jpg', '.png', '.pdf', '.docx']


def handle_upload_attachment(instance, module, file):
    if instance and file:
        name, ext = os.path.splitext(file.name)

        fsize = file.size / 1000
        if fsize > 5000:
            raise serializers.ValidationError({'detail': _("Ukuran file maksimal 5 MB")})
    
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError({'detail': _("Jenis file tidak diperbolehkan")})

        certificate = getattr(instance, module)
        username = certificate.user.username
        title = certificate.title
        filename = '{username}_{title}'.format(username=username, title=title)
        filename_slug = slugify(filename)

        instance.attach_type = ext
        instance.attach_file.save('%s%s' % (filename_slug, ext), file, save=False)
        instance.save(update_fields=['attach_file', 'attach_type'])
