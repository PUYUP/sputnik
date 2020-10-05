import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from utils.validators import IDENTIFIER_VALIDATOR, non_python_keyword
from ..utils.constants import SKILL_LEVELS, SKILLED


class AbstractExpertise(models.Model):
    # mapping :User with :Skill as :Expertise
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='expertises', null=False)
    skill = models.ForeignKey('master.Skill', related_name='expertises',
                              on_delete=models.CASCADE, null=False,
                              limit_choices_to={'is_active': True})
    level = models.CharField(choices=SKILL_LEVELS, default=SKILLED, max_length=25,
                             validators=[IDENTIFIER_VALIDATOR, non_python_keyword])
    description = models.TextField(null=True, blank=True,
                                   help_text=_("What you doing with this Expertise"))

    class Meta:
        abstract = True
        app_label = 'resume'
        ordering = ['-create_date']
        verbose_name = _("Expertise")
        verbose_name_plural = _("Expertises")
        constraints = [
            models.UniqueConstraint(fields=['user', 'skill'], name='unique_user_skill')
        ]

    def __str__(self):
        return '{0}'.format(self.skill.label)
