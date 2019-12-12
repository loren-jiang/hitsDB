import datetime as dt
from django.utils import timezone
from random import randint
from django.template.defaultfilters import slugify
import factory
from factory import DjangoModelFactory, lazy_attribute
import faker
from lib.tests.fixtures import make_n_compounds
from experiment.models import PlateType

faker = faker.Factory.create() 
#--------------------------------------------Project--------------------------------------------
class ProjectFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: 'proj_%d' % n) 
    owner = factory.SubFactory('log.tests.factories.UserFactory')
    
    class Meta:
        model = 'experiment.Project'

#--------------------------------------------Experiment--------------------------------------------
class ExperimentFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: 'exp_%d' % n) 
    owner = factory.SubFactory('log.tests.factories.UserFactory')
    project = factory.SubFactory('experiment.tests.factories.ProjectFactory', owner=owner)
    srcPlateType = factory.SubFactory('experiment.tests.factories.EchoSourcePlateTypeFactory')
    destPlateType = factory.SubFactory('experiment.tests.factories.MRC3DestPlateTypeFactory')
    
    class Meta:
        model = 'experiment.Experiment'


#--------------------------------------------Plate--------------------------------------------
class PlateFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: 'plate_%d' % n) 

    class Meta:
        model = 'experiment.Plate'

class SourcePlateFactory(PlateFactory):
    isSource=True
    # plateType = PlateType.objects.get(name="Echo 384-well source plate")
    plateType = factory.SubFactory('experiment.tests.factories.EchoSourcePlateTypeFactory')

class DestPlateFactory(PlateFactory):
    isSource=False
    # plateType = PlateType.objects.get(name="Swiss MRC-3 96 well microplate")
    plateType = factory.SubFactory('experiment.tests.factories.MRC3DestPlateTypeFactory')

class EchoSourcePlateTypeFactory(DjangoModelFactory):
    # name="Echo 384-well source plate"
    name = factory.Sequence(lambda n: 'Echo 384-well source plate %d' % n)
    numRows=16
    numCols=24
    xPitch = 4.5
    yPitch = 4.5
    plateLength = 127.76
    plateWidth = 85.48
    plateHeight = 10.48
    xOffsetA1 = 12.13
    yOffsetA1 = 8.99
    echoCompatible=True
    isSource=True
    dataSheetURL=''
    class Meta:
        model = 'experiment.PlateType'

class MRC3DestPlateTypeFactory(DjangoModelFactory):
    # name="Swiss MRC-3 96 well microplate"
    name = factory.Sequence(lambda n: 'Swiss MRC-3 96 well microplate %d' % n)
    numRows=8
    numCols=12
    numSubwells = 3
    xPitch = 9
    yPitch = 9
    plateLength = 127.5
    plateWidth = 85.3
    plateHeight = 11.7
    xOffsetA1 = 16.1
    yOffsetA1 = 8.9
    echoCompatible=True
    isSource=False
    dataSheetURL=''
    class Meta:
        model = 'experiment.PlateType'

#--------------------------------------------XtalContainer--------------------------------------------
class PuckFactory(DjangoModelFactory):
    name = factory.sequence(lambda n: '%d' % n)
    type = 'puck'

    class Meta:
        'experiment.XtalContainer'