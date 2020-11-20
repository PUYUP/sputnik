import uuid

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db import models

from utils.generals import random_string
from apps.helpdesk.utils.constants import PAYMENT_STATUS, PENDING


class AbstractInvoice(models.Model):
    """
    Invoice will has multiple assigned
    So Client can pay all with one action
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='client_invoice')
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='consultant_invoice')
    reservation = models.ForeignKey('helpdesk.Reservation', on_delete=models.CASCADE,
                                    related_name='invoice')

    number = models.CharField(max_length=255, editable=False, unique=True, null=True)
    status = models.CharField(choices=PAYMENT_STATUS, default=PENDING, max_length=15)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")

    def __str__(self):
        return self.consultant.username

    def save(self, *args, **kwargs):
        if not self.pk:
            rand = random_string(8)
            now = timezone.datetime.now()
            timestamp = timezone.datetime.timestamp(now)
            number = 'INV{}{}'.format(rand, int(timestamp))

            self.number = number
        super().save(*args, **kwargs)


class AbstractInvoiceItem(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    invoice = models.ForeignKey('helpdesk.Invoice', on_delete=models.CASCADE,
                                related_name='invoice_item')
    reservation_item = models.ForeignKey('helpdesk.ReservationItem', on_delete=models.CASCADE,
                                         related_name='invoice_item')
    assign = models.ForeignKey('helpdesk.Assign', on_delete=models.CASCADE,
                               related_name='invoice_item')
    assigned = models.OneToOneField('helpdesk.Assigned', on_delete=models.CASCADE,
                                    related_name='invoice_item')

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")

    def __str__(self):
        return self.reservation_item.number
