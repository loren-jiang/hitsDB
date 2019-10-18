from django.test import TestCase
from django.contrib.auth.models import User
from .models import Experiment, Plate, PlateType, Project
from import_ZINC.models import Library
from .test_data import plateData
# # Create your tests here.

class Tests(TestCase):
    def setUp(self):
        self.user = User.objects.get_or_create(username='testuser')[0]
        self.client.force_login(self.user)

        self.echo_src_plate = PlateType.createEchoSourcePlate()
        self.mrc3_dest_plate = PlateType.create96MRC3DestPlate()
        self.library = Library.objects.get_or_create(name="test_library")[0]

        self.project = Project.objects.get_or_create(
            name="test_proj",
            owner=self.user
        )[0]
        self.experiment = Experiment.objects.get_or_create(
            name="test_exp",
            project=self.project,
            protein="test_protein",
            owner=self.user,
            srcPlateType=self.echo_src_plate,
            destPlateType=self.mrc3_dest_plate,
            library=self.library
        )[0]

    def testExperimentMakePlates(self):
        
        def testExperimentMakePlates_(platesCreated, plate_type):
            self.assertEqual(len(platesCreated), 5)
            for p in platesCreated:
                wells = p.wells.filter()
                self.assertEqual(p.isSource, plate_type.isSource) #check correct source or dest label
                self.assertEqual(wells.count(), plate_type.numResWells) #check number of wells
                self.assertEqual(wells.count() * wells[0].numSubwells, plate_type.numSubwellsTotal) #check number of subwells

        testExperimentMakePlates_(self.experiment.makePlates(5, self.echo_src_plate), self.echo_src_plate)
        testExperimentMakePlates_(self.experiment.makePlates(5, self.mrc3_dest_plate), self.mrc3_dest_plate)
    
    # def testCreateExperimentPlatesFromPlateDataJSON(self):
    #     self.experiment.plateData = plateData

    #     def createPlatesFromPlateDataJSON(exp, plate_type):
    #         numPlates = len(exp.plateData.keys())
    #         exp.makePlates(numPlates, plate_type)

    #     createPlatesFromPlateDataJSON(self.experiment, self.mrc3_dest_plate)

    #     self.experiment.save()
