from django.shortcuts import render
import boto3
from django.conf import settings
from botocore.exceptions import ClientError
from s3.s3utils import myS3Client, myS3Resource, create_presigned_url
from django.views.generic.edit import FormView
# from s3.models import PrivateImage
from s3.forms import FileFieldForm
import logging
from s3.models import WellImage
from experiment.models import Plate
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

# upload multiple image view
class FileFieldView(FormView):
    form_class = FileFieldForm
    template_name = './s3/private_files_upload.html'  # Replace with your template.
    success_url = '/'  # Replace with your URL or reverse().

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file_field')
        if form.is_valid():
            for f in files:
                new_image = WellImage(upload=f, owner=request.user)
                new_image.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

# Create your views here.
def imageGUIView(request, *args, **kwargs):
    s3 = myS3Resource()
    bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
    plate_id = kwargs['plate_id']
    user_id = kwargs['user_id']
    file_name = kwargs['file_name']

    well_name = file_name.split("_")[0]
    subwell_idx = int(file_name.split("_")[1])
    p = get_object_or_404(Plate,id=plate_id)
    p_well_images= p.well_images.all()
    s_w = p.wells.get(name=well_name).subwells.get(idx=subwell_idx)
    soak = s_w.soak
    soakX = soak.soakOffsetX
    soakY = soak.soakOffsetY

    def render_view(user_id, plate_id, file_name, soakX, soakY):
        if request.user.id == int(user_id): #users can only see their own images
            file_names = [w.file_name for w in p_well_images]
            prefix = 'media/private/private/' + str(user_id) + '/' + str(plate_id) + '/'
            obj_keys = []
            for obj in bucket.objects.filter(Prefix=prefix): 
                # check that the object key belongs to the requesting user
                obj_keys.append(obj.key)

            if obj_keys:
                curr_image_key = prefix + str(p_well_images.filter(file_name=file_name)[0].key)
                # curr_key_idx = obj_keys.index(curr_image_key)
                # prev_image_key = obj_keys[curr_key_idx-1]
                # next_image_key = obj_keys[(curr_key_idx+1) % len(obj_keys)]
                image_url = create_presigned_url(settings.AWS_STORAGE_BUCKET_NAME, curr_image_key, 4000)

                curr_well_name_idx = file_names.index(file_name)
                prev_well = file_names[curr_well_name_idx-1]
                next_well = file_names[(curr_well_name_idx+1)%len(file_names)]
            data = {
                # "response": response,
                # "prev_image_key":prev_image_key,
                # "next_image_key":next_image_key,
                "prev_well":prev_well,
                "image_url":image_url,
                "next_well":next_well,
                "keys": obj_keys,
                "file_name":file_name,
                "user_id":user_id,
                "plate_id":plate_id,
                "soakX" : soakX,
                "soakY" : soakY,
                "file_names":file_names,
            }
            return render(request, "xtal_img/imageGUI.html", data)
        else:
            return HttpResponse("bad request")

    if request.method == 'POST':
        soak.soakOffsetX = request.POST.get("soak-x",0.00)
        soak.soakOffsetY = request.POST.get("soak-y",0.00)
        soak.save()
        return render_view(user_id,plate_id,file_name,soak.soakOffsetX, soak.soakOffsetY)
    else: #request.method == 'GET'
        return render_view(user_id,plate_id,file_name,soak.soakOffsetX,soak.soakOffsetY)
