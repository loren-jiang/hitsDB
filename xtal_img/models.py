from django.db import models
from s3.models import PrivateFile, upload_path
from experiment.models import Plate
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from s3.s3utils import PrivateMediaStorage
import uuid


# Create your models here.

fs = FileSystemStorage(location='media/')

def upload_local_path(instance, filename):
        return 'local/' +  str(instance.owner.id)+ '/' +str(instance.plate.id)+ '/'+ str(instance.well_name)

class DropImageS3(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    key = models.UUIDField(default=uuid.uuid4, unique=True) #unique id to grab from s3 bucket
    owner = models.ForeignKey(User, related_name='drop_images_s3', on_delete=models.SET_NULL, null=True, blank=True)
    upload = models.ImageField(upload_to=upload_path,storage=PrivateMediaStorage())

    plate = models.ForeignKey(Plate, related_name='drop_images_s3', on_delete=models.SET_NULL, null=True, blank=True)
    well_name = models.CharField(max_length=10)  # e.g. A_01; regex [a-zA-Z]{1,2}_[123]{1}
    
    def __str__(self):
        return self.well_name

#DropImage that is stored locally
class DropImage(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, related_name='drop_images', on_delete=models.SET_NULL, null=True, blank=True)
    upload = models.ImageField(upload_to=upload_local_path,storage=fs)

    plate = models.ForeignKey(Plate, related_name='drop_images', on_delete=models.SET_NULL, null=True, blank=True)
    well_name = models.CharField(max_length=10)  # e.g. A_01; regex [a-zA-Z]{1,2}_[123]{1}
    
    def __str__(self):
        return self.well_name