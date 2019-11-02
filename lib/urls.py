#experiment/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views
from django.contrib.auth.models import User

urlpatterns = [
    re_path(r'^home/libs/upload_file/(?P<form_class>\w+)/$', views.new_lib_from_file,
        name='new_lib_from_file'),
    # re_path(r'^home/libs/new_lib/(?P<form_class>\w+)/$', views.new_lib,
    #     name='new_lib'),
]   
   	