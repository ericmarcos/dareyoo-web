import re
from django.utils.translation import ugettext_lazy as _
from django.core import validators
from django.db import models
from django.conf import settings
from custom_user.models import AbstractEmailUser
from bets.models import Bet

NOTIFICATION_TYPE_CHOICES = (
    ("bidding", "Bidding"),
    ("event", "Event"),
    ("resolving", "Resolving"),
    ("complaining", "Complaining"),
    ("arbitrating", "Arbitrating"),
    ("closed", "Closed"),
    )

REFILL_TYPE_CHOICES = (
    ("free", "Free"),
    ("paying", "Paying"),
    )

class DareyooUser(AbstractEmailUser):
    username = models.CharField(_('username'), max_length=30, blank=True, null=True,
        help_text=_('30 characters or fewer. Letters, numbers and '
                    '@/./+/-/_ characters'),
        validators=[
            validators.RegexValidator(re.compile('^[\w.@+-]+$'), _('Enter a valid username.'), 'invalid')
        ])
    first_name = models.CharField(_('first name'), max_length=30, blank=True, null=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    reference_user = models.ForeignKey('self', blank=True, null=True, related_name='invited_users')
    following = models.ManyToManyField('self', blank=True, null=True, symmetrical=False, related_name='followers')
    facebook_uid = models.CharField(max_length=255, blank=True, null=True)

    coins_available = models.FloatField(blank=True, null=True, default=settings.INITIAL_COINS)
    coins_at_stake = models.FloatField(blank=True, null=True, default=0)
    points = models.FloatField(blank=True, null=True, default=0)

    def n_following(self):
        return len(self.following.all())

    def n_followers(self):
        return len(self.followers.all())

    def __unicode__(self):
        return "%s - %s" % (self.email, self.username)

class UserRanking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='rankings', blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    points = models.FloatField(blank=True, null=True, default=0)
    position = models.IntegerField(blank=True, null=True, default=0)

    def __unicode__(self):
        return "%s - %s [%s]" % (self.date, self.position, self.user)

class Notification(models.Model):
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', blank=True, null=True)
    subject = facebook_uid = models.CharField(max_length=255, blank=True, null=True)
    notification_type = models.CharField(max_length=63, blank=True, null=True, choices=NOTIFICATION_TYPE_CHOICES)
    bet = models.ForeignKey(Bet, related_name='notifications', blank=True, null=True)
    is_new = models.BooleanField(blank=True, default=True)
    readed = models.BooleanField(blank=True, default=False)

    def __unicode__(self):
        return "%s - %s [%s]" % (self.date, self.position, self.user)

class UserRefill(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='refills', blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    refill_type = models.CharField(max_length=63, blank=True, null=True, choices=REFILL_TYPE_CHOICES)
    amount = models.FloatField(blank=True, null=True, default=0)

    def __unicode__(self):
        return "%s - %s [%s]" % (self.date, self.user, self.refill_type)