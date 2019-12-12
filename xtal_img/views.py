from django.shortcuts import render
import boto3
from django.conf import settings
from s3.s3utils import create_presigned_url
from django.views.generic.edit import FormView
from s3.forms import ImagesFieldForm, FilesFieldForm
from .models import DropImage
import logging
from experiment.models import Plate, Soak, Well
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from hitsDB.views_import import *
from .forms import DropImageUploadForm, SoakGUIForm
import copy 
from experiment.decorators import is_dest_plate
from my_utils.utility_functions import UM_TO_PIX, PIX_TO_UM, IMG_SCALE, STROKE_WIDTH, VolumeToRadius, RadiusToVolume, reshape
from django.db.models import F
from django.forms.models import model_to_dict

import json
from django.core.serializers.json import DjangoJSONEncoder
# Create your views here.

# def upload_drop_image(request):
#     if request.method == 'POST':
#         form = DropImageUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return HttpResponseRedirect(request.path_info)
#     else:
#         form = DropImageUploadForm()
#     return render(request, 'basic_form.html', {
#         'form': form
#     })

#loads drop images with corresponding model instance and associated plate id and user id 
class DropImagesUploadView(FormView):
    form_class = ImagesFieldForm
    template_name = './s3/private_images_upload.html'
    # template_name = 'modals/modal_form.html'

    def get_success_url(self):
        p = Plate.objects.get(id=self.kwargs['pk_plate'])
        if p:
            return reverse_lazy('exp', kwargs={'pk_exp':p.experiment.id, 'pk_proj':p.experiment.project.id})
        return HttpResponseRedirect(self.request.path_info)

    @method_decorator(is_dest_plate, login_required)
    def dispatch(self, *args, **kwargs):
        return super(DropImagesUploadView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk_plate', None)
        if pk:
            p = get_object_or_404(Plate, pk=pk)
            drop_images = p.drop_images.filter()
            form = self.get_form(self.get_form_class())
            context = {
                'form': form,
                'images': drop_images,
                'dont_show_path': True,
            }
            return render(request, './s3/private_images_upload.html', context)

    def post(self, request, *args, **kwargs):
        p = get_object_or_404(Plate, id=kwargs['pk_plate'])
        self.object = p
        if p.experiment.owner == request.user: #only the appropriate user can upload images 
            p.drop_images.remove(*[img for img in p.drop_images.all()])
            # p.drop_images.filter().delete() #delete well images associated with plate before uploading new ones
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            files = request.FILES.getlist('image_field')
            drop_images = []
            if form.is_valid():
                for f in files:
                    file_name = f.name.split('.')[0] #just get the file name, not the extension
                    if form.cleaned_data['use_local']:
                        new_file = DropImage(local_upload=f, owner=request.user, plate=p, file_name=file_name, useS3=False)
                    else:
                        new_file = DropImage(upload=f, owner=request.user, plate=p, file_name=file_name, useS3=True)
                    drop_images.append(new_file)
                    # new_file.save()
                DropImage.objects.bulk_create(drop_images)
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

from my_utils.my_views import AjaxableResponseMixin
class DropImagesUploadModalView(AjaxableResponseMixin, DropImagesUploadView):
    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk_plate', None)
        if pk:
            p = get_object_or_404(Plate, pk=pk)
            drop_images = p.drop_images.filter()
            form = self.get_form(self.get_form_class())
            context = {
                'form': form,
                'images': drop_images,
                'dont_show_path': True,
                'use_ajax':True,
                'modal_title':"Upload drop images",
                'action': reverse('drop_images_upload_modal', kwargs={'pk_plate':pk})
            }
            return render(request, 'xtal_img/drop_images_upload_modal.html', context)

@login_required(login_url="/login")
def DropImageViewGUI(request, *args, **kwargs):    
    plate_id = kwargs['plate_id']
    user_id = kwargs['user_id']
    file_name = kwargs['file_name']
    well_name = file_name.split("_")[0]
    subwell_idx = int(file_name.split("_")[1])
    p = get_object_or_404(Plate,id=plate_id)
    exp = p.experiment
    src_wells_with_compounds_and_no_soaks = exp.srcWells.exclude(compounds__isnull=True
        ).exclude(soak__isnull=False
        ).select_related('plate'
        ).order_by('plate__plateIdxExp', 'name')
    src_qs = src_wells_with_compounds_and_no_soaks
    p_drop_images= p.drop_images.all()

    well_qs = p.wells.all().prefetch_related('subwells','subwells__parentWell', 'subwells__soak').order_by('name')
    numWells = well_qs.count()
    wells_ = [w for w in well_qs]
    wells = [None] * len(wells_)
    soakDict = {}
    soakSaves = []
    for k in range(numWells):
        w = wells_[k]
        wells[k] = {'name': w.name}
        subwells = []
        for s_w in w.subwells.all():
            file_name_ = w.name+'_'+str(s_w.idx)
            s_w_dict = {'id': s_w.id, 'name':s_w.name, 'idx':s_w.idx, 'saveCount': None, 'guiURL':'', 'file_name': file_name_}
            
            try:
                if s_w.soak:
                    guiURL = reverse_lazy('imageGUI', kwargs={'plate_id':p.pk, 
                                'user_id':request.user.pk, 
                                'file_name': file_name_})
                    soakSaves.append(s_w.soak.saveCount)
                    soakDict[s_w.id] = {
                        'saveCount':s_w.soak.saveCount,
                        'guiURL': guiURL, 
                        'file_name': file_name_
                    }
                    s_w_dict.update(
                        {'saveCount': s_w.soak.saveCount, 
                        'guiURL': guiURL,
                        })
            except Soak.DoesNotExist as e:
                pass

            subwells.append(s_w_dict)
            subwells.sort(key=lambda s_w: s_w['name'])
        wells[k]['subwells'] = subwells

    wells_reshaped = reshape(wells, (p.numRows, p.numCols))

    perc_complete = len(list(filter(lambda x: bool(x), soakSaves))) / len(soakSaves)
    
    useS3 = p_drop_images.first().useS3
    target_well = well_qs.get(name=well_name)
    s_w = target_well.subwells.get(idx=subwell_idx)
    soak = s_w.soak
    well_XYR_um = soak.well_XYR_um
    drop_XYR_um = soak.drop_XYR_um
    form = SoakGUIForm(initial={
        'soakVolume':soak.soakVolume, 
        'soakOffsetX':soak.soakOffsetX, 
        'soakOffsetY':soak.soakOffsetY,
        'well_x':well_XYR_um[0],
        'well_y':well_XYR_um[1],
        'well_radius':well_XYR_um[2],
        'useSoak':soak.useSoak,}, 
        src_qs=src_qs)
    
    obj_keys = [w.key for w in p_drop_images]
    file_names = [w.file_name for w in p_drop_images]
    prefix_s3 = 'media/private/' + str(user_id) + '/' + str(plate_id) + '/'
    prefix_local = '/media/local/user_folder/' + str(user_id) + '/dropimages/' + str(plate_id) + '/'
    prefix = prefix_s3 if useS3 else prefix_local

    def get_prev_next_well(arr, f_n):
        i = arr.index(f_n)
        prv = arr[i-1]
        nxt = arr[(i+1)%len(arr)]
        return (prv, nxt)

    def render_view(user_id, plate_id, file_name, soak, subwell, form):

        if request.user.id == int(user_id): #users can only see their own images
            soakOffset_xyr = soak.soak_XYR_um
            targetWell_xyr = well_XYR_um
            context = {
                "prev_well":prev_well,
                "image_url":image_url,
                "next_well":next_well,
                "keys": obj_keys,
                "file_name":file_name,
                "user_id":user_id,
                "plate_id":plate_id,
                "file_names":file_names,
                "dont_show_path": True,
                "back_to_exp_url": reverse_lazy('exp', kwargs={'pk_exp':exp.id, 'pk_proj':exp.project.id,}),
                "perc_complete": (perc_complete*100//1), 

                'wellMatrix' : wells_reshaped,
                'soakDict': soakDict,

                "soakCircleColor": '#ffc107',
                "wellCircleColor": '#28a745',
                "soakOffsetX" : soakOffset_xyr[0],
                "soakOffsetY" : soakOffset_xyr[1],
                "soakVolume": soak.soakVolume,
                "topSoakCircle": soakOffset_xyr[1]-soakOffset_xyr[2],
                "leftSoakCircle":soakOffset_xyr[0]-soakOffset_xyr[2],
                "sideSoakCircle": 2*soakOffset_xyr[2],                
                "radSoakCircle_": soakOffset_xyr[2],

                "targetWellX" : targetWell_xyr[0],
                "targetWellY" : targetWell_xyr[1],
                "targetWellRadius": targetWell_xyr[2],
                "topWellCircle": targetWell_xyr[1] - targetWell_xyr[2],
                "leftWellCircle": targetWell_xyr[0] - targetWell_xyr[2],
                "sideWellCircle":2*targetWell_xyr[2],
                "radWellCircle_": targetWell_xyr[2],

                'SoakGUIForm':form,
                "saveCount": soak.saveCount,
                "use_soak" : soak.useSoak, 
            }
            guiData = copy.deepcopy(context)
            guiData.pop('SoakGUIForm')
            context["guiData"] = json.dumps(guiData, cls=DjangoJSONEncoder)
            return render(request, "xtal_img/imageGUI.html", context)
        else:
            return HttpResponse("bad request")

    if obj_keys:
        curr_image_key = str(p_drop_images.filter(file_name=file_name)[0].key)
        image_url_s3 = create_presigned_url(settings.AWS_STORAGE_BUCKET_NAME, prefix +  curr_image_key, 4000)
        image_url_local = prefix + curr_image_key 
        image_url = image_url_s3 if useS3 else image_url_local
        (prev_well, next_well) = get_prev_next_well(file_names, file_name)
    if request.method == 'POST':
        form = SoakGUIForm(data=request.POST, src_qs=src_qs)
        if (form.is_valid()):
            #process valid form 
            cleaned_data = form.cleaned_data
            for k, v in cleaned_data.items():
                setattr(soak, k, v)
            soak.save()

            # go to next well ion successful form submit
            arr_url = request.get_full_path().split('/')
            arr_url[len(arr_url) - 2] = next_well
            new_url = '/'.join(arr_url)
            if (request.POST.get('nextWellOnSave')):
                return redirect(new_url)
            else:
                return render_view(user_id,plate_id,file_name, soak, s_w, form)

        return render_view(user_id,plate_id,file_name, soak, s_w, form)
    else: #request.method == 'GET'
        return render_view(user_id,plate_id,file_name, soak, s_w, form)

