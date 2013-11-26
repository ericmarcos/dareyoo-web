from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Prints \"Hello world\""
    can_import_settings = True
    option_list = (
        make_option('--option-name', dest='option_name', default='world',
                    help='Fixture name to write to'),
    )

    def handle(self, *args, **options):
        print "Hello %s" % options["option_name"]