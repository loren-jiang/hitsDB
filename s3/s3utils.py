from storages.backends.s3boto3 import S3Boto3Storage
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