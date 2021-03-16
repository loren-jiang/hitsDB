from django.test import TestCase
from django.contrib.auth.models import User, Group
from experiment.models import Experiment, Plate, PlateType, Project, Soak, SubWell, Well
from lib.models import Library, Compound
from datetime import datetime
from django.utils.timezone import make_aware
from django.db import transaction
from django.db.utils import IntegrityError
from django.test import Client
from log.tests import factories as logFactories
from log.tests import fixtures as logFixtures
from lib.tests.factories import LibraryFactory
from lib.tests.fixtures import make_n_compounds
from .factories import PlateFactory, SourcePlateFactory, DestPlateFactory, ExperimentFactory
from django.db.utils import IntegrityError
from random import randint
from my_utils.utility_functions import lists_equal
from django.core.exceptions import ValidationError
from .fixtures import example_init_data, experiment_with_init_data, experiment_with_source_plates, experiment_with_matched_soaks
import os

class ExperimentTests(TestCase):
    def setUp(self):
        self.client = Client()

    ### SIGNAL TESTING ###
    def testAwareOfState(self):
        lib1 = LibraryFactory(compounds=make_n_compounds(randint(100,1000)))
        init_data1 = example_init_data()

        exp = ExperimentFactory(library=lib1)
        exp.initData = init_data1
        exp.save()
        self.assertEquals(exp.prev_library_id, lib1.id) #library id taken note of
        self.assertEquals(exp.prev_initData_id, exp.initData.id) #library id taken note of
        os.remove("./media/" + str(exp.initData.local_upload)) 
        
        same_exp = Experiment.objects.filter(id=exp.id)

    def testInitDataPostSignal(self):
        exp = experiment_with_init_data()
        plates_qs_1 = exp.plates.all()
        exp.save()
        plates_qs_2 = exp.plates.all()
        self.assertQuerysetEqual(plates_qs_1, plates_qs_2, transform=lambda x:x)
        new_init_data = example_init_data()
        
        exp.initData = new_init_data
        exp.save()
        os.remove("./media/" + str(new_init_data.local_upload)) 
        plates_qs_3 = exp.plates.all()
        self.assertQuerysetEqual(Plate.objects.order_by('id')[Plate.objects.count()-3:Plate.objects.count()], 
            plates_qs_3, transform=lambda x:x)

    def testCreateSrcPlatesFromLibFile(self):
        exp = ExperimentFactory()
        with open('./test_data/example_library_plate_data.csv', newline='') as f:
            exp.createSrcPlatesFromLibFile(2, f)
        src_plates = exp.plates.filter(isSource=True)
        self.assertEquals(2, src_plates.count())
        plate_1_compounds = src_plates[0].compounds
        plate_2_compounds = src_plates[1].compounds
        self.assertEquals(plate_1_compounds.count(), 768/2)
        self.assertEquals(plate_2_compounds.count(), 768/2)

        self.assertQuerysetEqual(
            plate_1_compounds, 
            Compound.objects.filter(my_wells__plate=src_plates[0].id).order_by('my_wells__name'), transform=lambda x:x)
        self.assertQuerysetEqual(
            plate_2_compounds, 
            Compound.objects.filter(my_wells__plate=src_plates[1].id).order_by('my_wells__name'), transform=lambda x:x)

    def testMatchSrcWellsToSoaks(self):
        exp = experiment_with_source_plates()

        exp.matchSrcWellsToSoaks()
        self.assertEquals(exp.usedSoaks.count() , exp.srcWells.filter(soak__isnull=False).count())
        self.assertTrue(exp.soaksValid)

    def testInterleaveSrcWellsToSoaks(self):
        exp = experiment_with_source_plates()

        exp.interleaveSrcWellsToSoaks()
        self.assertEquals(exp.usedSoaks.count() , exp.srcWells.filter(soak__isnull=False).count())
        self.assertTrue(exp.soaksValid)

        exp.interleaveSrcWellsToSoaks()
        self.assertEquals(exp.usedSoaks.count() , exp.srcWells.filter(soak__isnull=False).count())
        self.assertTrue(exp.soaksValid)

    def testPriorityInterleaveSrcWellsToSoaks(self):
        exp = experiment_with_source_plates()
        wells = [w for w in exp.srcWellsWithCompounds]
        for w in wells:
            w.priority = randint(1, 10)

        Well.objects.bulk_update(wells,['priority'])

        exp.priorityInterleaveSrcWellsToSoaks()
        self.assertEquals(exp.usedSoaks.count() , exp.srcWells.filter(soak__isnull=False).count())
        self.assertTrue(exp.soaksValid)
        exp_soaks = exp.soaks.select_related('src', 'dest__parentWell').order_by('src__name')

    def testGetSoakPlatePairs(self):
        exp = experiment_with_matched_soaks()
        pairs = exp.getSoakPlatePairs()
        self.assertEquals(
            [(pair[0].name, pair[1].name) for pair in pairs], 
            [('src_1', 'dest_1')]
        )

        exp.interleaveSrcWellsToSoaks()
        pairs = exp.getSoakPlatePairs()
        self.assertEquals(
            [(pair[0].name, pair[1].name) for pair in pairs], 
            [('src_1', 'dest_1'), ('src_2', 'dest_1')]
        )

class PlateTests(TestCase):
    def setUp(self):
        self.client = Client()

    def testDBConstraints(self):
        src_plate = SourcePlateFactory()
        src_plate.isTemplate = True 
        src_plate.save()

        # Testing that on save, destination plates (isSource=False) cannot also be templates (isTemplate=True)
        dest_plate = DestPlateFactory()
        error = None
        try:    
            with transaction.atomic():      
                dest_plate.isTemplate = True  
                dest_plate.save()
        except IntegrityError as e:
            error = e
        self.assertTrue(bool(error) and issubclass(type(error), IntegrityError)) # only source plates can have isTemplate=True
        dest_plate.isTemplate = False
        dest_plate.save() #now destination plate can be saved

        # Testing only dest plates can have rockMakerId
        error = None
        try:
            with transaction.atomic(): 
                src_plate.rockMakerId = 1
                src_plate.save()
        except IntegrityError as e:
            error = e 
        self.assertTrue(bool(error) and issubclass(type(error), IntegrityError))

        dest_plate.rockMakerId = 1
        dest_plate.save() #should be fine

    def testUpdateCompounds(self):
        compounds = make_n_compounds(384)
        src_plate = SourcePlateFactory()
        src_plate.updateCompounds(compounds)
        my_wells = src_plate.wells.filter(compound__isnull=False).select_related('compound')
        well_compounds = [w.compound for w in my_wells]
        self.assertEquals(compounds, well_compounds)
        compounds_dict = {}
        for w in my_wells:
            compounds_dict[w.compound.zinc_id] = w.name
        from my_utils.utility_functions import shuffleDict
        
        shuffled_compounds_dict = shuffleDict(compounds_dict)
        src_plate.updateCompounds(compounds, shuffled_compounds_dict)
        self.assertEquals([k for k, v in sorted(shuffled_compounds_dict.items(), key=lambda x: x[1])], 
            [c.zinc_id for c in src_plate.compounds])

    def testCopyCompoundsFromOtherPlate(self):
        compounds = make_n_compounds(384)
        src_plates = [SourcePlateFactory()]
        src_plates[0].updateCompounds(compounds)
        for i in range(1,5):
            src_plates.append(SourcePlateFactory())
            src_plates[i].copyCompoundsFromOtherPlate(src_plates[0])
            
        self.assertQuerysetEqual(
            src_plates[0].compounds.order_by('zinc_id'), 
            src_plates[len(src_plates) - 1].compounds.order_by('zinc_id'), 
            transform=lambda x: x)
        
        # Testing that source plates that aren't template (isTemplate=False), should raise Validation Error
        src_plate_non_template = SourcePlateFactory()
        src_plate_non_template.isTemplate = False
        src_plate_non_template.save()
        error = None
        try:
            with transaction.atomic():
                src_plate_non_template.updateCompounds(compounds)
                src_plates[len(src_plates) - 1].copyCompoundsFromOtherPlate(src_plate_non_template)
        except Exception as e:
            error = e
            self.assertEquals(type(error), AssertionError) #make sure error is AssertionError
        self.assertEquals(bool(error), True) #make sure some error is thrown and caught