from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed
from django_fsm.signals import pre_transition, post_transition
from bets.models import Bet, Bid
from users.models import DareyooUser
from .models import *


@receiver(post_save, sender=DareyooUser)
def new_user_badges(sender, **kwargs):
    if kwargs.get('created', False):
        #Creating the 1to1 instance of badges
        #when a user is created
        user = kwargs.get('instance')
        ub = UserBadges()
        ub.user = user
        ub.fair_play = 1
        ub.save()


@receiver(post_transition, sender=Bet)
def bet_closing_points(sender, **kwargs):
    bet = kwargs.get('instance')
    transition = kwargs.get('name')

    if transition == 'closed_ok' or transition == 'closed_arbitrating':
        #Calculate points for this bet
        UserPointsFactory.fromBet(bet)

        #Check out if any badges were unlocked
        UserBadges.fromBet(bet)


@receiver(post_save, sender=Bet)
def bet_tournament(sender, **kwargs):
    bet = kwargs.get('instance')
    if kwargs.get('created', False):
        Tournament.check_bet_all_tournaments(bet)
    elif bet.accepted_bid:
        #TODO: set a signal when a bid is accepted
        Tournament.check_bet_bidder_tournaments(bet)

@receiver(m2m_changed, sender=Bid.participants.through)
def bid_participants_changed(sender, **kwargs):
    # Add participants to tournament
    pass


import django.dispatch

badge_unlocked = django.dispatch.Signal(providing_args=["user", "badge", "level", "prev_level"])