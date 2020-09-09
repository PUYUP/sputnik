from django.db import transaction
from django.db.models import Q

from apps.helpdesk.utils.constants import ACCEPT, CANCEL


@transaction.atomic
def assign_save_handler(sender, instance, created, **kwargs):
    if instance.status == ACCEPT:
        # mark other assign status to cancel
        oldest = instance.__class__.objects \
            .filter(Q(user_id=instance.user.id)) \
            .exclude(id=instance.id)

        if oldest.exists():
            oldest.update(status=CANCEL)
