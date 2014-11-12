from __future__ import absolute_import
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from celery import shared_task
from bets.models import *

@shared_task(name='bidding_deadline')
def bidding_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.is_bidding():
        b.next_state()

@shared_task(name='event_deadline')
def event_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.is_event():
        b.next_state()

@shared_task(name='resolving_deadline')
def resolving_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.is_resolving():
        b.next_state()

@shared_task(name='complaining_deadline')
def complaining_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.is_complaining():
        b.next_state()

@shared_task(name='arbitrating_deadline')
def arbitrating_deadline(bet_id=None, **kwargs):
    #b = Bet.objects.get(pk=bet_id)
    #if b.is_arbitrating():
    #    b.next_state()

@shared_task(name='missed_deadlines')
def missed_deadlines():
    for b in Bet.objects.all().bidding_deadline_missed():
        b.next_state()
    for b in Bet.objects.all().event_deadline_missed():
        b.next_state()
    for b in Bet.objects.all().resolving_deadline_missed():
        b.next_state()
    for b in Bet.objects.all().complaining_deadline_missed():
        b.next_state()
    for b in Bet.objects.all().arbitrating_deadline_missed():
        b.next_state()
