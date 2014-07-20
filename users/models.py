import re
import hashlib

try:
    from urllib.parse import urljoin, urlencode
except ImportError:
    from urlparse import urljoin
    from urllib import urlencode

import requests
from django.utils.translation import ugettext_lazy as _
from django.core import validators
from django.db import models
from django.conf import settings
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.db.models.query import QuerySet
from django.contrib.auth.models import UserManager
from celery.execute import send_task
from custom_user.models import AbstractEmailUser
from avatar.util import get_primary_avatar, force_bytes
from rest_framework.exceptions import APIException
from .signals import new_follower

class DareyooUserException(APIException):
    status_code = 400

    @property
    def detail(self):
        return str(self)


REFILL_TYPE_CHOICES = (
    ("free", "Free"),
    ("paying", "Paying"),
    )


class DareyooUserQuerySet(QuerySet):
    def staff(self, is_staff=True):
        return self.filter(is_staff=is_staff)

    def registered(self, registered=True):
        return self.filter(registered=registered)

    def real(self):
        return self.staff(False).registered()

    def joined_day(self):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(hours=24)
        return self.joined_between(today, tomorrow)

    def joined_week(self, prev_weeks=0):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        monday = today + timedelta(days=-today.weekday(), weeks=-prev_weeks)
        sunday = monday + timedelta(weeks=1) # this is actually next monday
        return self.joined_between(monday, sunday)

    def joined_month(self, prev_months=0):
        first = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first = first + relativedelta(months=-prev_months)
        last = first + relativedelta(months=1)
        return self.joined_between(first, last)

    def joined_between(self, start, end):
        return self.filter(date_joined__range=(start, end))


class DareyooUserManager(UserManager):
    use_for_related_fields = True

    def get_queryset(self):
        return DareyooUserQuerySet(self.model, using=self._db)

    def get_clean_queryset(self):
        return DareyooUserQuerySet(self.model, using=self._db)

    def real(self):
        qs = self.get_clean_queryset()
        return qs.real()

    def n(self):
        return self.real().count()


class DareyooUser(AbstractEmailUser):
    objects = DareyooUserManager()

    username = models.CharField(_('username'), max_length=30, blank=True, null=True,
        help_text=_('30 characters or fewer. Letters, numbers and '
                    '@/./+/-/_ characters'),
        validators=[
            validators.RegexValidator(re.compile('^[\w.@+-]+$'), _('Enter a valid username.'), 'invalid')
        ])
    reference_user = models.ForeignKey('self', blank=True, null=True, related_name='invited_users')
    reference_campaign = models.CharField(max_length=255, blank=True, null=True)
    registered = models.BooleanField(default=False)
    following = models.ManyToManyField('self', blank=True, null=True, symmetrical=False, related_name='followers')
    profile_pic = models.ImageField(upload_to='profiles', null=True, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    coins_available = models.FloatField(blank=True, null=True, default=settings.INITIAL_COINS)
    coins_locked = models.FloatField(blank=True, null=True, default=0)
    is_pro = models.BooleanField(default=False)
    is_vip = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)

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

    def avatar(self, size=settings.AVATAR_DEFAULT_SIZE):
        avatar = get_primary_avatar(self, size=size)
        if avatar:
            return avatar.avatar_url(size)

        if self.facebook_uid:
            return "http://graph.facebook.com/%s/picture" % self.facebook_uid
        
        default_avatar = urljoin(settings.STATIC_URL, "alpha/img/profile_%s.png" % (self.id or 1 % 10))

        if settings.AVATAR_GRAVATAR_BACKUP:
            params = {'s': str(size), 'd': default_avatar}
            path = "%s/?%s" % (hashlib.md5(force_bytes(self.email)).hexdigest(), urlencode(params))
            return urljoin(settings.AVATAR_GRAVATAR_BASE_URL, path)

        return default_avatar

    def get_profile_pic_url(self):
        if self.profile_pic:
            return self.profile_pic._get_url()
        else:
            return ""

    def get_fb_friends(self):
        social_user = self.social_auth.filter(
            provider='facebook',
        ).first()
        if social_user:
            url = u'https://graph.facebook.com/{0}/' \
                  u'friends?fields=id,name,picture' \
                  u'&access_token={1}'.format(
                      social_user.uid,
                      social_user.extra_data['access_token'],
                  )
            resp = requests.get(url).json()
            friends = resp['data']
            while 'paging' in resp and 'next' in resp['paging']:
                resp = requests.get(resp['paging']['next']).json()
                friends.extend(resp['data'])
            uids = [f['id'] for f in friends]
            in_app_friends = DareyooUser.objects.filter(social_auth__uid__in=uids, social_auth__provider='facebook')
            return in_app_friends
        return []

    def send_welcome_email(self):
        if self.email:
            kwargs = {
                'from_addr': settings.DEFAULT_FROM_EMAIL,
                'to_addr': self.email,
                'subject_template': "email/signup/subject.txt",
                'text_body_template': "email/signup/body.txt",
                'html_body_template': "email/signup/body.html",
                'template_data': {
                    'username': self.username,
                }
            }
            
            send_task('send_email', kwargs=kwargs)

    def __unicode__(self):
        return "%s - %s" % (self.email, self.username)


class UserRefill(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='refills', blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    refill_type = models.CharField(max_length=63, blank=True, null=True, choices=REFILL_TYPE_CHOICES)
    amount = models.FloatField(blank=True, null=True, default=0)

    def __unicode__(self):
        return "%s - %s [%s]" % (self.date, self.user, self.refill_type)
