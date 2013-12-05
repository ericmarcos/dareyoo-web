from django.conf.urls import patterns, url
from django.views.generic import TemplateView

urlpatterns = patterns('bets.views',
    url(r'^timeout$', TemplateView.as_view(template_name="timeout.html"), name='timeout'),
)