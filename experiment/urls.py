#experiment/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views
from django.contrib.auth.models import User

urlpatterns = [
    re_path(r'^libraries/$', views.libraries, name='libs'),
    re_path(r'^proj_libraries/(?P<pk_proj>\d+)$', views.proj_libraries, name='proj_libs'),
    re_path(r'^projects/$', views.projects, name='projects'),
    re_path(r'^projects/delete_projs/(?P<pks>(?:\d+/)+)$', views.delete_projects,
        name='delete_projs'),
    re_path(r'^proj/(?P<pk>\d+)$', views.project, name='proj'),
    re_path(r'^exp/(?P<pk>\d+)/$', views.experiment, name='exp'),
	# re_path(r'^experiments/exp/(?P<pk>\d+)/$', views.experiment, name='exp'),
	re_path(r'^experiments/soaks_csv_view/(?P<pk>\d+)/$', views.soaks_csv_view, name='soaks_csv_view'),
    re_path(r'^experiments/$', views.experiments, name='experiments'),
    re_path(r'^proj/(?P<pk_proj>\d+)/experiments/new/$', views.NewExp.as_view(), name='new_proj_experiment'),
    re_path(r'^experiments/new/$', views.MyView.as_view(), name='new_experiment'),
    re_path(r'^experiments/delete_exp/(?P<pk>\d+)/$', views.delete_experiment,
    	name='delete_exp'),
    re_path(r'^experiments/delete_exps/(?P<pks>(?:\d+/)+)$', views.delete_experiments,
        name='delete_exps'),
    re_path(r'^experiments/delete_exp_plates/(?P<pk>\d+)/$', views.delete_exp_plates,
    	name='delete_exp_plates'),
]   
   	