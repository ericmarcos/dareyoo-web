from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        print "Hello world"