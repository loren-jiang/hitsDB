from django.shortcuts import render
import logging
# Create your views here.
from django import http
from django.shortcuts import get_object_or_404
from django.views.generic import RedirectView
# from boto.s3.connection import S3Connection
from .models import PublicFile, PrivateFile
from django.views.generic.edit import FormView
from .forms import FileFieldForm, PrivateFileUploadForm
import boto3
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.conf import settings 
import os

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
                new_file = PrivateFile(upload=f, bucket_key="test-gui-images/"+f.name, owner=request.user)
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