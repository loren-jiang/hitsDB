#experiment/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views
from django.contrib.auth.models import User
from .forms import LibraryForm, UploadCompoundsNewLib
from .views import SecureLibraryModalEdit, SecureLibraryModifyFromTable

urlpatterns = [
    re_path(r'^home/libs/(?P<pk_lib>\d+)/$', views.lib_compounds, name='lib'),
    re_path(r'^home/libs/(?P<pk_lib>\d+)/edit/$', SecureLibraryModalEdit.as_view(
        model=LibraryForm.Meta.model, form_class=LibraryForm,pk_url_kwarg='pk_lib'), name='lib_edit'),
    re_path(r'^home/libs/(?P<pk_lib>\d+)/modify_lib_compounds/$', 
        views.modify_lib_compounds, name='modify_lib_compounds'),
    re_path(r'^home/libs/$', views.libs, name='libs'),
    re_path(r'^home/libs/modify_libs/$',SecureLibraryModifyFromTable.as_view(model_class=LibraryForm.Meta.model) , name='modify_libs'),
    re_path(r'^home/compounds_search/$', views.user_compounds, name='user_compounds'),
    re_path(r'^home/libs/upload_file/(?P<form_class>\w+)/$', views.new_lib_from_file,
        name='lib_new'),

    
]   
   	