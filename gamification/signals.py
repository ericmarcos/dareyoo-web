from django.conf import settings
from django.dispatch import receiver
from django_fsm.signals import pre_transition, post_transition
from bets.models import Bet
from .models import UserPointsFactory


@receiver(post_transition, sender=Bet)
def bet_closing_points(sender, **kwargs):
    bet = kwargs.get('instance')
    transition = kwargs.get('name')

    if transition == 'closed_ok':
        UserPointsFactory.fromBet(bet)

    if transition == 'closed_arbitrating':
        UserPointsFactory.fromBet(bet)
            