from django.contrib import admin
from users.models import DareyooUser
from custom_user.models import EmailUser

#admin.site.unregister(EmailUser)
admin.site.register(DareyooUser)