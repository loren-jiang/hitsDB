import factory 
import datetime as dt
from django.utils import timezone
from factory import DjangoModelFactory, lazy_attribute

class PrivateFileFactory(DjangoModelFactory):
    class Meta:
        model = 's3.PrivateFile'

class PrivateFileCSVFactory(DjangoModelFactory):
    class Meta:
        model = 's3.PrivateFileCSV'

class PrivateFileJSONFactory(DjangoModelFactory):
    class Meta:
        model = 's3.PrivateFileJSON'

class PublicFileFactory(DjangoModelFactory):
    class Meta:
        model = 's3.PublicFile'