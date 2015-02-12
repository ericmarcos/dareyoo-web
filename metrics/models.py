from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db import models

from users.signals import user_activated
from bets.models import Bet

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


class Widget(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    bets = models.ManyToManyField(Bet, related_name='widgets', blank=True, null=True)
    next_bets = models.ManyToManyField(Bet, related_name='widgets_next', blank=True, null=True)
    bg_pic = models.ImageField(upload_to='widget_bg', null=True, blank=True)
    header_pic = models.ImageField(upload_to='widget_headers', null=True, blank=True)
    header_link = models.URLField(blank=True, null=True)
    footer_pic = models.ImageField(upload_to='widget_footers', null=True, blank=True)
    footer_link = models.URLField(blank=True, null=True)

    _random_bets = None
    _random_next_bets = None

    def get_bg_pic_url(self):
        if self.bg_pic:
            return self.bg_pic._get_url()
        else:
            return ""

    def get_header_pic_url(self):
        if self.header_pic:
            return self.header_pic._get_url()
        else:
            return ""

    def get_footer_pic_url(self):
        if self.footer_pic:
            return self.footer_pic._get_url()
        else:
            return ""

    def get_random_bets(self):
        if not self._random_bets:
            self._random_bets = list(self.bets.order_by('?'))
        return self._random_bets

    def get_random_next_bets(self):
        if not self._random_next_bets:
            self._random_next_bets = list(self.next_bets.order_by('?'))
        return self._random_next_bets

    def __unicode__(self):
        return unicode(self.name)


class WidgetActivation(models.Model):
    LEVEL_IMPRESSION = 1
    LEVEL_INTERACTION = 2
    LEVEL_PARTICIPATE = 3
    LEVEL_REGISTER = 4
    LEVEL_LOGIN = 5
    LEVEL_SHARE = 6
    LEVEL_BANNER_CLICK = 7

    widget = models.ForeignKey(Widget, related_name='activations', blank=True, null=True)
    bet = models.ForeignKey(Bet, related_name='widget_activations', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    level = models.IntegerField(blank=True, null=True, default=1)
    from_ip = models.GenericIPAddressField(blank=True, null=True)
    from_host = models.CharField(max_length=255, blank=True, null=True)
    participate_result = models.CharField(max_length=255, blank=True, null=True)
    medium_shared = models.CharField(max_length=255, blank=True, null=True) #What medium was shared through (fb, tw...)?
    banner_clicked = models.CharField(max_length=255, blank=True, null=True) #What banner was clicked (footer, header...)?
