import django.dispatch

new_follower = django.dispatch.Signal(providing_args=["user", "follower"])