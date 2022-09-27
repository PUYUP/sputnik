import os

from django.db import transaction


@transaction.atomic
def attachment_delete_handler(sender, instance, using, **kwargs):
    file = getattr(instance, 'file', None)
    if file:
        if os.path.isfile(file.path):
            os.remove(file.path)
