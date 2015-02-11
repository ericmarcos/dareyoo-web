from django.contrib import admin
from bets.models import *

class BetChoiceInline(admin.TabularInline):
    model = BetChoice
    extra = 0


class BidInline(admin.TabularInline):
    raw_id_fields = ("author",  "claim_author", "participants")
    model = Bid
    extra = 0


class BetAdmin(admin.ModelAdmin):
    raw_id_fields = ("author", "recipients", "referee", )
    inlines = (BetChoiceInline, BidInline, )


admin.site.register(Bet, BetAdmin)