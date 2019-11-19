from django.test import TestCase
from .factories import PrivateFileJSONFactory, PrivateFileCSVFactory
from .fixtures import make_file_models
from django.db import transaction
from django.db.utils import IntegrityError
from ..models import PrivateFileJSON, PrivateFileCSV

class FileModelTests(TestCase):
    
    def testJSONFileDBConstraints(self):
        json_file_model, csv_file_model = make_file_models()
        with transaction.atomic():
            error = None
            try:
                json_file_model.local_upload = None    
                json_file_model.save()
            except (IntegrityError) as e:
                error = e
            self.assertTrue(bool(error) and issubclass(type(error), IntegrityError)) #check constraint 'has_upload'

    def testCSVFileDBConstraints(self):
        json_file_model, csv_file_model = make_file_models()
        with transaction.atomic():
            error = None
            try: 
                csv_file_model.local_upload = None
                csv_file_model.save()
            except(IntegrityError) as e:
                error = e
            self.assertTrue(bool(error) and issubclass(type(error), IntegrityError)) #check constraint 'has_upload'
        with transaction.atomic():
            error = None
            try:
                csv_file_model.local_upload = json_file_model.local_upload
                csv_file_model.save()
            except (IntegrityError) as e:
                error = e
            self.assertTrue(bool(error) and issubclass(type(error), IntegrityError)) #check constraint 'endswith_csv'

        



