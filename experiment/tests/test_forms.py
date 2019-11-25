from django.test import TestCase
from experiment.models import Experiment, Plate, PlateType, Project, Soak, SubWell, Well
from django.contrib.auth.models import User, Group
from lib.models import Library, Compound

from django.db import transaction
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

from django.test import Client
from ..forms import CreateSrcPlatesMultiForm

from .factories import PlateFactory, SourcePlateFactory, DestPlateFactory, ExperimentFactory
from django.core.files.uploadedfile import SimpleUploadedFile

class ExperimentMultiFormsTests(TestCase):
    def setUp(self):
        self.client = Client()
    
    def testCreateSrcPlatesMultiForm(self):

        ### Case: Good form for creating source plates from .csv file ###
        form_data = {
            'numSrcPlates': 2,
            'action': 'platelibform',
            }
        f = open('./test_data/example_library_plate_data.csv', 'r')
        good_file = SimpleUploadedFile('good_file.csv', f.read().encode('utf-8'), content_type="text/csv")
        form_file = {'plateLibDataFile': good_file}
        form = CreateSrcPlatesMultiForm(exp=ExperimentFactory(), data=form_data, files=form_file)
        self.assertTrue(form.is_valid())
        f.close()

        ### Case: Wrong file type ###
        f = open('./test_data/wrong_example_library_plate_data.json', 'r')
        wrong_file = SimpleUploadedFile('wrong_example_library_plate_data.json',
            f.read().encode('utf-8'), content_type="text/json")
        form_file.update({'plateLibDataFile' : wrong_file})
        form = CreateSrcPlatesMultiForm(exp=ExperimentFactory(), data=form_data, files=form_file)
        self.assertFalse(form.is_valid())
        f.close()

        ### Case: Bad headers in .csv ###
        f = open('./test_data/example_library_plate_data_bad_headers.csv', 'r')
        wrong_file = SimpleUploadedFile('example_library_plate_data_bad_headers.csv',
            f.read().encode('utf-8'), content_type="text/json")
        form_file.update({'plateLibDataFile' : wrong_file})
        form = CreateSrcPlatesMultiForm(exp=ExperimentFactory(), data=form_data, files=form_file)
        self.assertFalse(form.is_valid())
        print(form.errors)
        f.close()
        
        # ### Case: Too big file ###
        # f = open('./test_data/too_big_file.csv', 'r')
        # big_file = SimpleUploadedFile('too_big_file.csv', 
        #     f.read().encode('utf-8'), content_type="text/csv")
        # form_file.update({'plateLibDataFile' : big_file})
        # form = CreateSrcPlatesMultiForm(exp=ExperimentFactory(), data=form_data, files=form_file)
        # print(form.errors)
        # self.assertFalse(form.is_valid())
        # f.close()
        

        
            