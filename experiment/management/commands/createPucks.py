from django.core.management.base import BaseCommand
from experiment.models import XtalContainer

class Command(BaseCommand):
    def handle(self, **options):
        n = 16
        try:
            pucks = []
            for i in range(1, n+1):
                pucks.append(XtalContainer(name='FRS-'+str(i), type='puck'))

            XtalContainer.objects.bulk_create(pucks)
        except:
            pass

