from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db import models

from users.signals import user_activated

class UserActivation(models.Model):
    LEVEL_LOGIN = 1
    LEVEL_PARTICIPATE = 2 #participate, resolve, complain, arbitrate, follow...
    LEVEL_CREATE = 3
    LEVEL_BUY = 4

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="activations", blank=True, null=True) 
    timestamp = models.DateTimeField()
    level = models.IntegerField(blank=True, null=True, default=1)

def new_user_activation(sender, user, **kwargs):
    now = kwargs.get('timestamp', timezone.now())
    level = kwargs.get('level', 1)
    last_activation = user.activations.filter(level=level).order_by("-timestamp").first()
    if not last_activation or last_activation.timestamp < now - timedelta(hours=1):
        UserActivation.objects.create(user=user, timestamp=now, level=level)

user_activated.connect(new_user_activation)


from users.models import DareyooUser

def week_actives(cohort, week, activation_level=1):
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    monday = today + timedelta(days=-today.weekday(), weeks=-week)
    sunday = monday + timedelta(weeks=1) # this is actually next monday
    subq = UserActivation.objects.filter(timestamp__range=(monday, sunday), level__gte=activation_level)
    actives = cohort.filter(activations__in=subq).distinct()
    return actives

def weekly_cohort(joined_week, activation_level=1, campaign=None):
    cohort = DareyooUser.objects.real().joined_week(joined_week)
    if campaign:
        cohort = cohort.campaign(campaign)
    weeks = [cohort.count()]
    for i in reversed(xrange(joined_week)):
        actives = week_actives(cohort, i, activation_level)
        weeks.append(actives.count())
    return weeks