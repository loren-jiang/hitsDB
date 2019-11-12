import datetime as dt
from django.utils import timezone
from random import randint
from django.template.defaultfilters import slugify
import factory
from factory import DjangoModelFactory, lazy_attribute
import faker
import random
import decimal

faker = faker.Factory.create() 

class LibraryFactory(DjangoModelFactory):
    class Meta:
        model = 'lib.Library'
    name = factory.Sequence(lambda n: 'library_%s' % n)

    @factory.post_generation
    def compounds(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            self.compounds.add(*extracted)

class CompoundFactory(DjangoModelFactory):
    class Meta:
        model = 'lib.Compound'
    zinc_id = factory.Sequence(lambda n: 'ZINC_%s' % n)
    molWeight = float(decimal.Decimal(random.randrange(0, 100)))
    concentration = float(decimal.Decimal(random.randrange(50, 100)))