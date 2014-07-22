from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from users.views import *
from bets.views import *
from notifications.views import *
from gamification.views import *
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'users', DareyooUserBetPointsViewSet)
router.register(r'bets', BetPointsViewSet)
router.register(r'bids', BidViewSet)
router.register(r'tournaments', TournamentViewSet)
router.register(r'notifications', NotificationViewSet)
#TODO:
#/search/
#/search/users/
#/search/bets/
#/search/tournaments/

extra_api_urls = patterns('',
    url(r'^bets/search/$', SearchBetsPointsList.as_view(), name='bets-search'),
    url(r'^timeline/$', TimelinePointsList.as_view(), name='timeline'),
    url(r'^me/(?P<rest>\w*)', MeRedirectView.as_view(), name='me-user-detail'),
    url(r'^search-facebook-friends/$', SearchFacebookFriendsList.as_view(), name='search-facebook-friends'),
    url(r'^search-dareyoo-suggested/$', SearchDareyooSuggestedList.as_view(), name='search-dareyoo-suggested'),
)

from django.contrib import admin
admin.autodiscover()

### API resources ###
'''v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(BetResource())
v1_api.register(BidResource())
'''
urlpatterns = patterns('',
    url(r'^', include('beta.urls')),
    url(r'^', include('metrics.urls')),
    #url(r'^alpha/', include('alpha.urls')),
    url(r'^api/v1/', include(extra_api_urls)),
    url(r'^api/v1/', include(router.urls)),
    url(r'^oauth2/', include('provider.oauth2.urls', namespace = 'oauth2')),
    #(r'^api/', include(v1_api.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    (r'^avatar/', include('avatar.urls')),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url('', include('password_reset.urls')),
)
urlpatterns += staticfiles_urlpatterns()