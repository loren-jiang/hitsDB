#experiment/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views
from django.contrib.auth.models import User

urlpatterns = [
    re_path(r'^home/libs/upload_file/$', views.upload_file,
        name='upload_file'),
]   
   	