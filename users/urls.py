from django.conf.urls import patterns, include, url
from users.views import *

urlpatterns = patterns('users.views',
    url(r'^invite_request/$', 'invite_request', name='invite-request')
)