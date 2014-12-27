from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


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
    url(r'^mobile-notification/$', 'beta.views.mobile_notification', name='beta-mobile-notification'),
    url(r'^app', 'beta.views.app', name='beta-home'),
)