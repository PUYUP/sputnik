from django.apps import AppConfig
from django.db.models.signals import post_save


class HelpdeskConfig(AppConfig):
    name = 'apps.helpdesk'

    def ready(self):
        from utils.generals import get_model
        from apps.helpdesk.signals import (
            schedule_save_handler, 
            reservation_save_handler,
            reservationitem_save_handler,
            assign_save_handler
        )

        Reservation = get_model('helpdesk', 'Reservation')
        ReservationItem = get_model('helpdesk', 'ReservationItem')
        Schedule = get_model('helpdesk', 'Schedule')
        Assign = get_model('helpdesk', 'Assign')

        post_save.connect(reservation_save_handler, sender=Reservation,
                          dispatch_uid='reservation_save_signal')

        post_save.connect(reservationitem_save_handler, sender=ReservationItem,
                          dispatch_uid='reservationitem_save_signal')

        post_save.connect(schedule_save_handler, sender=Schedule,
                          dispatch_uid='schedule_save_signal')

        post_save.connect(assign_save_handler, sender=Assign,
                          dispatch_uid='assign_save_signal')
