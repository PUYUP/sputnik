import os

from django.db import transaction


@transaction.atomic
def attachment_delete_handler(sender, instance, using, **kwargs):
    attach_file = getattr(instance, 'attach_file', None)
    if attach_file:
        if os.path.isfile(attach_file.path):
            os.remove(attach_file.path)
