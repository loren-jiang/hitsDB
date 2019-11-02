from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
# from .models import Experiment, Plate, PlateType, Project, Soak
from lib.models import Library
# from .test_init_data import test_init_data
from datetime import datetime
from django.utils.timezone import make_aware
from s3.models import PrivateFile, PrivateFileJSON
from django.core.files.uploadedfile import SimpleUploadedFile
import uuid
from django.db import transaction
from django.db import IntegrityError

# # Create your tests here.

class Tests(TestCase):
    @classmethod
    def setUp(cls):
        cls.user = User.objects.get_or_create(username='testuser')[0]
        

        # cls.echo_src_plate = PlateType.createEchoSourcePlate()
        # cls.mrc3_dest_plate = PlateType.create96MRC3DestPlate()
        # cls.library = Library.objects.get_or_create(name="test_library")[0]

        # cls.project = Project.objects.get_or_create(
        #     name="test_proj",
        #     owner=cls.user
        # )[0]
        

        # cls.experiment = Experiment.objects.get_or_create(
        #     name="test_exp",
        #     project=cls.project,
        #     protein="test_protein",
        #     owner=cls.user,
        #     srcPlateType=cls.echo_src_plate,
        #     destPlateType=cls.mrc3_dest_plate,
        #     library=cls.library,
        #     initDataJSON = test_init_data
        # )[0]

    def testFileUploadValidations(self):
        self.client.force_login(self.user)

        #test PrivateFileJSON upload file field only accepts JSON file
        with open('./test_data/test_plate_data_copy.txt', 'r') as f:
            data = f.read()
            uploaded_file = SimpleUploadedFile("./test_data/test_plate_data_copy.txt", bytes(data, 'utf-8'), content_type="application/text")
        
        test_json_file = PrivateFileJSON(owner=self.user)
        try:
            with transaction.atomic():
                test_json_file.save()   
            integrity_error = 0 
        except IntegrityError:
            integrity_error = 1
        
        self.assertEquals(integrity_error, 1)
        
        test_json_file_ = PrivateFileJSON(owner=self.user, local_upload=uploaded_file)
        try:
            with transaction.atomic():
                test_json_file_.save()   
            integrity_error = 0 
        except IntegrityError:
            integrity_error = 1
        #print(test_json_file_.local_upload)
        self.assertEquals(integrity_error, 0)
        

