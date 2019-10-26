from django.test import TestCase
from django.contrib.auth.models import User
from experiment.models import Experiment, Plate, PlateType, Project, Soak
from import_ZINC.models import Library
from .test_init_data import test_init_data
from datetime import datetime
from django.utils.timezone import make_aware
from utility_functions import PIX_TO_UM, UM_TO_PIX, IMG_SCALE
from s3.models import PrivateFile, PrivateFileJSON
from django.core.files.uploadedfile import SimpleUploadedFile
import uuid
from django.db import transaction

# # Create your tests here.

class Tests(TestCase):
    @classmethod
    def setUp(cls):
        cls.user = User.objects.get_or_create(username='testuser')[0]
        

        cls.echo_src_plate = PlateType.createEchoSourcePlate()
        cls.mrc3_dest_plate = PlateType.create96MRC3DestPlate()
        cls.library = Library.objects.get_or_create(name="test_library")[0]

        cls.project = Project.objects.get_or_create(
            name="test_proj",
            owner=cls.user
        )[0]
        with open('./test_data/test_plate_data.json', 'r') as myfile:
            data = myfile.read()
            uploaded_file = SimpleUploadedFile("./test_data/test_plate_data.json", bytes(data, 'utf-8'), content_type="application/json")
            cls.test_init_file = PrivateFileJSON.objects.get_or_create(owner=cls.user, local_upload=uploaded_file)[0]

        cls.experiment = Experiment.objects.get_or_create(
            name="test_exp",
            project=cls.project,
            protein="test_protein",
            owner=cls.user,
            srcPlateType=cls.echo_src_plate,
            destPlateType=cls.mrc3_dest_plate,
            library=cls.library,
            initDataJSON = test_init_data
        )[0]

    # def testMakeExperimentPlates(self):
    #     self.client.force_login(self.user)
    #     def makeExperimentPlates(platesCreated, plate_type):
    #         self.assertEqual(len(platesCreated), 5)
    #         for p in platesCreated:
    #             wells = p.wells.filter()
    #             self.assertEqual(p.isSource, plate_type.isSource) #check correct source or dest label
    #             self.assertEqual(wells.count(), plate_type.numResWells) #check number of wells
    #             self.assertEqual(wells.count() * wells[0].numSubwells, plate_type.numSubwellsTotal) #check number of subwells

    #     makeExperimentPlates(self.experiment.makePlates(5, self.echo_src_plate), self.echo_src_plate)
    #     makeExperimentPlates(self.experiment.makePlates(5, self.mrc3_dest_plate), self.mrc3_dest_plate)
    
    # def testCreateSoaksFromInitFileJSON(self):
    #     self.client.force_login(self.user)
    #     def createPlatesSoaksFromInitDataJSON(self):
    #         exp = self.experiment
    #         init_data_plates = exp.initDataJSON.items()
    #         lst_plates = exp.makePlates(len(init_data_plates), self.mrc3_dest_plate)
    #         # lst_wells = [[w for w in p.wells.filter()] for p in lst_plates]
    #         soaks = []
    #         for i, (plate_id, plate_data) in enumerate(init_data_plates):
    #             id = plate_data.pop("plate_id", None) 
    #             date_time = plate_data.pop("date_time", None)
    #             plate = lst_plates[i]
    #             plate.rockMakerId = id
    #             plate.dateTime = make_aware(datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S.%f'))
    #             plate.save()

    #             # loop through well keys and create soaks w/ appropriate data
    #             for j, (well_key, well_data) in enumerate(plate_data.items()):
    #                 well_name, s_w_idx = well_key.split('_')
    #                 well = plate.wells.filter(name=well_name)[0]
    #                 s_w = well.subwells.get(idx=s_w_idx) 
    #                 soaks.append(Soak(
    #                     experiment_id = exp.id,
    #                     dest_id = s_w.id, 
    #                     drop_x = well_data['drop_x'] * PIX_TO_UM, 
    #                     drop_y = well_data['drop_y'] * PIX_TO_UM,
    #                     drop_radius = well_data['drop_radius'] * PIX_TO_UM,
    #                     well_x =  well_data['well_x'] * PIX_TO_UM, 
    #                     well_y =  well_data['well_y'] * PIX_TO_UM,
    #                     well_radius =  well_data['well_radius'] * PIX_TO_UM
    #                 ))         
    #         return Soak.objects.bulk_create(soaks)
        
    #     soaks = createPlatesSoaksFromInitDataJSON(self)

    #     soaks_from_experiment = [s for s in self.experiment.soaks.order_by('id')]
    #     self.assertEqual(soaks, soaks_from_experiment) #check soaks are create in DB

    def testProcessInitFileOnExperimentCreationSave(self):
        self.client.force_login(self.user)
        e1 = Experiment.objects.get_or_create(
            name="e1",
            project=self.project,
            protein="protein_1",
            owner=self.user,
            srcPlateType=self.echo_src_plate,
            destPlateType=self.mrc3_dest_plate,
            library=self.library,
            initData = self.test_init_file
        )[0]
        copy_initData = PrivateFileJSON.objects.filter(id=self.test_init_file.id).first()
        copy_initData.id = None
        copy_initData.key = uuid.uuid4()
        copy_initData.save()
        e1.initData = copy_initData
        e1.save()

        soaks_from_experiment = e1.soaks.order_by('id')
        self.assertEqual(288, soaks_from_experiment.count()) #check soaks are create in DB
        e1.name="e1_changed_name"
        e1.save()
        self.assertEqual([s for s in soaks_from_experiment], [s for s in e1.soaks.order_by('id')])

    def testDeletePlateSoaksOnLibChance(self):
        self.client.force_login(self.user)
        exp = self.experiment
        #create new Library from copy of self.library
        new_lib = Library.objects.filter(id=self.library.id).first()
        new_lib.id = None
        new_lib.name="new_lib"
        new_lib.save()
        
        #save new library to experiment
        exp.library = new_lib
        exp.save()
        #check that soaks and plates have been deleted
        self.assertEqual(0, exp.soaks.filter().count())
        self.assertEqual(0, Soak.objects.filter(experiment=exp.id).count())
        self.assertEqual(0, exp.plates.filter().count())
        self.assertEqual(0, Plate.objects.filter(experiment=exp.id).count())

    

