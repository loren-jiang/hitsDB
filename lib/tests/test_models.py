from django.test import TestCase
from django.test import Client
from ..models import Library, Compound
from .factories import LibraryFactory, CompoundFactory
from .fixtures import make_n_compounds
from ..utils import bulk_get_or_create_compounds, bulk_get_or_create_compounds_to_library

# Create your tests here.

class Tests(TestCase):
    def setUp(self):
        self.client = Client()

    def testBulkGetOrCreateCompounds(self):
        # compounds = make_n_compounds(1000)
        # print(compounds)
        compounds = make_n_compounds(1000) #saved to DB
        self.assertEquals(1000, Compound.objects.all().count()) #checking saved to DB

        [pks_added, pks_existing] = bulk_get_or_create_compounds(compounds)
        self.assertEquals(0, len(pks_added)) #0 compounds added
        self.assertEquals(1000, len(pks_existing)) #1000 compounds existing

        unsavedCompounds = [CompoundFactory.build() for k in range(100)]#not saved to DB
        self.assertEquals(1000, Compound.objects.all().count()) #checking saved to DB
        [pks_added, pks_existing]  = bulk_get_or_create_compounds(unsavedCompounds)
        self.assertEquals(100, len(pks_added)) #100 compounds added
        self.assertEquals(0, len(pks_existing)) #0 compounds existing
        self.assertEquals(1100, Compound.objects.all().count()) #checking saved to DB

    def testBulkGetOrCreateCompoundsToLibrary(self):
        self.assertEquals(Compound.objects.all().count(), 0)
        lib = LibraryFactory()
        compounds = make_n_compounds(1000)
        lib.compounds.add(*compounds[0:500]) #adds first 500 compounds
        self.assertEquals(500, lib.compounds.count()) #should have 500 compounds

        [pks_added_to_lib, pks_existing_in_lib] = bulk_get_or_create_compounds_to_library(compounds, library=lib)
        self.assertEquals(1000, lib.compounds.count()) #should have 1000 compounds now
        self.assertEquals(500, len(pks_added_to_lib)) #500 compounds added
        self.assertEquals(500, len(pks_existing_in_lib)) #500 compounds existing

        unsavedCompounds = [CompoundFactory.build() for k in range(100)]#not saved to DB; should still work
        [pks_added_to_lib, pks_existing_in_lib] = bulk_get_or_create_compounds_to_library(unsavedCompounds, library=lib)
        self.assertEquals(100, len(pks_added_to_lib)) #100 compounds added 
        self.assertEquals(0, len(pks_existing_in_lib)) #0 compounds existing

        compoundsAlreadyInLib = compounds[0:100]
        [pks_added_to_lib, pks_existing_in_lib] = bulk_get_or_create_compounds_to_library(compoundsAlreadyInLib, library=lib)
        self.assertEquals(0, len(pks_added_to_lib))
        self.assertEquals(100, len(pks_existing_in_lib))

