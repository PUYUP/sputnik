import logging
import smtplib

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.mail import BadHeaderError, EmailMultiAlternatives

# Celery config
from celery import shared_task


@shared_task
def send_verifycode_email(data):
    logging.info(_(u"Send VerifyCode email run"))

    to = data.get('email', None)
    passcode = data.get('passcode', None)

    if to and passcode:
        subject = _(u"Kode Verifiaksi")
        from_email = '%s <hellopuyup@gmail.com>' % (settings.APP_NAME)

        # Message
        text = _(
            "JANGAN BERIKAN KODE Kode Verifiaksi ini kepada siapapun "
            "TERMASUK PIHAK %(app_name)s. Kode Kode Verifiaksi Anda: " +
            passcode
        ) % {'app_name': settings.APP_NAME}

        html = _(
            "JANGAN BERIKAN KODE Kode Verifiaksi ini kepada siapapun "
            "TERMASUK PIHAK %(app_name)s.<br />"
            "Kode Kode Verifiaksi Anda: "
            "<strong>" + passcode + "</strong>"
            "<br /><br />"
            "Salam, <br /> <strong>%(app_name)s</strong>"
        ) % {'app_name': settings.APP_NAME}

        if subject and from_email:
            try:
                msg = EmailMultiAlternatives(subject, text, from_email, [to])
                msg.attach_alternative(html, "text/html")
                msg.send()
                logging.info(_(u"VerifyCode email success"))
            except smtplib.SMTPConnectError as e:
                logging.error('SMTPConnectError: %s' % e)
            except smtplib.SMTPAuthenticationError as e:
                logging.error('SMTPAuthenticationError: %s' % e)
            except smtplib.SMTPSenderRefused as e:
                logging.error('SMTPSenderRefused: %s' % e)
            except smtplib.SMTPRecipientsRefused as e:
                logging.error('SMTPRecipientsRefused: %s' % e)
            except smtplib.SMTPDataError as e:
                logging.error('SMTPDataError: %s' % e)
            except smtplib.SMTPException as e:
                logging.error('SMTPException: %s' % e)
            except BadHeaderError:
                logging.warning(_(u"Invalid header found"))
    else:
        logging.warning(_(u"Tried to send email to non-existing VerifyCode Code"))
