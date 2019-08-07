from storages.backends.s3boto3 import S3Boto3Storage
import boto3
from django.conf import settings
import logging
from botocore.exceptions import ClientError

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

# creates presigned url that expires for private s3 objects
def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = myS3Client()
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None
    # The response contains the presigned URL
    return response