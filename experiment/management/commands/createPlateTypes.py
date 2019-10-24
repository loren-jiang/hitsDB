from django.core.management.base import BaseCommand
from experiment.models import PlateType

class Command(BaseCommand):
    def handle(self, **options):
        PlateType.createEchoSourcePlate()
        PlateType.create96MRC3DestPlate()
        