from __future__ import absolute_import
from datetime import datetime, timedelta
from django.conf import settings
from celery import shared_task
from bets.models import *

@shared_task(name='bidding_deadline')
def bidding_deadline(bet_id=None, **kwargs):
    print "[start] bidding deadline"
    b = Bet.objects.get(pk=bet_id)
    if not b.is_event():
        if b.is_desert():
            print "closing desert"
            b.closed_desert()
        else:
            print "event"
            b.event()
    print "[end] bidding deadline"

@shared_task(name='event_deadline')
def event_deadline(bet_id=None, **kwargs):
    print "[start] event deadline"
    b = Bet.objects.get(pk=bet_id)
    b.resolving()
    print "[end] event deadline"

@shared_task(name='resolving_deadline')
def resolving_deadline(bet_id=None, **kwargs):
    print "[start] resolving deadline"
    b = Bet.objects.get(pk=bet_id)
    if b.is_resolving():
        if not b.claim:
            b.claim = Bet.CLAIM_LOST
        print "claiming"
        b.complaining()
    print "[end] resolving deadline"

@shared_task(name='complaining_deadline')
def complaining_deadline(bet_id=None, **kwargs):
    print "[start] complaining deadline"
    b = Bet.objects.get(pk=bet_id)
    if b.is_complaining():
        if not b.accepted_bid.claim:
            print "closing ok"
            b.closed_ok()
        else:
            print "arbitrating"
            b.arbitrating()
    print "[end] complaining deadline"

@shared_task(name='arbitrating_deadline')
def arbitrating_deadline(bet_id=None, **kwargs):
    print "[start] arbitrating deadline"
    b = Bet.objects.get(pk=bet_id)
    if b.is_arbitrating():
        print "closing conflict"
        b.closed_conflict()
    print "[end] arbitrating deadline"
