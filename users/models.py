import re
from django.utils.translation import ugettext_lazy as _
from django.core import validators
from django.db import models
from django.conf import settings
from django.db import IntegrityError, transaction
from custom_user.models import AbstractEmailUser
from .signals import new_follower

class DareyooUserException(Exception):
    pass

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
    coins_locked = models.FloatField(blank=True, null=True, default=0)

    def n_following(self):
        return self.following.all().count()

    def n_followers(self):
        return self.followers.all().count()

    def follow(self, user):
        if self == user:
            raise DareyooUserException("You can't follow yourself.")
        try:
            with transaction.atomic():
                self.following.add(user)
                new_follower.send(sender=self.__class__, user=user, follower=self)
        except IntegrityError as ie:
            raise DareyooUserException("User %s is already following user %s." % (self.username, user.username))

    def unfollow(self, user):
        self.following.remove(user)

    def is_following(self, user_id):
        return self.following.filter(id=user_id).exists()

    def is_vip(self):
        pass

    def has_funds(self, amount=None):
        if amount:
            return self.coins_available >= amount
        else:
            return self.coins_available > 0

    def lock_funds(self, amount):
        if self.has_funds(amount):
            self.coins_available -= amount
            self.coins_locked += amount
        else:
            raise DareyooUserException("Not enough funds!")
    
    def unlock_funds(self, amount):
        if self.coins_locked >= amount:
            self.coins_available += amount
            self.coins_locked -= amount
        else:
            raise DareyooUserException("Not enough money at stake!")

    def charge(self, amount, locked=False):
        if locked:
            if self.coins_locked >= amount:
                self.coins_locked -= amount
            else:
                raise DareyooUserException("Not enough funds!")
        else:
            if self.has_funds(amount):
                self.coins_available -= amount
            else:
                raise DareyooUserException("Not enough funds!")

    def __unicode__(self):
        return "%s - %s" % (self.email, self.username)


class UserRanking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='rankings', blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    points = models.FloatField(blank=True, null=True, default=0)
    position = models.IntegerField(blank=True, null=True, default=0)

    def __unicode__(self):
        return "%s - %s [%s]" % (self.date, self.position, self.user)


class UserRefill(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='refills', blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    refill_type = models.CharField(max_length=63, blank=True, null=True, choices=REFILL_TYPE_CHOICES)
    amount = models.FloatField(blank=True, null=True, default=0)

    def __unicode__(self):
        return "%s - %s [%s]" % (self.date, self.user, self.refill_type)
