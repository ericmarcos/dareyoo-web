"""
Django settings for dareyoo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

import os
from datetime import timedelta
from django.utils.translation import ugettext_lazy as _
import dj_database_url
import djcelery
#from celery.schedules import crontab

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '#l)5==o7sfqc0oib4bz++nx02)taxpgc#pw+l8m3*26^wryk!*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(int(os.environ.get('DEBUG', True)))

TEMPLATE_DEBUG = DEBUG

PROJECT_NAME = os.environ.get('PROJECT_NAME', 'django_template')

ALLOWED_HOSTS = ['shielded-castle-9030.herokuapp.com', '.dareyoo.com', '.dareyoo.net']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_auth',
    'south',
    'gunicorn',
    'storages',
    'rest_framework',
    'djcelery',
    'kombu.transport.django',
    'haystack',
    'provider',
    'provider.oauth2',
    'custom_user',
    'dareyoo',
    'bets',
    'users',
    'notifications',
    'gamification',
    'alpha',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
)

ROOT_URLCONF = '%s.urls' % PROJECT_NAME

WSGI_APPLICATION = '%s.wsgi.application' % PROJECT_NAME


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-gb'

LANGUAGES = (
    ('en-gb', _('English')),
    ('es-es', _('Spanish')),
    ('ca', _('Catalan'))
)

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = os.environ.get('STATIC_URL', '/static/')

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.environ.get('PROJECT_HOME', '') + '/static/',
)

####### S3 Storage setup ########
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')

### Coins ###

INITIAL_COINS = 10
MAX_FREE_COINS = 10
FREE_COINS_INTERVAL = 60*60*2.4 # In seconds. 1 coin every 2.4 hours are 10 coins every 24h
FREE_COINS_INTERVAL_AMOUNT = 1 # 1 coin in every interval
MIN_FREE_REFILL_PERIOD = timedelta(days=7)
FREE_REFILL_AMOUNT = 50
WINNING_FEES_RATIO = 0.02
REFEREE_FEES_RATIO = 0.02
LOTTERY_REFEREE_FEES = 6

######### CELERY SETUP ###########
djcelery.setup_loader()

BROKER_URL = 'django://'

#RANKING_PERIOD = crontab(hour=1, minute=30, day_of_week=1) # deprecated
RESOLVING_COUNTDOWN = 60*60*24
COMPLAINING_COUNTDOWN = 60*60*24
ARBITRATING_COUNTDOWN = 60*60*24
AUTO_QUEUE_DEADLINES = bool(int(os.environ.get('AUTO_QUEUE_DEADLINES'))) #Set to False when testing to ignore celery (then calling tasks manually)
GENERATE_NOTIFICATIONS = bool(int(os.environ.get('GENERATE_NOTIFICATIONS')))  #Set to False when testing to ignore notifications

CELERYBEAT_SCHEDULE = {
    'add-free-coins': {
        'task': 'free_coins',
        'schedule': timedelta(seconds=FREE_COINS_INTERVAL)
    },
    #'generate-ranking': {
    #    'task': 'users.tasks.ranking',
    #    'schedule': RANKING_PERIOD
    #},
}

CELERY_TIMEZONE = 'UTC'

# Not using migrations for the following apps. (strange errors)
SOUTH_MIGRATION_MODULES = {
    'provider': 'ignore',
    'oauth2': 'ignore',
    'social_auth': 'ignore',
}

AUTHENTICATION_BACKENDS = (
    'social_auth.backends.facebook.FacebookBackend',
    'django.contrib.auth.backends.ModelBackend',
)

FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID')
FACEBOOK_API_SECRET = os.environ.get('FACEBOOK_API_SECRET')
FACEBOOK_EXTENDED_PERMISSIONS = ['email']

AUTH_USER_MODEL = 'users.DareyooUser'
SOCIAL_AUTH_USER_MODEL = 'users.DareyooUser'

SOCIAL_AUTH_PIPELINE = (
    'social_auth.backends.pipeline.social.social_auth_user',
    'social_auth.backends.pipeline.associate.associate_by_email',
    'social_auth.backends.pipeline.user.get_username',
    'social_auth.backends.pipeline.user.create_user',
    'social_auth.backends.pipeline.social.associate_user',
    'social_auth.backends.pipeline.social.load_extra_data',
    'social_auth.backends.pipeline.user.update_user_details'
)

### Haystack ###
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}


#### REST framework ####
REST_FRAMEWORK = {
    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS': 'rest_framework.serializers.HyperlinkedModelSerializer',

    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'PAGINATE_BY': 10
}