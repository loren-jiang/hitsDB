from django.test import TestCase
from django.contrib.auth.models import User
from experiment.models import Experiment, Plate, PlateType, Project, Soak, SubWell, Well
from import_ZINC.models import Library, Compound
from datetime import datetime
from django.utils.timezone import make_aware
# from utility_functions import PIX_TO_UM, UM_TO_PIX, IMG_SCALE
# from s3.models import PrivateFile, PrivateFileJSON
# from django.core.files.uploadedfile import SimpleUploadedFile
# import uuid
from django.db import transaction
from django.db.utils import IntegrityError

class Tests(TestCase):
    @classmethod
    def setUp(cls):
        cls.user = User.objects.get_or_create(username='testuser')[0]
        cls.echo_src_plate = PlateType.createEchoSourcePlate()
        cls.mrc3_dest_plate = PlateType.create96MRC3DestPlate()
        cls.library = Library.objects.get_or_create(name="test_library")[0]
        cls.project = Project.objects.get_or_create(name="test_proj", owner=cls.user)[0]
        cls.experiment = Experiment.objects.get_or_create(
            name="test_exp",
            project=cls.project,
            protein="test_protein",
            owner=cls.user,
            srcPlateType=cls.echo_src_plate,
            destPlateType=cls.mrc3_dest_plate,
            library=cls.library,
        )[0]

    def testExperimentMethods(self):
        exp = self.experiment
        num = 3
        exp.makePlates(num, self.mrc3_dest_plate) #make 3 mrc3 dest plates 
        exp.makePlates(num, self.echo_src_plate) #make 3 echo source plates 

        """Check various instance properties """        
        # Case: check destSubwells
        with self.assertNumQueries(1):
            self.assertEqual(exp.destSubwells.count(), num*96*3)
            
        # Case: check srcWells
        with self.assertNumQueries(1):
            self.assertEqual(exp.srcWells.count(), num*384)


    def testPlateWellSubwell(self):
        exp = self.experiment
        platesMade = exp.makePlates(3, self.mrc3_dest_plate)
        self.assertEqual(len(platesMade), 3)
        for p in platesMade:
            wells = p.wells.filter()
            self.assertEqual(p.isSource, False) #check correct source or dest label
            self.assertEqual(wells.count(), 96) #check number of wells
            self.assertEqual(SubWell.objects.filter(parentWell__in=wells).count(), 96*3) #check number of subwells

        """Test DB contraints on Plate"""
        # Case: duplicate key value violates unique constraint "unique_src_dest_plate_idx"
        try:
            test_plate = Plate(plateType=self.mrc3_dest_plate, experiment_id=exp.id,
                isSource=self.mrc3_dest_plate.isSource, plateIdxExp=1)
            with transaction.atomic():
                test_plate.save()
        except Exception as e:
            self.assertEqual(IntegrityError, type(e)) # django.db.utils.IntegrityError: duplicate key value violates unique constraint "unique_src_dest_plate_idx"
        # Case: 

        """Test DB constraints on Well"""
        # Case: bad name that doesn't match regex validator on field 'name'
        try:
            test_plate = Plate(name='test_plate',plateType=self.mrc3_dest_plate, experiment_id=exp.id,
                isSource=self.mrc3_dest_plate.isSource, plateIdxExp=exp.plates.all().last().plateIdxExp + 1)
            test_plate.save()
            test_well_1 = Well(name='A01', wellIdx=1, wellRowIdx=1, wellColIdx=1, maxResVol=130, minResVol=10, plate_id=test_plate.id)
            test_well_2 = Well(name='A01', wellIdx=2, wellRowIdx=1, wellColIdx=2, maxResVol=130, minResVol=10, plate_id=test_plate.id)

            with transaction.atomic():
                test_well_1.save()
                test_well_2.save()
        except IntegrityError as e:
            self.assertEqual(IntegrityError, type(e))
