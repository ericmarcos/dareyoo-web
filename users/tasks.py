from datetime import datetime, timedelta
from celery import shared_task
from users.models import *
from django.conf import settings
from django.utils.timezone import now

@shared_task(name='free_coins')
def free_coins(**kwargs):
    '''Recurrent task that gives free free coins
    to all users under MAX_FREE_COINS'''
    users = DareyooUser.objects.filter(coins_available__lt=settings.MAX_FREE_COINS)
    #TODO: should it be coins_available or coins_available - coins_locked?
    for user in users:
        if user.coins_available < settings.MAX_FREE_COINS - settings.FREE_COINS_INTERVAL_AMOUNT:
            user.coins_available += settings.FREE_COINS_INTERVAL_AMOUNT
            user.save()
        elif user.coins_available < settings.MAX_FREE_COINS:
            user.coins_available = settings.MAX_FREE_COINS
            user.save()
