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
        # lib2 = LibraryFactory(compounds=make_n_compounds(randint(100,1000)))
        init_data1 = example_init_data()
        # init_data2 = example_init_data()

        exp = ExperimentFactory(library=lib1)
        exp.initData = init_data1
        exp.save()
        self.assertEquals(exp.prev_library_id, lib1.id) #library id taken note of
        self.assertEquals(exp.prev_initData_id, exp.initData.id) #library id taken note of
        os.remove("./media/" + str(exp.initData.local_upload)) 
        
        same_exp = Experiment.objects.filter(id=exp.id)
        # exp.library = lib2
        # exp.save()  
        # self.assertEquals(exp.prev_library_id, lib2.id) #library id taken note of

    def testInitDataPostSignal(self):
        # exp = ExperimentFactory()
        # init_data = example_init_data()
        # exp.initData = init_data
        # exp.save()
        # os.remove("./media/" + str(init_data.local_upload)) 
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
        # used_soak_src_wells = [s.src for s in exp.usedSoaks.select_related('src')]
        self.assertEquals(exp.usedSoaks.count() , exp.srcWells.filter(soak__isnull=False).count())
        self.assertTrue(exp.soaksValid)

        # delete first destination plate; should still work
        exp.plates.filter(isSource=False).first().delete()
        exp.interleaveSrcWellsToSoaks()
        used_soak_src_wells = [s.src for s in exp.usedSoaks.select_related('src')]
        self.assertEquals(exp.usedSoaks.count() , exp.srcWells.filter(soak__isnull=False).count())
        self.assertTrue(exp.soaksValid)

    def testGetSoakPlatePairs(self):
        exp = experiment_with_matched_soaks()
        pairs = exp.getSoakPlatePairs()
        print(pairs)

        exp.interleaveSrcWellsToSoaks()
        pairs = exp.getSoakPlatePairs()
        print(pairs)

    # def setUp(self):
    #     self.user = User.objects.get_or_create(username='testuser')[0]
    #     self.echo_src_plate = PlateType.createEchoSourcePlate()
    #     self.mrc3_dest_plate = PlateType.create96MRC3DestPlate()
    #     self.library = Library.objects.get_or_create(name="test_library")[0]
    #     self.project = Project.objects.get_or_create(name="test_proj", owner=self.user)[0]
    #     self.experiment = Experiment.objects.get_or_create(
    #         name="test_exp",
    #         project=self.project,
    #         protein="test_protein",
    #         owner=self.user,
    #         srcPlateType=self.echo_src_plate,
    #         destPlateType=self.mrc3_dest_plate,
    #         library=self.library,
    #     )[0]
    #     self.client = Client()

    # def testExperimentMethods(self):
    #     exp = self.experiment
    #     num = 3
    #     exp.makePlates(num, self.mrc3_dest_plate) #make 3 mrc3 dest plates 
    #     exp.makePlates(num, self.echo_src_plate) #make 3 echo source plates 

    #     """Check various instance properties """        
    #     # Case: check destSubwells
    #     with self.assertNumQueries(1):
    #         self.assertEqual(exp.destSubwells.count(), num*96*3)
            
    #     # Case: check srcWells
    #     with self.assertNumQueries(1):
    #         self.assertEqual(exp.srcWells.count(), num*384)


    # def testPlateWellSubwell(self):
    #     exp = self.experiment
    #     platesMade = exp.makePlates(3, self.mrc3_dest_plate)
    #     self.assertEqual(len(platesMade), 3)
    #     for p in platesMade:    
    #         wells = p.wells.filter()
    #         self.assertEqual(p.isSource, False) #check correct source or dest label
    #         self.assertEqual(wells.count(), 96) #check number of wells
    #         self.assertEqual(SubWell.objects.filter(parentWell__in=wells).count(), 96*3) #check number of subwells

    #     """Test DB contraints on Plate"""
    #     # Case: duplicate key value violates unique constraint "unique_src_dest_plate_idx"
    #     try:
    #         test_plate = Plate(plateType=self.mrc3_dest_plate, experiment_id=exp.id,
    #             isSource=self.mrc3_dest_plate.isSource, plateIdxExp=1)
    #         with transaction.atomic():
    #             test_plate.save()
    #     except Exception as e:
    #         self.assertEqual(IntegrityError, type(e)) # django.db.utils.IntegrityError: duplicate key value violates unique constraint "unique_src_dest_plate_idx"
    #     # Case: 

    #     """Test DB constraints on Well"""
    #     # Case: bad name that doesn't match regex validator on field 'name'
    #     try:
    #         test_plate = Plate(name='test_plate',plateType=self.mrc3_dest_plate, experiment_id=exp.id,
    #             isSource=self.mrc3_dest_plate.isSource, plateIdxExp=exp.plates.all().last().plateIdxExp + 1)
    #         test_plate.save()
    #         test_well_1 = Well(name='A01', wellIdx=1, wellRowIdx=1, wellColIdx=1, maxResVol=130, minResVol=10, plate_id=test_plate.id)
    #         test_well_2 = Well(name='A01', wellIdx=2, wellRowIdx=1, wellColIdx=2, maxResVol=130, minResVol=10, plate_id=test_plate.id)

    #         with transaction.atomic():
    #             test_well_1.save()
    #             test_well_2.save()
    #     except IntegrityError as e:
    #         self.assertEqual(IntegrityError, type(e))

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