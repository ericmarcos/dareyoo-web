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

    #def active_month(self):
    #    UserActivation.objects.filter(timestamp__gt=n).values('user').distinct().count()

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
    twitter_share_text = models.CharField(max_length=255, blank=True, null=True,
        help_text="Per posar un hashtag, escriure %23 en comptes de #. Per posar el resultat, escriure {0}. Per posar el titol de l'aposta, escriure {1}",
        default="He apostado por {0} en la porra \"{1}\" via @dareyooApp")

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

    def get_bets(self):
        return list(self.bets.all().bidding())

    def get_random_bets(self):
        if not self._random_bets:
            self._random_bets = list(self.bets.all().bidding().order_by('?'))
        return self._random_bets

    def get_random_next_bets(self):
        if not self._random_next_bets:
            self._random_next_bets = list(self.next_bets.all().bidding().order_by('?'))
        return self._random_next_bets

    def impressions(self):
        return self.activations.filter(level=1).count()

    def interactions(self):
        return self.activations.filter(level=2).count()

    def interactions_formatted(self):
        n = self.interactions()
        try:
            return "{0:n} ({1:.1f}%)".format(n, float(n)/self.impressions() * 100)
        except ZeroDivisionError:
            return "{0:n} (--)".format(n)
    interactions_formatted.short_description = 'Interactions'

    def participate_clicks(self):
        return self.activations.filter(level=3).count()

    def participate_clicks_formatted(self):
        n = self.participate_clicks()
        try:
            return "{0:n} ({1:.1f}%)".format(n, float(n)/self.impressions() * 100)
        except ZeroDivisionError:
            return "{0:n} (--)".format(n)
    participate_clicks_formatted.short_description = 'Participate clicks'

    def registers(self):
        return self.activations.filter(level=4).count()

    def registers_formatted(self):
        n = self.registers()
        try:
            return "{0:n} ({1:.1f}%)".format(n, float(n)/self.participate_clicks() * 100)
        except ZeroDivisionError:
            return "{0:n} (--)".format(n)
    registers_formatted.short_description = 'Registers'

    def logins(self):
        return self.activations.filter(level=5).count()

    def logins_formatted(self):
        n = self.logins()
        try:
            return "{0:n} ({1:.1f}%)".format(n, float(n)/self.participate_clicks() * 100)
        except ZeroDivisionError:
            return "{0:n} (--)".format(n)
    logins_formatted.short_description = 'Logins'

    def shares(self):
        return self.activations.filter(level=6).count()

    def shares_formatted(self):
        n = self.shares()
        try:
            return "{0:n} ({1:.1f}%)".format(n, float(n)/(self.registers() + self.logins()) * 100)
        except ZeroDivisionError:
            return "{0:n} (--)".format(n)
    shares_formatted.short_description = 'Shares'

    def banner_clicks(self):
        return self.activations.filter(level=7).count()

    def banner_clicks_formatted(self):
        n = self.banner_clicks()
        try:
            return "{0:n} ({1:.1f}%)".format(n, float(n)/self.impressions() * 100)
        except ZeroDivisionError:
            return "{0:n} (--)".format(n)
    banner_clicks_formatted.short_description = 'Banner clicks'

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
