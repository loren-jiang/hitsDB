#experiment/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views, library_views, project_views, experiment_views, soak_views
from django.contrib.auth.models import User

urlpatterns = [
    # --------------- urls to Main app views ------------------------------
    re_path(r'^$', views.home, name='home'),
    re_path(r'^home/$', views.home, name='home'),

    # --------------- urls to Library views ------------------------------
    # re_path(r'^home/lib_compounds/(?P<pk_lib>\d+)/$', library_views.lib, name='lib_compounds'),
    re_path(r'^home/libs/(?P<pk_lib>\d+)/$', library_views.lib_compounds, name='lib'),
    re_path(r'^home/libs/(?P<pk_lib>\d+)/edit/$', library_views.lib_edit, name='lib_edit'),
    re_path(r'^home/libs/(?P<pk_lib>\d+)/modify_lib_compounds/$', 
        library_views.modify_lib_compounds, name='modify_lib_compounds'),
    re_path(r'^home/libs/$', library_views.libs, name='libs'),
    re_path(r'^home/libs/delete/$', library_views.modify_libraries, name='modify_libs'),
    # re_path(r'^home/compounds_search/$', library_views.UserCompoundsFilterView.as_view(), name='user_compounds'),
    re_path(r'^home/compounds_search/$', library_views.user_compounds, name='user_compounds'),
    

    # --------------- urls to Project views ------------------------------
    re_path(r'^home/soaks/(?P<pk_soak>\d+)/edit/$', soak_views.SoakEdit.as_view(), name='soak_edit'),
    re_path(r'^home/soak/(?P<pk_soak>\d+)/edit/$', soak_views.soak_edit, name='soak__edit'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/soaks/$', soak_views.soaks, name='exp_soaks_'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/libs/(?P<pk_lib>\d+)/$', project_views.proj_lib, name='proj_lib'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/libs/$', project_views.proj_libs, name='proj_libs'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/edit/$', project_views.project_edit, name='proj_edit'),
    re_path(r'^home/projs/simple_edit/(?P<pk_proj>\d+)/$', project_views.project_edit_simple, name='proj_edit_simple'),
    # re_path(r'^home/proj_libraries/(?P<pk_proj>\d+)/$', project_views.proj_libraries, name='proj_libs'),
    re_path(r'^home/projs/$', project_views.projects, name='projects'),
    re_path(r'^home/projs/delete_projs/(?P<pks>\d*(?:_\d+)*)$', project_views.delete_projects, name='delete_projs'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/$', project_views.project, name='proj'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/exps/$', project_views.proj_exps, name='proj_exps'),
    # re_path(r'^home/projs/(?P<pk_proj>\d+)/exp/new/$', project_views.NewExp.as_view(), name='new_proj_experiment'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/delete_exps/(?P<pks>\d*(?:_\d+)*)$', project_views.delete_experiments, name='delete_proj_exps'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/delete_exps/(?P<pks_exp>\d*(?:_\d+)*)$', project_views.del_proj_exps, name='del_proj_exps'),

    # --------------- urls to Experiment views ------------------------------
    # re_path(r'^home/multiform/$', experiment_views.MultipleFormsDemoView.as_view(), name='multiform'),
    # re_path(r'^home/exps/(?P<pk>\d+)/$', experiment_views.experiment, name='exp'),
    re_path(r'^home/exps/(?P<pk_exp>\d+)/$', experiment_views.MultipleFormsDemoView.as_view(), name='exp'),
    re_path(r'^home/exps/(?P<pk_exp>\d+)/setup/$', experiment_views.MultipleFormsDemoView.as_view(), name='exp_setup'),
	# re_path(r'^home/experiments/exp/(?P<pk>\d+)/$', experiment_views.experiment, name='exp'),
    # re_path(r'^home/exps/(?P<pk>\d+)/soaks_csv_view/$', experiment_views.soaks_csv_view, name='soaks_csv_view'),
    re_path(r'^home/exps/(?P<pk_exp>\d+)/soaks_csv_view/all$', experiment_views.soaks_csv_view, name='soaks_csv_view'),
	re_path(r'^home/exps/(?P<pk_exp>\d+)/soaks_csv_view/(?P<pk_src_plate>\d+)/(?P<pk_dest_plate>\d+)/$', experiment_views.soaks_csv_view, name='soaks_csv_view'),
    re_path(r'^home/exps/(?P<pk_exp>\d+)/soaks/$', experiment_views.soaks, name='exp_soaks'),
    re_path(r'^home/exps/(?P<pk_exp>\d+)/grouped_soaks/$', experiment_views.soaks, name='exp_grouped_soaks'),
    re_path(r'^home/exps/(?P<pk_exp>\d+)/plates/$', experiment_views.plates, name='exp_plates'),
    re_path(r'^home/exps/$', experiment_views.experiments, name='experiments'),
    # re_path(r'^home/exps/new/$', experiment_views.NewExp.as_view(), name='new_experiment'),
    re_path(r'^home/exps/delete_exp/(?P<pk_exp>\d+)/$', experiment_views.delete_experiment, name='delete_exp'),
    re_path(r'^home/exps/delete_exps/(?P<pk_exp>(?:\d+/)+)/$', experiment_views.delete_experiments, name='delete_exps'),
    re_path(r'^home/exps/(?P<pk_exp>\d+)/delete_exp_plates/$', experiment_views.delete_exp_plates, name='delete_exp_plates'),

    re_path(r'^home/projs/(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/$', experiment_views.MultipleFormsDemoView.as_view(), name='exp'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/setup/$', experiment_views.MultipleFormsDemoView.as_view(), name='exp_setup'),
	# re_path(r'^home/experiments/exp/(?P<pk>\d+)/$', experiment_views.experiment, name='exp'),
    # re_path(r'^home/exps/(?P<pk>\d+)/soaks_csv_view/$', experiment_views.soaks_csv_view, name='soaks_csv_view'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/soaks_csv_view/all$', experiment_views.soaks_csv_view, name='soaks_csv_view'),
	re_path(r'^home/projs/(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/soaks_csv_view/(?P<pk_src_plate>\d+)/(?P<pk_dest_plate>\d+)/$', experiment_views.soaks_csv_view, name='soaks_csv_view'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/soaks/$', experiment_views.soaks, name='exp_soaks'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/grouped_soaks/$', experiment_views.soaks, name='exp_grouped_soaks'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/plates/$', experiment_views.plates, name='exp_plates'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/exps/$', experiment_views.experiments, name='experiments'),
    # re_path(r'^home/projs/(?P<pk_proj>\d+)/exps/new/$', experiment_views.NewExp.as_view(), name='new_experiment'),
    # re_path(r'^home/projs/(?P<pk_proj>\d+)/exps/delete_exp/(?P<pk_exp>\d+)/$', experiment_views.delete_experiment, name='delete_exp'),
    # re_path(r'^home/projs/(?P<pk_proj>\d+)/exps/delete_exps/(?P<pks_exp>(?:\d+/)+)/$', experiment_views.delete_experiments, name='delete_exps'),
    re_path(r'^home/projs/(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/delete_exp_plates/$', experiment_views.delete_exp_plates, name='delete_exp_plates'),
    
]       
   	