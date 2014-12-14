from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db import models

from users.signals import user_activated

class UserActivation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="activations", blank=True, null=True) 
    timestamp = models.DateTimeField()

def new_user_activation(sender, user, **kwargs):
    now = timezone.now()
    last_activation = user.activations.order_by("-timestamp").first()
    if not last_activation or last_activation.timestamp < now - timedelta(hours=1):
        UserActivation.objects.create(user=user, timestamp=now)

user_activated.connect(new_user_activation)