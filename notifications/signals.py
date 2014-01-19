from django.core import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django_fsm.signals import pre_transition, post_transition
from bets.models import Bet
from .models import *

'''
Listening to bet state changes to create notifications.
TODO: listen to "follow" actions from users
'''


@receiver(post_save, sender=Bet)
def bet_auto_queue_bidding_deadline_task(sender, **kwargs):
    if kwargs.get('created', False) and settings.GENERATE_NOTIFICATIONS:
        bet = kwargs.get('instance')
        for r in bet.recipients.all():
            n = NotificationFactory.bet_received(r, bet)
            n.save()

@receiver(post_transition, sender=Bet)
def bet_auto_queue_deadlines_tasks(sender, **kwargs):
    if settings.GENERATE_NOTIFICATIONS:
        bet = kwargs.get('instance')
        transition = kwargs.get('name')

        if transition == 'event':
            if bet.is_simple():
                n = NotificationFactory.bet_accepted(bet)
                n.save()
            elif bet.is_auction():
                n = NotificationFactory.bid_accepted(bet.accepted_bid)
                n.save()

        if transition == 'resolving':
            n = NotificationFactory.bet_event_finished(bet)
            n.save()

        if transition == 'complaining':
            if bet.is_simple() or bet.is_auction():
                n = NotificationFactory.bet_resolving_finished(bet)
                n.save()
            elif bet.is_lottery():
                for bid in bet.bids.all():
                    for participant in bid.participants.all():
                        n = NotificationFactory.bet_resolving_finished(bet, participant)
                        n.save()

        if transition == 'arbitrating':
            arbitrating_deadline.apply_async(args=[b.id], countdown=settings.ARBITRATING_COUNTDOWN)

        if transition == 'closed_ok':
            arbitrating_deadline.apply_async(args=[b.id], countdown=settings.ARBITRATING_COUNTDOWN)

        if transition == 'closed_desert':
            arbitrating_deadline.apply_async(args=[b.id], countdown=settings.ARBITRATING_COUNTDOWN)
            