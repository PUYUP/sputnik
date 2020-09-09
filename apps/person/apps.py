from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class PersonConfig(AppConfig):
    name = 'apps.person'

    def ready(self):
        from django.conf import settings
        from utils.generals import get_model
        from apps.person.signals import (
            user_save_handler,
            otpcode_save_handler,
            education_attachment_delete_handler,
            experience_attachment_delete_handler,
            certificate_attachment_delete_handler
        )

        OTPFactory = get_model('person', 'OTPFactory')
        Account = get_model('person', 'Account')
        EducationAttachment = get_model('person', 'EducationAttachment')
        ExperienceAttachment = get_model('person', 'ExperienceAttachment')
        CertificateAttachment = get_model('person', 'CertificateAttachment')

        post_save.connect(user_save_handler, sender=settings.AUTH_USER_MODEL,
                          dispatch_uid='user_save_signal')

        post_save.connect(otpcode_save_handler, sender=OTPFactory,
                          dispatch_uid='otpcode_save_signal')

        post_delete.connect(education_attachment_delete_handler, sender=EducationAttachment,
                            dispatch_uid='education_attachment_delete_signal')

        post_delete.connect(experience_attachment_delete_handler, sender=ExperienceAttachment,
                            dispatch_uid='experience_attachment_delete_signal')

        post_delete.connect(certificate_attachment_delete_handler, sender=CertificateAttachment,
                            dispatch_uid='certificate_attachment_delete_signal')
