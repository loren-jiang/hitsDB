from django.conf import settings
from django.db import models
from django.core.files.storage import get_storage_class
import boto3
import logging
from botocore.exceptions import ClientError
from .s3utils import PrivateMediaStorage, PublicMediaStorage
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.validators import FileExtensionValidator
from .s3utils import fs #filestorage
import uuid

def upload_local_path(instance, filename):
        return 'local/' +  user_folder_upload_path(instance, filename)

def user_folder_upload_path(instance, filename): 
    return user_upload_path(instance, filename) + 'user_folder/' + filename

def user_upload_path(instance, filename):
    return str(instance.owner.id) + '/'

class FileAbstract(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, related_name="%(app_label)s_%(class)s_related" , on_delete=models.CASCADE)
    upload = models.FileField(upload_to=user_folder_upload_path,storage=PublicMediaStorage(), null=True, blank=True)
    local_upload = models.FileField(upload_to=upload_local_path, storage=fs, null=True, blank=True)
    s3_fileName = models.CharField(max_length=100, default='')
    local_fileName = models.CharField(max_length=100, default='')
    key = models.UUIDField(default=uuid.uuid4, unique=True) #unique id to grab from s3 bucket

    class Meta:
        abstract=True

class PrivateFile(FileAbstract):
    # key = models.UUIDField(default=uuid.uuid4, unique=True) #unique id to grab from s3 bucket
    upload = models.FileField(upload_to=user_folder_upload_path,storage=PrivateMediaStorage())
    

class PrivateFileJSON(FileAbstract):
    # key = models.UUIDField(default=uuid.uuid4, unique=True) #unique id to grab from s3 bucket
    upload = models.FileField(validators=[FileExtensionValidator(['json'])], 
                                upload_to=user_folder_upload_path,storage=PrivateMediaStorage())
    local_upload = models.FileField(validators=[FileExtensionValidator(['json'])], 
                                upload_to=user_folder_upload_path,storage=fs) #TODO this json valdiation isnt working...
    class Meta(FileAbstract.Meta):
        constraints = [
            models.CheckConstraint(check=~models.Q(local_upload__in=['',None]) 
                | ~models.Q(upload__in=['',None]), name='has_upload'), 
        ]

class PublicFile(FileAbstract):
    class Meta(FileAbstract.Meta):
        constraints = [
            models.CheckConstraint(check=~models.Q(local_upload__in=['',None]) 
                | ~models.Q(upload__in=['',None]), name='has_upload'), 
        ]
