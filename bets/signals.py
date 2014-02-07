from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django_fsm.signals import pre_transition, post_transition
from .models import Bet
from celery.execute import send_task

'''
The reason to put this logic here is to centralize
the task queuing when bet state changes. We could do
this in the transition functions inside the Bet model,
but I think the model should not know about Celery tasks.
'''


@receiver(post_save, sender=Bet)
def bet_auto_queue_bidding_deadline_task(sender, **kwargs):
    if kwargs.get('created', False) and settings.AUTO_QUEUE_DEADLINES:
        bet = kwargs.get('instance')
        send_task('bidding_deadline', [bet.id], eta=bet.bidding_deadline)

@receiver(post_transition, sender=Bet)
def bet_auto_queue_deadlines_tasks(sender, **kwargs):
    if settings.AUTO_QUEUE_DEADLINES:
        bet = kwargs.get('instance')
        transition = kwargs.get('name')
        print bet, transition
        if transition == 'event':
            send_task('event_deadline', [bet.id], eta=bet.event_deadline)

        if transition == 'resolving':
            send_task('resolving_deadline', [bet.id], countdown=settings.RESOLVING_COUNTDOWN)

        if transition == 'complaining':
            send_task('complaining_deadline', [bet.id], countdown=settings.COMPLAINING_COUNTDOWN)

        if transition == 'arbitrating':
            send_task('arbitrating_deadline', [bet.id], countdown=settings.ARBITRATING_COUNTDOWN)
            