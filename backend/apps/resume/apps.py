from django.apps import AppConfig
from django.db.models.signals import post_delete


class ResumeConfig(AppConfig):
    name = 'apps.resume'

    def ready(self):
        from utils.generals import get_model
        from apps.resume.signals import attachment_delete_handler

        Attachment = get_model('resume', 'Attachment')

        post_delete.connect(attachment_delete_handler, sender=Attachment,
                            dispatch_uid='attachment_delete_signal')
