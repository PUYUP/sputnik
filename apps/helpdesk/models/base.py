import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class AbstractExpertise(models.Model):
    # mapping :User with :Topic as :Expertise
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='expertises', null=False)
    topic = models.ForeignKey('helpdesk.Topic', related_name='expertises',
                              on_delete=models.CASCADE, null=False,
                              limit_choices_to={'is_active': True})

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Expertise")
        verbose_name_plural = _("Expertises")
        constraints = [
            models.UniqueConstraint(fields=['user', 'topic'], name='unique_user_topic')
        ]

    def __str__(self):
        return '{0}'.format(self.topic.subject)
