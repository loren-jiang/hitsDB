# xtal_img/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    re_path(r'^image-gui/(?P<user_id>\d+)/(?P<plate_id>\d+)/(?P<file_name>.*)/$', login_required(views.imageGUIView), name='imageGUI'),
]