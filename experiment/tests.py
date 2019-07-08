from django.test import TestCase
from .models import Experiment, Plate, Well, SubWell, Soak, Project
from import_ZINC.models import Library, Compound
# Create your tests here.

class MyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.foo = Foo.objects.create(bar="Test")
        return 

    def test1(self):
        # Some test using self.foo
        return 

    def test2(self):
        # Some other test using self.foo
        return 