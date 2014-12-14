import django.dispatch
#No need to create a new signal really, can do it with m2m_changed signal
new_follower = django.dispatch.Signal(providing_args=["user", "follower"])

user_activated = django.dispatch.Signal(providing_args=["user"])