from __future__ import absolute_import
from datetime import datetime, timedelta
from django.conf import settings
from celery import shared_task
from bets.models import *
from .models import *

@shared_task(name='send_invite_notifications')
def send_invite_notifications(bet_id=None, **kwargs):
    if settings.GENERATE_NOTIFICATIONS:
        b = Bet.objects.get(pk=bet_id)
        for r in b.recipients.all():
            n = NotificationFactory.bet_received(r, b)
            n.save()
            n.send_notification_email()