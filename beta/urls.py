from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = patterns('',
    url(r'^login/$', 'django.contrib.auth.views.login',
        {'template_name': 'beta-login.html',
        'current_app': 'beta',
        'extra_context': {'next': '/app/main/timeline-global'}},
        name="beta-login"),
    url(r'^register/$', 'beta.views.register_view', name="beta-register"),
    url(r'^logout/$', 'django.contrib.auth.views.logout',
        #{'template_name': 'beta-landing.html'},
        {'next_page': '/'},
        name='beta-logout'),
    url(r'^$', 'beta.views.landing_view', name='beta-landing'),
    url(r'^app', 'beta.views.app', name='beta-home'),
)