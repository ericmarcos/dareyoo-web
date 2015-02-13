from django.contrib import admin
from .models import *


class WidgetAdmin(admin.ModelAdmin):
    raw_id_fields = ("bets", "next_bets", )
    list_display = ('name', 'impressions',
        'interactions_formatted',
        'participate_clicks_formatted',
        'registers_formatted',
        'logins_formatted',
        'shares_formatted',
        'banner_clicks_formatted')


admin.site.register(Widget, WidgetAdmin)