from django.db import models
from django.conf import settings
from bets.models import Bet

NOTIFICATION_TYPE_CHOICES = (
    ("bidding", "Bidding"),
    ("event", "Event"),
    ("resolving", "Resolving"),
    ("complaining", "Complaining"),
    ("arbitrating", "Arbitrating"),
    ("closed", "Closed"),
    )

class Notification(models.Model):
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    facebook_uid = models.CharField(max_length=255, blank=True, null=True)
    notification_type = models.CharField(max_length=63, blank=True, null=True, choices=NOTIFICATION_TYPE_CHOICES)
    bet = models.ForeignKey(Bet, related_name='notifications', blank=True, null=True)
    is_new = models.BooleanField(blank=True, default=True)
    readed = models.BooleanField(blank=True, default=False)

    def __unicode__(self):
        return "%s - %s [%s]" % (self.date, self.position, self.user)