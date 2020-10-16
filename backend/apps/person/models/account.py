import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from utils.validators import non_python_keyword, IDENTIFIER_VALIDATOR
from apps.person.utils.constants import UNDEFINED, GENDER_CHOICES


# Create your models here.
class AbstractAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='account')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    email = models.EmailField(blank=True, null=True)
    msisdn = models.CharField(blank=True, null=True, max_length=14)

    email_verified = models.BooleanField(default=False, null=True)
    msisdn_verified = models.BooleanField(default=False, null=True)

    class Meta:
        abstract = True
        app_label = 'person'
        ordering = ['-user__date_joined']
        verbose_name = _(u"Account")
        verbose_name_plural = _(u"Accounts")

    def __str__(self):
        return self.user.username

    @property
    def username(self):
        return self.user.username

    @property
    def password(self):
        return self.user.password

    def save(self, *args, **kwargs):
        self.email = self.user.email
        super().save(*args, **kwargs)


class AbstractProfile(models.Model):
    _UPLOAD_TO = 'images/user'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='profile')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    headline = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(choices=GENDER_CHOICES, blank=True, null=True,
                              default=UNDEFINED, max_length=255,
                              validators=[IDENTIFIER_VALIDATOR, non_python_keyword])
    birthdate = models.DateField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    picture = models.ImageField(upload_to=_UPLOAD_TO, max_length=500,
                                null=True, blank=True)
    picture_original = models.ImageField(upload_to=_UPLOAD_TO, max_length=500,
                                         null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'person'
        ordering = ['-user__date_joined']
        verbose_name = _(u"Profile")
        verbose_name_plural = _(u"Profiles")

    def __str__(self):
        return self.user.username

    @property
    def first_name(self):
        return self.user.first_name
