from django.conf import settings
from django.db import models
from django.core.files.storage import get_storage_class
import boto3
import logging
from botocore.exceptions import ClientError
from .s3utils import PrivateMediaStorage
from django.contrib.auth.models import User


# class PrivateFolder(models.Model):
#     uploaded_at = models.DateTimeField(auto_now_add=True)
#     folderpath = models.FilePathField(storage=PrivateMediaStorage())
#     user = models.ForeignKey(User, related_name='files', on_delete=models.CASCADE)

class PrivateFile(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload = models.FileField(storage=PrivateMediaStorage())
    owner = models.ForeignKey(User, related_name='files', on_delete=models.CASCADE)

class PublicFile(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload = models.FileField()



# def sync_to_s3(target_dir, aws_region=AWS_REGION, bucket_name=BUCKET_NAME):
#     if not os.path.isdir(target_dir):
#         raise ValueError('target_dir %r not found.' % target_dir)

#     s3 = boto3.resource('s3', region_name=aws_region)
#     try:
#         s3.create_bucket(Bucket=bucket_name,
#                          CreateBucketConfiguration={'LocationConstraint': aws_region})
#     except ClientError:
#         pass

#     for filename in os.listdir(target_dir):
#         logger.warn('Uploading %s to Amazon S3 bucket %s' % (filename, bucket_name))
#         s3.Object(bucket_name, filename).put(Body=open(os.path.join(target_dir, filename), 'rb'))

#         logger.info('File uploaded to https://s3.%s.amazonaws.com/%s/%s' % (
#             aws_region, bucket_name, filename))

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


