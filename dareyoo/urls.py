import pytz
from dateutil import rrule
from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.sitemaps.views import sitemap
from django.contrib import sitemaps
from django.contrib import admin
from django.utils import timezone
from users.views import *
from bets.views import *
from notifications.views import *
from gamification.views import *
from metrics.views import *
from rest_framework import routers

# API
router = routers.DefaultRouter()
router.register(r'users', DareyooUserBetPointsViewSet)
router.register(r'bets', BetPointsViewSet)
router.register(r'bids', BidViewSet)
router.register(r'tournaments', TournamentViewSet)
router.register(r'prizes', PrizeViewSet)
router.register(r'notifications', NotificationViewSet)

extra_api_urls = patterns('',
    url(r'^bets/search/$', SearchBetsPointsList.as_view(), name='bets-search'),
    url(r'^timeline/$', TimelinePointsList.as_view(), name='timeline'),
    #url(r'^me/$', MeRedirectView.as_view(), name='me-user-detail'),
    url(r'^me/$', MeView.as_view(), name='me-user-detail'),
    url(r'^search-facebook-friends/$', SearchFacebookFriendsList.as_view(), name='search-facebook-friends'),
    url(r'^search-dareyoo-suggested/$', SearchDareyooSuggestedList.as_view(), name='search-dareyoo-suggested'),
    url(r'^register/$', register, name='register'),
    url(r'^register-by-access-token/(?P<backend>[^/]+)/$', register_by_access_token, name='register_by_access_token'),
    url(r'^widget_activation/(?P<widget>[^/]+)/(?P<level>\w+)/$', widget_activation, name='widget_activation'),
)

admin.autodiscover()

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['beta-register', 'beta-login', 'beta-landing', 'beta-how-to', 'beta-faq', 'beta-archive-index']

    def location(self, item):
        return reverse(item)

class BetArchiveSitemap(sitemaps.Sitemap):
    priority = 0.6
    changefreq = 'always'

    def items(self):
        start_date = timezone.datetime(year=2014, month=6, day=1, tzinfo=pytz.UTC)
        weeks = rrule.rrule(rrule.WEEKLY, dtstart=start_date, until=timezone.now())
        return [start_date + timezone.timedelta(weeks=weeks.count() - 1 - i) for i in xrange(weeks.count())]

    def location(self, item):
        return reverse('beta-archive-page', args=[item.strftime('%d-%m-%Y'),])

sitemaps = {
    'static': StaticViewSitemap,
    'archive': BetArchiveSitemap,
    'bets': sitemaps.GenericSitemap({
        'queryset': Bet.objects.all().public(),
        'date_field': 'created_at',
    }, priority=0.7)
}

urlpatterns = patterns('',
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps},
    name='django.contrib.sitemaps.views.sitemap'),
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
