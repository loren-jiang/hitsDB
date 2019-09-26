from django.db import models
from s3.models import PrivateFile
from experiment.models import Plate

# Create your models here.

#extends S3.models PrivateFile class
class DropImage(PrivateFile):
    # Fields inherited from PrivateFile parent class
    # uploaded_at = models.DateTimeField(auto_now_add=True)
    # key = models.UUIDField(default=uuid.uuid4, unique=True) #unique id to grab from s3 bucket
    # owner = models.ForeignKey(User, related_name='well_images', on_delete=models.SET_NULL, null=True, blank=True)
    # upload = models.ImageField(upload_to=upload_path,storage=PrivateMediaStorage())

    plate_from = models.ForeignKey(Plate, related_name='drop_images', on_delete=models.SET_NULL, null=True, blank=True)
    well_name = models.CharField(max_length=10)  # e.g. A_01; regex [a-zA-Z]{1,2}_[123]{1}
    
    def __str__(self):
        return self.well_name