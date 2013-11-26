from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from tastypie.api import Api
from users.api import *
from bets.api import *

from django.contrib import admin
admin.autodiscover()

### API resources ###
v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(BetResource())
v1_api.register(BidResource())

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name="index.html"), name='home'),
    url(r'^oauth2/', include('provider.oauth2.urls', namespace = 'oauth2')),
    (r'^api/', include(v1_api.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('users.urls')),
    url(r'', include('social_auth.urls')),
    #url(r'', include('bets.urls')),
)
urlpatterns += staticfiles_urlpatterns()