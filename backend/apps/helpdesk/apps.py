from django.apps import AppConfig
from django.db.models.signals import post_save


class HelpdeskConfig(AppConfig):
    name = 'apps.helpdesk'

    def ready(self):
        from utils.generals import get_model
        from apps.helpdesk.signals import assign_save_handler, schedule_save_handler

        Assign = get_model('helpdesk', 'Assign')
        Schedule = get_model('helpdesk', 'Schedule')

        post_save.connect(assign_save_handler, sender=Assign,
                          dispatch_uid='assign_save_signal')
        post_save.connect(schedule_save_handler, sender=Schedule,
                          dispatch_uid='schedule_save_signal')
