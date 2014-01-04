from django.core import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django_fsm.signals import pre_transition, post_transition
from .models import Bet
from .tasks import *

'''
The reason to put this logic here is to centralize
the task queuing when bet state changes. We could do
this in the transition functions inside the Bet model,
but I think the model should not know about Celery tasks.
'''


@receiver(post_save, sender=Bet)
def bet_auto_queue_bidding_deadline_task(sender, **kwargs):
    if kwargs.get('created', False) and settings.AUTO_QUEUE_DEADLINES:
        bidding_deadline.apply_async(args=[bet.id], eta=bet.bidding_deadline)

@receiver(post_transition, sender=Bet)
def bet_auto_queue_deadlines_tasks(sender, **kwargs):
    if settings.AUTO_QUEUE_DEADLINES:
        bet = kwargs.get('instance')
        transition = kwargs.get('name')

        if transition == 'event':
            event_deadline.apply_async(args=[bet.id], eta=bet.event_deadline)

        if transition == 'resolving':
            resolving_deadline.apply_async(args=[bet.id], countdown=settings.RESOLVING_COUNTDOWN)

        if transition == 'complaining':
            complaining_deadline.apply_async(args=[bet.id], countdown=settings.COMPLAINING_COUNTDOWN)

        if transition == 'arbitrating':
            arbitrating_deadline.apply_async(args=[b.id], countdown=settings.ARBITRATING_COUNTDOWN)
            