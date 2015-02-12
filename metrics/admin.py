from django.contrib import admin
from .models import *


class WidgetAdmin(admin.ModelAdmin):
    raw_id_fields = ("bets", "next_bets", )


admin.site.register(Widget, WidgetAdmin)