from datetime import datetime, timedelta
from celery.task import task
from users.models import *
from django.conf import settings
from django.utils.timezone import now

@task
def free_coins(**kwargs):
    '''Recurrent task that gives free free coins
    to all users under MAX_FREE_COINS'''
    users = DareyooUser.objects.all()
    for user in users:
        if user.coins_available < settings.MAX_FREE_COINS - settings.FREE_COINS_INTERVAL_AMOUNT:
            user.coins_available += settings.FREE_COINS_INTERVAL_AMOUNT
            user.save()
        elif user.coins_available < settings.MAX_FREE_COINS:
            user.coins_available = settings.MAX_FREE_COINS
            user.save()

@task
def generate_rankings(**kwargs):
    ranking_date = now()
    users = list(DareyooUser.objects.all().order_by('-points'))
    for i, u in enumerate(users):
        r = UserRanking()
        r.user = u
        r.date = ranking_date
        r.points = u.points
        r.position = i + 1
        r.save()
        u.points = 0
        u.save()

