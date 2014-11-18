from django.contrib import admin
from users.models import DareyooUser, PromoCode
from custom_user.models import EmailUser

class DareyooUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'date_joined', 'last_login', 'is_paying', 'is_staff', 'n_bets')
    list_filter = ('is_staff',)
    search_fields = ('username', 'email')

    def n_bets(self, obj):
        return unicode(obj.bets.count())

admin.site.register(DareyooUser, DareyooUserAdmin)
admin.site.register(PromoCode)