from django.shortcuts import render
import logging
# Create your views here.
from django import http
from django.shortcuts import get_object_or_404
from django.views.generic import RedirectView
# from boto.s3.connection import S3Connection
from .models import PublicFile, PrivateFile
from django.views.generic.edit import FormView
from .forms import ImagesFieldForm, FilesFieldForm, PrivateFileUploadForm
import boto3
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.conf import settings 
import os
from experiment.models import Plate
from experiment.decorators import is_dest_plate
from hitsDB.views_import import *

#loads well images with corresponding model instance and associated plate id and user id 
class WellImagesUploadView(FormView):
    form_class = ImagesFieldForm
    template_name = './s3/private_images_upload.html'  # Replace with your template.
    
    def get_success_url(self):
        return '/'

    @method_decorator(is_dest_plate)
    def dispatch(self, *args, **kwargs):
        return super(WellImagesUploadView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        p = get_object_or_404(Plate, id=kwargs['pk_plate'])
        well_images = p.well_images.filter()
        form = self.get_form(self.get_form_class())
        context = {
            'form': form,
            'well_images': well_images,
            'dont_show_path': True,
        }
        return render(request, './s3/private_images_upload.html', context)

    def post(self, request, *args, **kwargs):
        p = get_object_or_404(Plate, id=kwargs['pk_plate'])
        if p.experiment.owner == request.user: #only the appropriate user can upload images 
            p.well_images.filter().delete() #delete well images associated with plate before uploading new ones
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            files = request.FILES.getlist('image_field')
            if form.is_valid():
                for f in files:
                    file_name = f.name.split('.')[0] #just get the file name, not the extension
                    if form.cleaned_data['use_local']:
                        new_file = WellImage(local_upload=f, owner=request.user, plate=p, file_name=file_name, useS3=False)
                    else:
                        new_file = WellImage(upload=f, owner=request.user, plate=p, file_name=file_name, useS3=True)
                    new_file.save()
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

class PrivateFilesUploadView(FormView):
    form_class = FilesFieldForm
    template_name = './s3/private_files_upload.html'  # Replace with your template.
    success_url = '/'  # Replace with your URL or reverse().

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file_field')
        if form.is_valid():
            for f in files:
                new_file = PrivateFile(upload=f, owner=request.user)
                new_file.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

def upload_private_file(request):
    if request.method == 'POST':
        form = PrivateFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            file = cd['upload']
            bucket_key = cd['bucket_key']
            new_file = PrivateFile(upload=file, bucket_key=bucket_key, owner=request.user)
            new_file.save()
            data = {
                "file": new_file,
            }
            return render(request, 's3/private_file_upload.html', data)
            # return HttpResponseRedirect('')
    else:
        form = PrivateFileUploadForm()
    return render(request, 's3/private_file_upload.html', {'form': form})

class CreatePrivateFileView(CreateView):
    model = PrivateFile
    fields = ['upload', ]
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documents = PrivateFile.objects.all()
        context['documents'] = documents
        return context