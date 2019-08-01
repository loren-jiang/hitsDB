# s3/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    re_path(r'^private_files_upload/$', login_required(views.FileFieldView.as_view()), name='private_files_upload'),
    re_path(r'^private_file_upload/$', login_required(views.upload_private_file), name='private_file_upload'),
    # re_path(r'^(?P<pk>[\d]+)/secretfile/$', login_required(views.SecretFileView.as_view()), name='secret_file'),
]