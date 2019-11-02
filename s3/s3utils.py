from storages.backends.s3boto3 import S3Boto3Storage
import boto3
from django.conf import settings
import logging
from botocore.exceptions import ClientError
from django.core.files.storage import FileSystemStorage

fs = FileSystemStorage(location='media/')

def upload_local_path(instance, filename):
    """
    Local path to upload file to

    Parameters:
    instance (Model instance): Django model instance
    filename (string): file name

    Returns (string) upload path
    """
    return 'local/' +  user_file_upload_path(instance, filename)

def user_file_upload_path(instance, filename): 
    """
    Path to upload user file to user's upload folder

    Parameters:
    instance (Model instance): Django model instance
    filename (string): file name

    Returns (string) upload path
    """
    return user_upload_path(instance, filename) + filename

def user_upload_path(instance, filename):
    """
    Path to user's upload folder

    Parameters:
    instance (Model instance): Django model instance
    filename (string): file name

    Returns (string) upload path
    """
    return 'user_folder/' + str(instance.owner.id) + '/'



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

    Parameters::
    bucket_name (string): name of AWS s3 bucket
    object_name (string): name of object
    expiration (int): Time in seconds for the presigned URL to remain valid
    
    Returns (string) presigned URL as string. If error, returns None.
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