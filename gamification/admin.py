from django.contrib import admin
from .models import *

class TournamentAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'only_author', 'tag', 'public', 'visible', 'weekly', 'start', 'end')

admin.site.register(Prize)
admin.site.register(Tournament, TournamentAdmin)