from storages.backends.s3boto3 import S3Boto3Storage
import boto3
from django.conf import settings

# StaticS3BotoStorage = lambda: S3Boto3Storage(location='static')
# MediaS3BotoStorage = lambda: S3Boto3Storage(location='media')

class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False

class PublicMediaStorage(S3Boto3Storage):
    location = settings.AWS_PUBLIC_MEDIA_LOCATION
    file_overwrite = False

class PrivateMediaStorage(S3Boto3Storage):
    location = settings.AWS_PRIVATE_MEDIA_LOCATION
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False

def myS3Resource(key_id=settings.AWS_ACCESS_KEY_ID, access_key=settings.AWS_SECRET_ACCESS_KEY):
    return boto3.resource('s3',
        aws_access_key_id=key_id,
        aws_secret_access_key=access_key)

def myS3Client(key_id=settings.AWS_ACCESS_KEY_ID, access_key=settings.AWS_SECRET_ACCESS_KEY):
    return boto3.client('s3',
        aws_access_key_id=key_id,
        aws_secret_access_key=access_key)