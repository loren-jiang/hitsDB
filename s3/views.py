from django.shortcuts import render
import logging
# Create your views here.
from django import http
from django.shortcuts import get_object_or_404
from django.views.generic import RedirectView
# from boto.s3.connection import S3Connection
from .models import PublicFile, PrivateFile
from .forms import PrivateFileUploadForm
import boto3
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy

# from .models import Document

def upload_private_file(request):
    if request.method == 'POST':
        form = PrivateFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['upload'] #assumes lib_name is unique
            new_file = PrivateFile(upload=file, owner=request.user)
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

logger = logging.getLogger('django.request')

class SecretFileView(RedirectView):
    permanent = False
    s3Client = boto3.client('s3')

    def get_redirect_url(self, **kwargs):
        # s3 = S3Connection(settings.AWS_ACCESS_KEY_ID,
        #                     settings.AWS_SECRET_ACCESS_KEY,
        #                     is_secure=True)
        # Create a URL valid for 60 seconds.
        return s3Client.generate_presigned_url('get_object', 
            Params = {'Bucket': 'settings.AWS_STORAGE_BUCKET_NAME', 'Key': kwargs['filepath']}, ExpiresIn = 60)
        # return s3.generate_url(60, 'GET',
        #                     bucket=settings.AWS_STORAGE_BUCKET_NAME,
        #                     key=kwargs['filepath'],
        #                     force_http=True)

    def get(self, request, *args, **kwargs):
        m = get_object_or_404(MyModel, pk=kwargs['pk'])
        u = request.user

        if u.is_authenticated() and (u.get_profile().is_very_special() or u.is_staff):
            if m.private_file:
                filepath = settings.MEDIA_DIRECTORY + m.private_file
                url = self.get_redirect_url(filepath=filepath)
                # The below is taken straight from RedirectView.
                if url:
                    if self.permanent:
                        return http.HttpResponsePermanentRedirect(url)
                    else:
                        return http.HttpResponseRedirect(url)
                else:
                    logger.warning('Gone: %s', self.request.path,
                                extra={
                                    'status_code': 410,
                                    'request': self.request
                                })
                    return http.HttpResponseGone()
            else:
                raise http.Http404
        else:
            raise http.Http404