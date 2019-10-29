from django.db import models
from s3.models import PrivateFile
from experiment.models import Plate
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from s3.s3utils import PrivateMediaStorage, user_files_upload_path, fs, user_upload_path
import uuid

def upload_local_path(instance, file):
        return 'local/' +  user_upload_path(instance, file) + str(instance.plate.id)+ '/'+ str(instance.file_name)

def well_image_upload_path(instance, file):
    return user_upload_path(instance, file) + str(instance.plate.id) + '/' + str(instance.key)

# Create your models here
class DropImage(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    key = models.UUIDField(default=uuid.uuid4, unique=True) #unique id to grab from s3 bucket
    owner = models.ForeignKey(User, related_name='drop_images', on_delete=models.SET_NULL, null=True, blank=True)
    upload = models.ImageField(upload_to=well_image_upload_path,storage=PrivateMediaStorage())
    file_name = models.CharField(max_length=5)
    # file_name = models.CharField(max_length=5, validators=[RegexValidator(regex='^[A-Z]\d{1,2}_[123]', 
        # message='Enter valid file name, e.g. A_01_2')])  #should be well name + subwell idx; e.g. A_01_2
    plate = models.ForeignKey(Plate, related_name='drop_images', on_delete=models.SET_NULL, null=True, blank=True)
    useS3 = models.BooleanField(default=True) #if True, then use s3 upload; if False, use local_upload
    local_upload = models.ImageField(upload_to=upload_local_path,storage=fs, null=True, blank=True)
    
    def __str__(self):
        return self.file_name

    class Meta:
        ordering=('file_name',)
