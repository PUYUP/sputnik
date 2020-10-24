import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from utils.validators import IDENTIFIER_VALIDATOR, non_python_keyword
from apps.resume.utils.constants import EXPERTISE_LEVELS, SKILLED

MAX_ALLOWED_EXPERTISE = 11


class AbstractExpertise(models.Model):
    # mapping :User with :Topic as :Expertise
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='expertises', null=False)
    topic = models.ForeignKey('master.Topic', related_name='expertises',
                              on_delete=models.CASCADE,
                              limit_choices_to={'is_active': True})
    level = models.CharField(choices=EXPERTISE_LEVELS, default=SKILLED, max_length=25,
                             validators=[IDENTIFIER_VALIDATOR, non_python_keyword])
    description = models.TextField(null=True, blank=True,
                                   help_text=_("What you doing with this Expertise"))
    sort_order = models.IntegerField(default=1, null=True)

    class Meta:
        abstract = True
        app_label = 'resume'
        ordering = ['-create_date']
        verbose_name = _("Expertise")
        verbose_name_plural = _("Expertises")
        constraints = [
            models.UniqueConstraint(fields=['user', 'topic'], name='unique_user_topic')
        ]

    def __str__(self):
        return '{0}'.format(self.topic.label)

    def clean(self):
        if self.topic and not self.uuid:
            c = self.__class__.objects.filter(user_id=self.user.id).count()
            if c > MAX_ALLOWED_EXPERTISE:
                raise ValidationError({'topic': _(u"Max %s topics" % MAX_ALLOWED_EXPERTISE)})

    def save(self, *args, **kwargs):
        if self.user and not self.pk:
            c = self.__class__.objects.filter(user_id=self.user.id).count()
            self.sort_order = c + 1
        super().save(*args, **kwargs)
