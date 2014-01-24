from datetime import datetime, timedelta
from django.conf import settings
from celery.task import task
from bets.models import *

@task
def bidding_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.has_bid():
        if not b.is_event():
            b.event()
    else:
        self.closed_desert()

@task
def event_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    b.resolving()

@task
def resolving_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.is_resolving():
        if not b.claim:
            b.claim = Bet.CLAIM_LOST
        b.complaining()

@task
def complaining_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.is_complaining():
        if not b.accepted_bid.claim:
            b.closed_ok()
        else:
            b.arbitrating()

@task
def arbitrating_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.is_arbitrating():
        b.closed_conflict()
