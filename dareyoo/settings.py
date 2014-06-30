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
DEBUG = bool(int(os.environ.get('DEBUG', 1)))

TEMPLATE_DEBUG = DEBUG

PROJECT_NAME = os.environ.get('PROJECT_NAME', 'django_template')

ALLOWED_HOSTS = ['dareyoo.herokuapp.com', 'dareyoo-pro.herokuapp.com', 'dareyoo-pre.herokuapp.com', '.dareyoo.com', '.dareyoo.net', '.dareyoo.es']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
#    'social_auth',
    'south',
    'gunicorn',
    'storages',
    'rest_framework',
    'djcelery',
#    'kombu.transport.django',
#    'haystack',
    'provider',
    'provider.oauth2',
    'custom_user',
    'social.apps.django_app.default',
#    'social.apps.django_app.me',
    'avatar',
    'djrill',
    'dareyoo',
    'bets',
    'users',
    'notifications',
    'gamification',
    #'alpha',
    'beta',
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

TEMPLATE_CONTEXT_PROCESSORS = ("django.contrib.auth.context_processors.auth",
                                "django.core.context_processors.debug",
                                "django.core.context_processors.i18n",
                                "django.core.context_processors.media",
                                "django.core.context_processors.static",
                                "django.core.context_processors.tz",
                                "django.contrib.messages.context_processors.messages",
                                "django.core.context_processors.request",
                                "social.apps.django_app.context_processors.backends",
                                "social.apps.django_app.context_processors.login_redirect",)

####### S3 Storage setup ########
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')

### Coins ###

INITIAL_COINS = 100
MAX_FREE_COINS = 100
FREE_COINS_INTERVAL = 60*60*2.4 # In seconds. 10 coin every 2.4 hours are 10 coins every 24h
FREE_COINS_INTERVAL_AMOUNT = 10 # 10 coin in every interval
MIN_FREE_REFILL_PERIOD = timedelta(days=7)
FREE_REFILL_AMOUNT = 50
WINNING_FEES_RATIO = 0.02
REFEREE_FEES_RATIO = 0.02
LOTTERY_REFEREE_FEES = 6

######### CELERY SETUP ###########
BROKER_POOL_LIMIT = 3
#BROKER_TRANSPORT = 'amqplib'
#BROKER_CONNECTION_MAX_RETRIES = 0

djcelery.setup_loader()

#BROKER_URL = 'django://'
BROKER_URL = os.environ.get('CLOUDAMQP_URL', 'django://')

CELERY_ACCEPT_CONTENT = ['json']

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

#CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'
#CELERY_RESULT_BACKEND = 'database'
#CELERY_BEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
db_url = os.environ.get('DATABASE_URL')

'postgresql+psycopg2://scott:tiger@localhost/mydatabase'
#CELERY_RESULT_BACKEND = 'db+postgresql' + db_url[8:]
CELERY_TASK_RESULT_EXPIRES = 14400


#RANKING_PERIOD = crontab(hour=1, minute=30, day_of_week=1) # deprecated
RESOLVING_COUNTDOWN = 60*60*24
COMPLAINING_COUNTDOWN = 60*60*24
ARBITRATING_COUNTDOWN = 60*60*24
AUTO_QUEUE_DEADLINES = bool(int(os.environ.get('AUTO_QUEUE_DEADLINES', 1))) #Set to False when testing to ignore celery (then calling tasks manually)
GENERATE_NOTIFICATIONS = bool(int(os.environ.get('GENERATE_NOTIFICATIONS', 1)))  #Set to False when testing to ignore notifications

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

#this is the default already
#CELERY_TIMEZONE = 'UTC'

# Not using migrations for the following apps. (strange errors)
SOUTH_MIGRATION_MODULES = {
    'provider': 'ignore',
    'oauth2': 'ignore'
}

#AUTHENTICATION_BACKENDS = (
#    'social_auth.backends.facebook.FacebookBackend',
#    'django.contrib.auth.backends.ModelBackend',
#)

#FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID')
#FACEBOOK_API_SECRET = os.environ.get('FACEBOOK_API_SECRET')
#FACEBOOK_EXTENDED_PERMISSIONS = ['email']
SOCIAL_AUTH_FACEBOOK_KEY = os.environ.get('FACEBOOK_APP_ID')
SOCIAL_AUTH_FACEBOOK_SECRET = os.environ.get('FACEBOOK_API_SECRET')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'user_friends']
SOCIAL_AUTH_FACEBOOK_EXTRA_DATA = ['first_name', 'middle_name', 'last_name', 'locale', 'gender', 'location', 'timezone']

AUTHENTICATION_BACKENDS = (
    'social.backends.facebook.FacebookOAuth2',
    'social.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

#http://python-social-auth.readthedocs.org/en/latest/configuration/settings.html#urls-options
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/app/main/timeline-global'
SOCIAL_AUTH_LOGIN_URL = '/login/'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/app/edit-profile?new'
SOCIAL_AUTH_NEW_ASSOCIATION_REDIRECT_URL = '/new-association-redirect-url/'
SOCIAL_AUTH_DISCONNECT_REDIRECT_URL = '/account-disconnected-redirect-url/'
SOCIAL_AUTH_INACTIVE_USER_URL = '/inactive-user/'

SOCIAL_AUTH_STRATEGY = 'social.strategies.django_strategy.DjangoStrategy'
SOCIAL_AUTH_STORAGE = 'social.apps.django_app.default.models.DjangoStorage'

AUTH_USER_MODEL = 'users.DareyooUser'
SOCIAL_AUTH_USER_MODEL = 'users.DareyooUser'

SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',
    'social.pipeline.user.get_username',
    'social.pipeline.user.create_user',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details',
    'users.pipelines.save_profile_picture',
    'users.pipelines.save_username',
    'users.pipelines.save_reference_user',
    'users.pipelines.save_registered',
)

### Haystack ###
#HAYSTACK_CONNECTIONS = {
#    'default': {
#        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
#    },
#}


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

### DJRILL ###

MANDRILL_API_KEY = os.environ.get('MANDRILL_APIKEY')
EMAIL_BACKEND = "djrill.mail.backends.djrill.DjrillBackend"

DEFAULT_FROM_ADDR = 'no-reply@dareyoo.com'