from django.conf import settings
from django.db import models
from django.core.files.storage import get_storage_class
import boto3
import logging
from botocore.exceptions import ClientError
from .s3utils import PrivateMediaStorage
from django.contrib.auth.models import User
from experiment.models import Plate
from django.db.models.signals import post_save
from django.dispatch import receiver

def upload_path(instance, filename):
    return instance.bucket_key

# contains images appropriately named '[well]_[subwell].jpg' (i.e. 'A01_1.jpg')
class PrivateFile(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    bucket_key = models.CharField(max_length=1000)
    owner = models.ForeignKey(User, related_name='files', on_delete=models.CASCADE)
    upload = models.FileField(upload_to=upload_path,storage=PrivateMediaStorage())

class PublicFile(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload = models.FileField()

@receiver(post_save, sender=PrivateFile)
def generateBucketKey(sender, instance, created, **kwargs):


class S3PrivateFileField(models.FileField):
    """
    A FileField that gives the 'private' ACL to the files it uploads to S3, instead of the default ACL.
    """
    def __init__(self, verbose_name=None, name=None, upload_to='', storage=None, **kwargs):
        if storage is None:
            storage = get_storage_class()(acl='private')
        super(S3PrivateFileField, self).__init__(verbose_name=verbose_name,
                name=name, upload_to=upload_to, storage=storage, **kwargs)

# class MyModel(models.Model):
#     public_file = models.FileField(blank=True, null=True, upload_to='open/')
#     # private_file = models.FileField(blank=True, null=True, upload_to='seekrit/')
#     private_file = S3PrivateFileField(blank=True, null=True, upload_to='seekrit/')
#     uploaded_at = models.DateTimeField(auto_now_add=True)

#     def save(self, *args, **kwargs):
#         super(MyModel, self).save(*args, **kwargs)
#         # if self.private_file:
#         #     fileName = settings.MEDIA_DIRECTORY + self.private_file
#         #     s3 = boto3.resource('s3')
#         #     bucket = s3.Bucket('settings.AWS_STORAGE_BUCKET_NAME')
#         #     upload_file(fileName, bucket)
#             # upload_file()
#             # conn = boto.s3.connection.S3Connection(
#             #                     settings.AWS_ACCESS_KEY_ID,
#             #                     settings.AWS_SECRET_ACCESS_KEY)
#             # # If the bucket already exists, this finds that, rather than creating.
#             # bucket = conn.create_bucket(settings.AWS_STORAGE_BUCKET_NAME)
#             # k = boto3.s3.key.Key(bucket)
#             # k.key = settings.MEDIA_DIRECTORY + self.private_file
#             # k.set_acl('private')


