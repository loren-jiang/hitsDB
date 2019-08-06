#experiment/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views, library_views, project_views, experiment_views
from django.contrib.auth.models import User

urlpatterns = [
    # --------------- urls to Main app views ------------------------------
    re_path(r'^$', views.home, name='home'),
    re_path(r'^home/$', views.home, name='home'),

    # --------------- urls to Library views ------------------------------
    re_path(r'^lib_compounds/(?P<pk_lib>\d+)$', library_views.lib_compounds, name='lib_compounds'),
    re_path(r'^libraries/$', library_views.libraries, name='libs'),

    # --------------- urls to Project views ------------------------------
    re_path(r'^proj/edit/(?P<pk>\d+)$', project_views.project_edit, name='proj_edit'),
    re_path(r'^proj/simple_edit/(?P<pk>\d+)$', project_views.project_edit_simple, name='proj_edit_simple'),
    re_path(r'^proj_libraries/(?P<pk_proj>\d+)$', project_views.proj_libraries, name='proj_libs'),
    re_path(r'^projects/$', project_views.projects, name='projects'),
    re_path(r'^projects/delete_projs/(?P<pks>(?:\d+/)+)$', project_views.delete_projects, name='delete_projs'),
    # re_path(r'^proj/(?P<pk>\d+)$', project_views.project, name='proj'),
    re_path(r'^proj/(?P<pk>\d+)$', project_views.ProjectView.as_view(), name='proj'),
    re_path(r'^proj/(?P<pk_proj>\d+)/exp/new/$', project_views.NewExp.as_view(), name='new_proj_experiment'),
    re_path(r'^proj/(?P<pk_proj>\d+)/delete_exps/(?P<pks>(?:\d+/)+)$', project_views.delete_experiments, name='delete_proj_exps'),
    
    # --------------- urls to Experiment views ------------------------------
    re_path(r'^exp/(?P<pk>\d+)/$', experiment_views.experiment, name='exp'),
	# re_path(r'^experiments/exp/(?P<pk>\d+)/$', experiment_views.experiment, name='exp'),
	re_path(r'^exp/(?P<pk>\d+)/soaks_csv_view/$', experiment_views.soaks_csv_view, name='soaks_csv_view'),
    re_path(r'^exp/(?P<pk>\d+)/soaks/$', experiment_views.soaks, name='exp_soaks'),
    re_path(r'^exp/(?P<pk>\d+)/plates/$', experiment_views.plates, name='exp_plates'),
    re_path(r'^exps/$', experiment_views.experiments, name='experiments'),
    re_path(r'^exps/new/$', experiment_views.NewExp.as_view(), name='new_experiment'),
    re_path(r'^exps/delete_exp/(?P<pk>\d+)/$', experiment_views.delete_experiment, name='delete_exp'),
    re_path(r'^exps/delete_exps/(?P<pks>(?:\d+/)+)$', experiment_views.delete_experiments, name='delete_exps'),
    re_path(r'^exp/(?P<pk>\d+)/delete_exp_plates/$', experiment_views.delete_exp_plates, name='delete_exp_plates'),
]   
   	