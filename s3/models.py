from django.conf import settings
from django.db import models
from django.core.files.storage import get_storage_class
import boto3
import logging
from .s3utils import PrivateMediaStorage, PublicMediaStorage
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.validators import FileExtensionValidator
from .s3utils import fs #filestorage
import uuid

def upload_local_path(instance, filename):
        return 'local/' +  user_file_upload_path(instance, filename)

def user_file_upload_path(instance, filename): 
    if instance.key:
        if instance.filetype:
            return user_upload_path(instance, filename) + str(instance.key) + instance.filetype
        return user_upload_path(instance, filename) + str(instance.key)
    return user_upload_path(instance, filename) + filename

def user_upload_path(instance, filename):
    return 'user_folder/' + str(instance.owner.id) + '/'

def has_upload_constraint(name='has_upload'):
    return models.CheckConstraint(check=~(models.Q(local_upload__in=['',None]) 
                & models.Q(upload__in=['',None])), name=name)

class FileAbstract(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, related_name="%(app_label)s_%(class)s_related" , on_delete=models.CASCADE)
    upload = models.FileField(upload_to=user_file_upload_path,storage=PublicMediaStorage(), null=True, blank=True)
    local_upload = models.FileField(upload_to=upload_local_path, storage=fs, null=True, blank=True)
    key = models.UUIDField(default=uuid.uuid4, unique=True) #unique id to grab from s3 bucket
    filetype = models.CharField(max_length=5, default='')
    filename = models.CharField(max_length=100, default='')
    
    class Meta:
        abstract=True

class PrivateFile(FileAbstract):
    upload = models.FileField(upload_to=user_file_upload_path,storage=PrivateMediaStorage())
    
class PrivateFileJSON(FileAbstract):
    upload = models.FileField(validators=[FileExtensionValidator(['json'])], 
                                upload_to=user_file_upload_path,storage=PrivateMediaStorage(),
                                null=True, blank=True)
    local_upload = models.FileField(validators=[FileExtensionValidator(['json'])], 
                                upload_to=upload_local_path,storage=fs,
                                null=True, blank=True)
    filetype = models.CharField(max_length=5, default='.json')
    class Meta(FileAbstract.Meta):
        constraints = [
            models.CheckConstraint(check=~(models.Q(local_upload__in=['',None]) 
                & models.Q(upload__in=['',None])), name='privatefilejson_has_upload'), 
            models.CheckConstraint(check=models.Q(local_upload__in=['', None]) | models.Q(local_upload__endswith='.json'), name='endswith_json'),
        ]

class PrivateFileCSV(FileAbstract):
    upload = models.FileField(validators=[FileExtensionValidator(['csv'])], 
                                upload_to=user_file_upload_path,storage=PrivateMediaStorage(), 
                                null=True, blank=True)
    local_upload = models.FileField(validators=[FileExtensionValidator(['csv'])], 
                                upload_to=upload_local_path,storage=fs, 
                                null=True, blank=True)
    filetype = models.CharField(max_length=5, default='.csv')    
    class Meta(FileAbstract.Meta):
        constraints = [
            has_upload_constraint(),
            models.CheckConstraint(check=models.Q(local_upload__endswith='.csv'), name='endswith_csv'),
        ]

class PublicFile(FileAbstract):
    class Meta(FileAbstract.Meta):
        constraints = [
            models.CheckConstraint(check=~models.Q(local_upload__in=['',None]) 
                | ~models.Q(upload__in=['',None]), name='publicfile_has_upload'), 
        ]
