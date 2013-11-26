from django.db import models
from django.conf import settings
from django.forms.models import model_to_dict


class ModelDiffMixin(object):
    """
    A model mixin that tracks model fields' values and provide some useful api
    to know what fields have been changed.
    http://stackoverflow.com/questions/1355150/django-when-saving-how-can-you-check-if-a-field-has-changed
    """

    def __init__(self, *args, **kwargs):
        super(ModelDiffMixin, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        super(ModelDiffMixin, self).save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        return model_to_dict(self, fields=[field.name for field in
                             self._meta.fields])



BET_STATE_CHOICES = (
    ("bidding", "Bidding"),
    ("event", "Event"),
    ("resolving", "Resolving"),
    ("complaining", "Complaining"),
    ("arbitrating", "Arbitrating"),
    ("closed", "Closed"),
    )

BET_CLAIM_CHOICES = (
    ("undefined", "Undefined"),
    ("won", "Won"),
    ("lost", "Lost"),
    ("null", "Null"),
    )

class BetManager(models.Manager):
    def get_by_user(self, user, state=None):
        if not state:
            return super(BetManager, self).get_queryset().filter(user=user)
        if state in [s[0] for s in BET_STATE_CHOICES]:
            return super(BetManager, self).get_queryset().filter(user=user).filter(bet_state=state)
        else:
            raise Exception

class Bet(models.Model, ModelDiffMixin):
    objects = BetManager()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='bets', blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    bet_state = models.CharField(max_length=63, blank=True, null=True, choices=BET_STATE_CHOICES)
    accepted_bid = models.ForeignKey("Bid", blank=True, null=True, related_name='accepted')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    bidding_deadline = models.DateTimeField(blank=True, null=True)
    event_deadline = models.DateTimeField(blank=True, null=True)
    public = models.BooleanField(blank=True, default=True)
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, null=True)
    claim = models.CharField(max_length=63, blank=True, null=True, choices=BET_CLAIM_CHOICES)

    class Meta:
        pass

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.id and self.user:   # Checking if bet user has enough coins to play
            if self.user.coins_available - self.amount < 0:
                raise Exception("Not enough money! (BET)")
            self.user.coins_available -= self.amount
            self.user.coins_at_stake += self.amount
            self.user.save()
        if 'accepted_bid' in self.changed_fields:
            prev_bid, curr_bid = self.get_field_diff('accepted_bid')
            if curr_bid and curr_bid.user:  # Checking if current bid user has enough coins
                if curr_bid.user.coins_available - self.amount < 0:
                    raise Exception("Not enough money! (BID)")
                curr_bid.user.coins_available -= curr_bid.amount
                curr_bid.user.coins_at_stake += curr_bid.amount
                curr_bid.user.save()
            if prev_bid and prev_bid.user:  # Restoring previous bid user coins
                prev_bid.user.coins_available += prev_bid.amount
                prev_bid.user.coins_at_stake -= prev_bid.amount
                prev_bid.user.save()
        super(Bet, self).save(*args, **kwargs)


class Bid(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='bids', blank=True, null=True)
    bet = models.ForeignKey(Bet, related_name='bids', blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    claim = models.CharField(max_length=63, blank=True, null=True, choices=BET_CLAIM_CHOICES)

    def __unicode__(self):
        return self.title

    class Meta:
        pass
