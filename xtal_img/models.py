from django.db import models
from botocore.exceptions import ClientError
from s3.s3utils import PrivateMediaStorage
from django.contrib.auth.models import User
from experiment.models import Plate
# from django.db.models.signals import post_save
# import boto3
# from django.conf import settings

# Create your models here.

def upload_path(instance, filename):
    return instance.bucket_key

class WellImage(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    bucket_key = models.CharField(max_length=1000, unique=True) #unique id to grab from s3 bucket
    owner = models.ForeignKey(User, related_name='well_images', on_delete=models.SET_NULL)
    upload = models.ImageField(upload_to=upload_path,storage=PrivateMediaStorage())
    plate = models.ForeignKey(Plate, related_name='well_images', on_delete=models.SET_NULL)
# # method for creating s3 object after WellImage save
# @receiver(post_save, sender=WellImage, dispatch_uid="make_s3_object")
# def create_s3_object(sender, instance, **kwargs):
            