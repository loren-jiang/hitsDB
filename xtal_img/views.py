from django.shortcuts import render
import boto3
from django.conf import settings
from botocore.exceptions import ClientError
from s3.s3utils import myS3Client, myS3Resource, create_presigned_url
from django.views.generic.edit import FormView
from s3.forms import ImagesFieldForm, FilesFieldForm
import logging
from s3.models import WellImage
# from .models import DropImageS3, DropImage
from experiment.models import Plate, Soak
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from .forms import DropImageUploadForm, SoakGUIForm
import copy 


import json
from django.core.serializers.json import DjangoJSONEncoder
# Create your views here.

def upload_drop_image(request):
    if request.method == 'POST':
        form = DropImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('')
    else:
        form = DropImageUploadForm()
    return render(request, 'basic_form.html', {
        'form': form
    })



@login_required(login_url="/login")
def s3ImageGUIView(request, *args, **kwargs):
    plate_id = kwargs['plate_id']
    user_id = kwargs['user_id']
    file_name = kwargs['file_name']
    well_name = file_name.split("_")[0]
    subwell_idx = int(file_name.split("_")[1])
    p = get_object_or_404(Plate,id=plate_id)
    p_well_images= p.well_images.all()
    useS3 = p_well_images[0].useS3
    target_well = p.wells.get(name=well_name)
    s_w = target_well.subwells.get(idx=subwell_idx)
    soak = s_w.soak

    form = SoakGUIForm(initial={
        'transferVol':soak.transferVol, 
        'soakOffsetX':soak.soakOffsetX, 
        'soakOffsetY':soak.soakOffsetY,
        'targetWellX':soak.targetWellX,
        'targetWellY':soak.targetWellY,
        'targetWellRadius':soak.targetWellRadius,
        'useSoak':soak.useSoak,})
    
    obj_keys = [w.key for w in p_well_images]
    file_names = [w.file_name for w in p_well_images]
    prefix_s3 = 'media/private/' + str(user_id) + '/' + str(plate_id) + '/'
    prefix_local = '/media/local/' + str(user_id) + '/' + str(plate_id) + '/'
    prefix = prefix_s3 if useS3 else prefix_local

    def get_prev_next_well(arr, f_n):
        i = arr.index(f_n)
        prv = arr[i-1]
        nxt = arr[(i+1)%len(arr)]
        return (prv, nxt)

    def render_view(user_id, plate_id, file_name, soak, form):

        if request.user.id == int(user_id): #users can only see their own images
            # obj_keys = []
            # for obj in bucket.objects.filter(Prefix=prefix): 
            #     # check that the object key belongs to the requesting user
            #     obj_keys.append(obj.key)
            soakXYVol = [soak.soakOffsetX, soak.soakOffsetY, soak.transferVol]
            targetWellXYRadius = [soak.targetWellX, soak.targetWellY, soak.targetWellRadius]
            context = {
                "prev_well":prev_well,
                "image_url":image_url,
                "next_well":next_well,
                "keys": obj_keys,
                "file_name":file_name,
                "user_id":user_id,
                "plate_id":plate_id,
                "soakX" : soakXYVol[0],
                "soakY" : soakXYVol[1],
                "transferVol": soakXYVol[2],
                "targetWellX" : targetWellXYRadius[0],
                "targetWellY" : targetWellXYRadius[1],
                "targetWellRadius": targetWellXYRadius[2],
                "file_names":file_names,
                "dont_show_path": True,
                "topSoakCircle": soakXYVol[1]-soakXYVol[2],
                "leftSoakCircle":soakXYVol[0]-soakXYVol[2],
                "sideSoakCircle":2*soakXYVol[2],
                # "radSoakCircle_": (2*soakXYVol[2] - 4) //2,
                "radSoakCircle_": soakXYVol[2],
                "topWellCircle": targetWellXYRadius[1] - targetWellXYRadius[2],
                "leftWellCircle": targetWellXYRadius[0] - targetWellXYRadius[2],
                "sideWellCircle":2*targetWellXYRadius[2],
                # "radWellCircle_": (2*targetWellXYRadius[2] - 4) //2,
                "radWellCircle_": targetWellXYRadius[2],
                'SoakGUIForm':form,
                "use_soak" : soak.useSoak, 
            }
            guiData = copy.deepcopy(context)
            guiData.pop('SoakGUIForm')
            context["guiData"] = json.dumps(guiData, cls=DjangoJSONEncoder)
            return render(request, "xtal_img/imageGUI.html", context)
        else:
            return HttpResponse("bad request")

    if obj_keys:
        curr_image_key = prefix + str(p_well_images.filter(file_name=file_name)[0].key)
        image_url_s3 = create_presigned_url(settings.AWS_STORAGE_BUCKET_NAME, curr_image_key, 4000)
        image_url_local = prefix + file_name 
        image_url = image_url_s3 if useS3 else image_url_local
        (prev_well, next_well) = get_prev_next_well(file_names, file_name)

    if request.method == 'POST':
        form = SoakGUIForm(request.POST)
        if (form.is_valid()):
            #process valid form 
            cleaned_data = form.cleaned_data
            for k in cleaned_data.keys():
                setattr(soak, k, cleaned_data.get(k))
            soak.save()
            # go to next well ion successful form submit
            arr_url = request.get_full_path().split('/')
            arr_url[len(arr_url) - 2] = next_well
            new_url = '/'.join(arr_url)
            if (request.POST.get('nextWellOnSave')):
                return redirect(new_url)
            else:
                return render_view(user_id,plate_id,file_name, soak, form)

        return render_view(user_id,plate_id,file_name, soak, form)
    else: #request.method == 'GET'
        return render_view(user_id,plate_id,file_name, soak, form)

