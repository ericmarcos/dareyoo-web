
from django.db import models


class MobileNotification(models.Model):

    email = models.EmailField()
    os = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)