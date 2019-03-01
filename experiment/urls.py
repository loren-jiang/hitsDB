#experiment/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views
from django.contrib.auth.models import User

urlpatterns = [
	re_path(r'^experiments/exp/(?P<pk>\d+)/$', views.experiment, name='exp'),
    re_path(r'^experiments/$', views.experiments, name='experiments'),
    re_path(r'^experiments/new/$', views.new_experiment, name='new_experiment'),
]   
   