from __future__ import absolute_import
from datetime import datetime, timedelta
from django.conf import settings
from celery import shared_task
from bets.models import *

@shared_task(name='bidding_deadline')
def bidding_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if not b.is_event():
        if b.is_desert():
            b.closed_desert()
        else:
            b.event()

@shared_task(name='event_deadline')
def event_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    b.resolving()

@shared_task(name='resolving_deadline')
def resolving_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.is_resolving():
        if not b.claim:
            b.claim = Bet.CLAIM_LOST
        b.complaining()

@shared_task(name='complaining_deadline')
def complaining_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.is_complaining():
        if not b.accepted_bid.claim:
            b.closed_ok()
        else:
            b.arbitrating()

@shared_task(name='arbitrating_deadline')
def arbitrating_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.is_arbitrating():
        b.closed_conflict()
