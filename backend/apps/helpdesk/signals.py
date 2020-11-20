from django.db import transaction

from utils.generals import get_model
from apps.helpdesk.utils.constants import ACCEPT

ScheduleTerm = get_model('helpdesk', 'ScheduleTerm')
Respond = get_model('helpdesk', 'Respond')
Assign = get_model('helpdesk', 'Assign')
Assigned = get_model('helpdesk', 'Assigned')
Invoice = get_model('helpdesk', 'Invoice')
InvoiceItem = get_model('helpdesk', 'InvoiceItem')


@transaction.atomic
def schedule_save_handler(sender, instance, created, **kwargs):
    if not hasattr(instance, 'schedule_term'):
        ScheduleTerm.objects.create(schedule=instance)


@transaction.atomic
def reservation_save_handler(sender, instance, created, **kwargs):
    """
    if created:
        client = instance.user
        consultant = instance.consultant
        reservation_item = instance.reservation_item.all()

        if reservation_item:
            assign_create = list()

            for item in reservation_item:
                o = Assign(user=client, consultant=consultant,
                           reservation=instance, reservation_item=item)
                assign_create.append(o)
            
            if assign_create:
                try:
                    Assign.objects.bulk_create(assign_create, ignore_conflicts=False)
                except Exception as e:
                    print(e)
    """
    pass


@transaction.atomic
def reservationitem_save_handler(sender, instance, created, **kwargs):
    if created:
        reservation = instance.reservation
        client = reservation.client
        consultant = reservation.consultant

        Assign.objects.create(client=client, consultant=consultant,
                              reservation=reservation, reservation_item=instance)


@transaction.atomic
def assign_save_handler(sender, instance, created, **kwargs):
    if not created:
        if instance.status == ACCEPT:
            consultant = instance.consultant
            client = instance.client
            reservation = instance.reservation
            reservation_item = instance.reservation_item

            # Create invoice.
            assigned = Assigned.objects.create(client=client, consultant=consultant, assign=instance)
            invoice, _created = Invoice.objects.get_or_create(client=client, consultant=consultant,
                                                              reservation=reservation)
            InvoiceItem.objects.create(invoice=invoice, reservation_item=reservation_item,
                                       assign=instance, assigned=assigned)
        else:
            assigneds = Assigned.objects.filter(assign__uuid=instance.uuid)
            if assigneds.exists():
                assigneds.delete()
    
