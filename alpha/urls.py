from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('alpha.views',
    url(r'^$', 'login_view', name='alpha-login'),
    url(r'^logout$', 'logout_view', name='alpha-logout'),
    url(r'^app$', 'app', name='alpha-home'),
)