from datetime import datetime, timedelta
from celery.task import task
from bets.models import *

@task
def bidding_deadline(bet_id=None, **kwargs):
    '''Task that is executed when a bet reaches
    the bidding deadline, passing from the bidding
    state to the event state'''
    b = Bet.objects.get(pk=bet_id)
    if b.bet_state == 'bidding':
        if not b.accepted_bid:
            b.bet_state = 'closed'
        else:
            b.bet_state = 'event'
            event_deadline.apply_asinc(b.id, eta=b.event_deadline)
        b.save()
    else:
        # This shouldn't be possible
        pass
    # TODO send notifications

@task
def event_deadline(bet_id=None, **kwargs):
    '''Task that is executed when a bet reaches
    the event deadline, passing from the event
    state to the resolving state'''
    b = Bet.objects.get(pk=bet_id)
    if b.bet_state == 'event':
        b.bet_state = 'resolving'
        b.save()
        resolving_deadline.apply_asinc(b.id, eta=b.event_deadline)
    else:
        # This shouldn't be possible
        pass
    # TODO send notifications

@task
def resolving_deadline(bet_id=None, **kwargs):
    '''Task that is executed when a bet reaches
    the resolving deadline, passing from the resolving
    state to the complaining or closed state'''
    b = Bet.objects.get(pk=bet_id)
    if b.bet_state == 'resolving':
        if b.claim == 'won' and b.accepted_bid.claim == 'won':
            b.bet_state = 'complaining'
        else:
            if b.claim == 'won':
                b.user.points += b.amount + b.accepted_bid.amount
            elif b.accepted_bid.claim == 'won':
                b.accepted_bid.user.points += b.amount + b.accepted_bid.amount
            else:
                b.user.coins_available += b.amount
                b.accepted_bid.user.coins_available += b.accepted_bid.amount
            b.user.coins_at_stake -= b.amount
            b.accepted_bid.user.coins_at_stake -= b.accepted_bid.amount
            b.bet_state = 'closed'
            b.user.save()
            b.accepted_bid.user.save()
        b.save()
    else:
        # This shouldn't be possible
        pass
    # TODO send notifications


