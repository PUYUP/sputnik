from django.db import transaction

from utils.generals import get_model

ScheduleTerm = get_model('helpdesk', 'ScheduleTerm')
Respond = get_model('helpdesk', 'Respond')


@transaction.atomic
def schedule_save_handler(sender, instance, created, **kwargs):
    if not hasattr(instance, 'schedule_term'):
        ScheduleTerm.objects.create(schedule=instance)
