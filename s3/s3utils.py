from storages.backends.s3boto3 import S3Boto3Storage, SpooledTemporaryFile
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
import os

class CustomS3Boto3Storage(S3Boto3Storage):

    def _save_content(self, obj, content, parameters):
        """
        We create a clone of the content file as when this is passed to boto3 it wrongly closes
        the file upon upload where as the storage backend expects it to still be open
        """
        # Seek our content back to the start
        content.seek(0, os.SEEK_SET)

        # Create a temporary file that will write to disk after a specified size
        content_autoclose = SpooledTemporaryFile()

        # Write our original content into our copy that will be closed by boto3
        content_autoclose.write(content.read())

        # Upload the object which will auto close the content_autoclose instance
        super(CustomS3Boto3Storage, self)._save_content(obj, content_autoclose, parameters)

        # Cleanup if this is fixed upstream our duplicate should always close
        if not content_autoclose.closed:
            content_autoclose.close()


class PublicMediaStorage(CustomS3Boto3Storage):
    location = settings.AWS_PUBLIC_MEDIA_LOCATION
    file_overwrite = False

class PrivateMediaStorage(CustomS3Boto3Storage):
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