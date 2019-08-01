# xtal_img/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    re_path(r'^image-gui/(?P<curr_image_key>.*)/$', login_required(views.imageGUIView), name='imageGUI'),
]