from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from tastypie.api import Api
from users.api import *
from users.views import *
from bets.api import *
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'users', DareyooUserViewSet)
followers = DareyooUserViewSet.as_view({
    'get': 'followers'
})
following = DareyooUserViewSet.as_view({
    'get': 'following',
    'post': 'follow',
    'delete': 'unfollow'
})

from django.contrib import admin
admin.autodiscover()

### API resources ###
'''v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(BetResource())
v1_api.register(BidResource())
'''
urlpatterns = patterns('',
    url(r'^api/v1/', include(router.urls)),
    #url(r'^api/v1/user/(?P<pk>[0-9]+)/followers/$', followers, name='followers'),
    #url(r'^api/v1/user/(?P<pk>[0-9]+)/following/$', following, name='following'),
    url(r'^$', TemplateView.as_view(template_name="index.html"), name='home'),
    url(r'^oauth2/', include('provider.oauth2.urls', namespace = 'oauth2')),
    #(r'^api/', include(v1_api.urls)),
    url(r'^admin/', include(admin.site.urls)),
    #url(r'', include('users.urls')),
    url(r'', include('social_auth.urls')),
    #url(r'', include('bets.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
)
urlpatterns += staticfiles_urlpatterns()