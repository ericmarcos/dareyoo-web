from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView


urlpatterns = patterns('',
    url(r'^login/$', 'django.contrib.auth.views.login',
        {'template_name': 'beta-login.html',
        'current_app': 'beta',
        'extra_context': {'next': '/app/main/timeline-global'}},
        name="beta-login"),
    url(r'^login-error/', 'beta.views.login_error'),
    url(r'^register/$', 'beta.views.register_view', name="beta-register"),
    url(r'^logout/$', 'django.contrib.auth.views.logout',
        #{'template_name': 'beta-landing.html'},
        {'next_page': '/'},
        name='beta-logout'),
    url(r'^$', 'beta.views.landing_view', name='beta-landing'),
    url(r'^como-funciona/$', 'beta.views.how_to', name='beta-how-to'),
    url(r'^faq/$', 'beta.views.faq', name='beta-faq'),
    url(r'^terminos-y-condiciones/$', 'beta.views.legal', name='beta-legal'),
    url(r'^mobile-notification/$', 'beta.views.mobile_notification', name='beta-mobile-notification'),
    url(r'^app', 'beta.views.app', name='beta-home'),
    url(r'^app/main/bet/(?P<slug>[-\w]+)/?$', 'beta.views.app', name='beta-app-bet-detail'),
    url(r'^proposito-2015/$', 'beta.views.campaign_ny2015_view', name='beta-ny2015'),
    url(r'^robots\.txt$', TemplateView.as_view(template_name="robots.txt"), name='beta-robots'),
)
