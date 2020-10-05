from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class HelpdeskConfig(AppConfig):
    name = 'apps.helpdesk'

    def ready(self):
        from utils.generals import get_model
        from apps.helpdesk.signals import assign_save_handler

        Assign = get_model('helpdesk', 'Assign')

        post_save.connect(assign_save_handler, sender=Assign,
                          dispatch_uid='assign_save_signal')
