# xtal_img/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views

urlpatterns = [
    re_path(r'^image-gui/(?P<user_id>\d+)/(?P<plate_id>\d+)/(?P<file_name>.*)/$',views.imageGUIView, name='imageGUI'),
]