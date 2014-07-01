from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from django_fsm.signals import pre_transition, post_transition
from users.models import DareyooUser
from users.signals import new_follower
from bets.models import Bet, Bid
from .models import *


@receiver(new_follower, sender=DareyooUser)
def user_follow_notification(sender, user, follower, **kwargs):
    if settings.GENERATE_NOTIFICATIONS:
        n = NotificationFactory.new_follower(user, follower)
        n.save()
        n.send_notification_email()


@receiver(post_save, sender=Bet)
def bet_recipients_notifications(sender, **kwargs):
    if kwargs.get('created', False) and settings.GENERATE_NOTIFICATIONS:
        bet = kwargs.get('instance')
        for r in bet.recipients.all():
            n = NotificationFactory.bet_received(r, bet)
            n.save()
            n.send_notification_email()

@receiver(post_save, sender=Bid)
def bid_posted_notification(sender, **kwargs):
    if kwargs.get('created', False) and settings.GENERATE_NOTIFICATIONS:
        bid = kwargs.get('instance')
        if bid.author != bid.bet.author and bid.bet.bet_type != 1:
            n = NotificationFactory.bid_posted(bid)
            n.save()
            n.send_notification_email()

@receiver(pre_delete, sender=Bid)
def bid_deleted_notification(sender, **kwargs):
    if settings.GENERATE_NOTIFICATIONS:
        bid = kwargs.get('instance')
        if bid.author != bid.bet.author:
            n = NotificationFactory.bid_deleted(bid)
            n.save()
            n.send_notification_email()

@receiver(post_transition, sender=Bet)
def bet_change_state_notifications(sender, **kwargs):
    if settings.GENERATE_NOTIFICATIONS:
        bet = kwargs.get('instance')
        transition = kwargs.get('name')

        if transition == 'event':
            if bet.is_simple():
                n = NotificationFactory.bet_accepted(bet)
                n.save()
                n.send_notification_email()
            elif bet.is_auction():
                n = NotificationFactory.bid_accepted(bet.accepted_bid)
                n.save()
                n.send_notification_email()

        if transition == 'resolving':
            n = NotificationFactory.bet_event_finished(bet)
            n.save()
            n.send_notification_email()

        if transition == 'complaining':
            if bet.is_simple() or bet.is_auction():
                n = NotificationFactory.bet_resolving_finished(bet)
                n.save()
                n.send_notification_email()
            elif bet.is_lottery():
                for bid in bet.bids.all():
                    for participant in bid.participants.all():
                        n = NotificationFactory.bet_resolving_finished(bet, participant)
                        n.save()
                        n.send_notification_email()

        if transition == 'arbitrating':
            if bet.is_simple() or bet.is_auction():
                n = NotificationFactory.bet_complaining_finished_conflict(bet)
                n.save()
                n.send_notification_email()
            elif bet.is_lottery():
                for p in bet.participants():
                    n = NotificationFactory.bet_complaining_finished_conflict(bet, p)
                    n.save()
                    n.send_notification_email()

        if transition == 'closed_ok':
            for p in bet.participants():
                n = NotificationFactory.bet_complaining_finished(bet, p)
                n.save()
                n.send_notification_email()

        if transition == 'closed_conflict':
            if bet.is_simple() or bet.is_auction():
                n = NotificationFactory.bet_arbitrated(bet, bet.author)
                n.save()
                n = NotificationFactory.bet_arbitrated(bet, bet.accepted_bid.author)
                n.save()
                n.send_notification_email()
            elif bet.is_lottery():
                for p in bet.participants():
                    n = NotificationFactory.bet_arbitrated(bet, p)
                    n.save()
                    n.send_notification_email()

        if transition == 'closed_desert':
            pass
            