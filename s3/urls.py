# s3/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    re_path(r'^plate/(?P<plate_pk>\d+)/well_images_upload/$', login_required(views.WellImagesUploadView.as_view()), name='well_images_upload'),
    re_path(r'^private_files_upload/$', login_required(views.PrivateFilesUploadView.as_view()), name='private_files_upload'),
    re_path(r'^private_file_upload/$', login_required(views.upload_private_file), name='private_file_upload'),
]