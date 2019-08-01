from django.shortcuts import render
import boto3
from django.conf import settings
from botocore.exceptions import ClientError
from s3.s3utils import myS3Client, myS3Resource
from s3.models import PrivateFile

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

# Create your views here.
def imageGUIView(request, curr_image_key="media/private/test-gui-images/A01_2.jpg"):
    s3 = myS3Resource()
    bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
    prefix = 'media/private/test-gui-images/' #change to folder name in future implementation
    obj_keys = []
    for obj in bucket.objects.filter(Prefix=prefix): 
        # check that the object key belongs to the requesting user
        obj_keys.append(obj.key)
    # folder_key = obj_keys.pop(0) #remove folder key 
    
    if obj_keys:
        # curr_image_key = "media/testing-gui/A05_2.jpg"
        curr_key_idx = obj_keys.index(curr_image_key)
        prev_image_key = obj_keys[curr_key_idx-1]
        next_image_key = obj_keys[(curr_key_idx+1) % len(obj_keys)]
        image_url = create_presigned_url(settings.AWS_STORAGE_BUCKET_NAME, curr_image_key, 4000)

    data = {
        # "response": response,
        "prev_image_key":prev_image_key,
        "image_url":image_url,
        "next_image_key":next_image_key,
        "keys": obj_keys,
    }
    return render(request, "xtal_img/imageGUI.html", data)