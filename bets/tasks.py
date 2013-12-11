from datetime import datetime, timedelta
from django.conf import settings
from celery.task import task
from bets.models import *

@task
def bidding_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.has_bid():
        b.event()
        event_deadline.apply_async(args=[b.id], eta=b.event_deadline)
    else:
        self.closed_desert()

@task
def event_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    b.resolving()
    resolving_deadline.apply_async(args=[b.id], countdown=settings.RESOLVING_COUNTDOWN)

@task
def resolving_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.bet_state == Bet.STATE_RESOLVING:
        if not b.claim:
            b.claim = Bet.CLAIM_LOST
        b.complaining()
        complaining_deadline.apply_async(args=[b.id], countdown=settings.COMPLAINING_COUNTDOWN)

@task
def complaining_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.bet_state == Bet.STATE_COMPLAINING:
        if not b.accepted_bid.claim:
            b.close_ok()
        else:
            b.arbitrating()
            arbitrating_deadline.apply_async(args=[b.id], countdown=settings.ARBITRATING_COUNTDOWN)

@task
def arbitrating_deadline(bet_id=None, **kwargs):
    b = Bet.objects.get(pk=bet_id)
    if b.bet_state == Bet.STATE_ARBITRATING:
        b.closed_conflict()
