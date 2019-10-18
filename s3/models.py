from django.conf import settings
from django.db import models
from django.core.files.storage import get_storage_class
import boto3
import logging
from botocore.exceptions import ClientError
from .s3utils import PrivateMediaStorage
from django.contrib.auth.models import User
from experiment.models import Plate, Well, SubWell
from django.core.files.storage import FileSystemStorage

import uuid

fs = FileSystemStorage(location='media/')

def upload_local_path(instance, filename):
        return 'local/' +  str(instance.owner.id)+ '/' +str(instance.plate.id)+ '/'+ str(instance.file_name)

def upload_path(instance, filename):
    return 'private/' +  str(instance.owner.id)+ '/' +str(instance.plate.id)+ '/'+ str(instance.key)

class WellImage(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    key = models.UUIDField(default=uuid.uuid4, unique=True) #unique id to grab from s3 bucket
    owner = models.ForeignKey(User, related_name='well_images', on_delete=models.SET_NULL, null=True, blank=True)
    upload = models.ImageField(upload_to=upload_path,storage=PrivateMediaStorage(), null=True, blank=True)
    plate = models.ForeignKey(Plate, related_name='well_images', on_delete=models.SET_NULL, null=True, blank=True)
    file_name = models.CharField(max_length=10) # e.g. A_01
    useS3 = models.BooleanField(default=True)
    local_upload = models.ImageField(upload_to=upload_local_path,storage=fs, null=True, blank=True)

    def __str__(self):
        return self.file_name

    class Meta:
        ordering = ('file_name',)

# contains images appropriately named '[well]_[subwell].jpg' (i.e. 'A01_1.jpg')
class PrivateFile(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    key = models.UUIDField(default=uuid.uuid4, unique=True) #unique id to grab from s3 bucket
    owner = models.ForeignKey(User, related_name='files', on_delete=models.CASCADE)
    upload = models.FileField(upload_to=upload_path,storage=PrivateMediaStorage())


class PublicFile(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload = models.FileField()


# class S3PrivateFileField(models.FileField):
#     """
#     A FileField that gives the 'private' ACL to the files it uploads to S3, instead of the default ACL.
#     """
#     def __init__(self, verbose_name=None, name=None, upload_to='', storage=None, **kwargs):
#         if storage is None:
#             storage = get_storage_class()(acl='private')
#         super(S3PrivateFileField, self).__init__(verbose_name=verbose_name,
#                 name=name, upload_to=upload_to, storage=storage, **kwargs)
