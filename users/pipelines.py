import os
import re
import hashlib

try:
    from urllib.parse import urljoin, urlencode
except ImportError:
    from urlparse import urljoin
    from urllib import urlencode

from avatar.util import get_primary_avatar, force_bytes
from requests import request, HTTPError

from django.core.files.base import ContentFile
from django.conf import settings
from .models import DareyooUser

#http://stackoverflow.com/questions/19890824/save-facebook-profile-picture-in-model-using-python-social-auth
def save_profile_picture(strategy, user, response, details,
                         is_new=False,*args,**kwargs):

    if is_new:
        if strategy and strategy.backend and strategy.backend.name == 'facebook':
            url = 'http://graph.facebook.com/{0}/picture'.format(response['id'])
            params={'type': 'normal', 'height': 200, 'width': 200}
        else:
            default_avatar = urljoin(settings.STATIC_URL, "beta/build/img/default_profile_pics/profile_{0}.png".format(user.id or 1 % 10))
            params = {'s': str(settings.AVATAR_DEFAULT_SIZE), 'd': default_avatar}
            path = str(hashlib.md5(force_bytes(user.email)).hexdigest())
            url = urljoin(settings.AVATAR_GRAVATAR_BASE_URL, path)
        try:
            resp = request('GET', url, params=params)
            resp.raise_for_status()
            ext = "jpg" if resp.headers['content-type'] == 'image/jpeg' else 'png'
            user.profile_pic.save('{0}_social.{1}'.format(user.id, ext),
                                   ContentFile(resp.content))
            user.save()
        except Exception:
            pass

def save_username(strategy, user, response, details,
                    is_new=False, *args, **kwargs):
    if is_new:
        if strategy and strategy.backend and strategy.backend.name == 'facebook':
            try:
                username = response['username']
                unique_slugify(user, response['username'], 'username')
                user.save()
            except Exception:
                pass
        else:
            params = {'class': 'fn'}
            path = hashlib.md5(force_bytes(user.email)).hexdigest()
            url = urljoin('http://gravatar.com', path)
            try:
                resp = request('GET', url + ".json", params=params)
                resp.raise_for_status()
                username = resp.json()['entry'][0]['preferredUsername']
                unique_slugify(user, username, 'username')
                user.save()
            except Exception:
                pass

def save_reference_user(strategy, user, response, details,
                    is_new=False, *args, **kwargs):
    if not user.reference_user:
        reference_user_id = int(kwargs['request'].session.get('from', '0')) or None
        try:
            ref_user = DareyooUser.objects.get(id=reference_user_id)
            user.reference_user = ref_user
            user.save()
            ref_user.coins_available += 50
            ref_user.save()
        except:
            pass

def save_registered(strategy, user, response, details,
                    is_new=False, *args, **kwargs):
    if not user.registered:
        user.registered = True
        user.save()

def save_campaign(strategy, user, response, details,
                    is_new=False, *args, **kwargs):
    if not user.reference_campaign:
        utm_source = kwargs['request'].session.get('utm_source')
        utm_medium = kwargs['request'].session.get('utm_medium')
        utm_campaign = kwargs['request'].session.get('utm_campaign')
        user.reference_campaign = "%s_%s_%s" % (utm_source, utm_medium, utm_campaign)
        user.save()

#https://djangosnippets.org/snippets/690/
import re
from django.template.defaultfilters import slugify


def unique_slugify(instance, value, slug_field_name='slug', queryset=None,
                   slug_separator='-'):
    """
    Calculates and stores a unique slug of ``value`` for an instance.

    ``slug_field_name`` should be a string matching the name of the field to
    store the slug in (and the field to check against for uniqueness).

    ``queryset`` usually doesn't need to be explicitly provided - it'll default
    to using the ``.all()`` queryset from the model's default manager.
    """
    slug_field = instance._meta.get_field(slug_field_name)

    slug = getattr(instance, slug_field.attname)
    slug_len = slug_field.max_length

    # Sort out the initial slug, limiting its length if necessary.
    slug = slugify(value)
    if slug_len:
        slug = slug[:slug_len]
    slug = _slug_strip(slug, slug_separator)
    original_slug = slug

    # Create the queryset if one wasn't explicitly provided and exclude the
    # current instance from the queryset.
    if queryset is None:
        queryset = instance.__class__._default_manager.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    # Find a unique slug. If one matches, at '-2' to the end and try again
    # (then '-3', etc).
    next = 2
    while not slug or queryset.filter(**{slug_field_name: slug}):
        slug = original_slug
        end = '%s%s' % (slug_separator, next)
        if slug_len and len(slug) + len(end) > slug_len:
            slug = slug[:slug_len-len(end)]
            slug = _slug_strip(slug, slug_separator)
        slug = '%s%s' % (slug, end)
        next += 1

    setattr(instance, slug_field.attname, slug)


def _slug_strip(value, separator='-'):
    """
    Cleans up a slug by removing slug separator characters that occur at the
    beginning or end of a slug.

    If an alternate separator is used, it will also replace any instances of
    the default '-' separator with the new separator.
    """
    separator = separator or ''
    if separator == '-' or not separator:
        re_sep = '-'
    else:
        re_sep = '(?:-|%s)' % re.escape(separator)
    # Remove multiple instances and if an alternate separator is provided,
    # replace the default '-' separator.
    if separator != re_sep:
        value = re.sub('%s+' % re_sep, separator, value)
    # Remove separator from the beginning and end of the slug.
    if separator:
        if separator != '-':
            re_sep = re.escape(separator)
        value = re.sub(r'^%s+|%s+$' % (re_sep, re_sep), '', value)
    return value