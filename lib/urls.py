#experiment/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views
from django.contrib.auth.models import User
from experiment.views import ModalCreateView
from .forms import LibraryForm, UploadCompoundsNewLib

urlpatterns = [
    # re_path(r'^home/libs/upload_file/(?P<form_class>\w+)/$', 
    #     ModalCreateView.as_view(model=LibraryForm.Meta.model, form_class=UploadCompoundsNewLib,),
    #     name='lib_new'),
    re_path(r'^home/libs/upload_file/(?P<form_class>\w+)/$', views.new_lib_from_file,
        name='lib_new'),
    # re_path(r'^home/libs/new_lib/(?P<form_class>\w+)/$', views.new_lib,
    #     name='lib_new'),
]   
   	