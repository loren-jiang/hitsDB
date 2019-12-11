#experiment/urls.py
from django.conf.urls import url, include
from django.urls import path, re_path
from . import views#, library_views, project_views, experiment_views, soak_views
from django.contrib.auth.models import User
from .forms import ProjectForm, PlateForm, ExperimentForm
from lib.forms import LibraryForm
from .views import SecureProjectModifyFromTable, SecurePlateModifyFromTable, SecureExperimentModifyFromTable
from my_utils.my_views import ModifyFromTableView
from django.contrib.auth.decorators import user_passes_test, login_required
from .decorators import *
from my_utils.my_views import ModalCreateView, ModalEditView

urlpatterns = [
    # --------------- urls to Main app views ------------------------------
    re_path(r'^$', views.home, name='home'),
    re_path(r'^home/$', views.home, name='home'),
    url(r'^home/', include([

        # --------------- urls to Project views ------------------------------
        url(r'^projs/', include([
            # re_path(r'^(?P<pk_proj>\d+)/$', views.project, name='proj'),
            re_path(r'^(?P<pk_proj>\d+)/$', views.MultiFormsProjView.as_view(), name='proj'),
            re_path(r'^(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/soaks/$', views.soaks, name='exp_soaks_'),
            re_path(r'^(?P<pk_proj>\d+)/libs/$', views.proj_libs, name='proj_libs'),
            re_path(r'^(?P<pk_proj>\d+)/edit/$', ModalEditView.as_view(
                model=ProjectForm.Meta.model, form_class=ProjectForm, pk_url_kwarg='pk_proj'),
                {'decorators': [login_required(login_url="/login"), is_users_project]},
                name='proj_edit'),
            re_path(r'^modify_projs/$', ModifyFromTableView.as_view(
                model_class=ProjectForm.Meta.model), 
                {'decorators' : [login_required(login_url="/login"), ]},
                name='modify_projs'),
            # re_path(r'^simple_edit/(?P<pk_proj>\d+)/$', views.project_edit_simple, name='proj_edit_simple'),
            re_path(r'^$', views.projects, name='projects'),
            re_path(r'^new$', ModalCreateView.as_view(
                form_class=ProjectForm, model=ProjectForm.Meta.model), 
                {'decorators' : [login_required(login_url="/login"), ]},
                name='proj_new'),
            re_path(r'^delete_projs/(?P<pks>\d*(?:_\d+)*)$', views.delete_projects, name='delete_projs'),
            re_path(r'^(?P<pk_proj>\d+)/exps/$', views.proj_exps, name='proj_exps'),
            re_path(r'^(?P<pk_proj>\d+)/delete_exps/(?P<pks>\d*(?:_\d+)*)$', views.delete_experiments, name='delete_proj_exps'),
            re_path(r'^(?P<pk_proj>\d+)/remove_exps/(?P<pks>\d*(?:_\d+)*)$', views.remove_exps_from_proj, name='remove_proj_exps'),
            re_path(r'^(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/$', views.MultiFormsExpView.as_view(), name='exp'),
            re_path(r'^(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/setup/$', views.MultiFormsExpView.as_view(), name='exp_setup'),
            re_path(r'^(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/soaks_csv_view/all$', views.soaks_csv_view, name='soaks_csv_view'),
            re_path(r'^(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/soaks_csv_view/(?P<pk_src_plate>\d+)/(?P<pk_dest_plate>\d+)/$', views.soaks_csv_view, name='soaks_csv_view'),
            re_path(r'^(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/soaks/$', views.soaks, name='exp_soaks'),
            re_path(r'^(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/soak_transfers/$', views.soak_transfers, name='soak_transfers'),
            re_path(r'^(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/grouped_soaks/$', views.soaks, name='exp_grouped_soaks'),
            re_path(r'^(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/plates/$', views.plates, name='exp_plates'),
            re_path(r'^(?P<pk_proj>\d+)/exps/$', views.experiments, name='experiments'),
            # re_path(r'^(?P<pk_proj>\d+)/exps/new$', ModalCreateView.as_view(
            #     form_class=ExperimentForm, model=ExperimentForm.Meta.model, pk_url_kwarg='pk_proj'), 
            #     {
            #         'decorators' : [login_required(login_url="/login"), ],
            #         'to_pass_to_context': ['pk_proj']
            #     },
            #     name='exp_new'),
            re_path(r'^(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/delete_exp_plates/$', views.delete_exp_plates, name='delete_exp_plates'),
            re_path(r'^(?P<pk_proj>\d+)/exps/(?P<pk_exp>\d+)/picklist_template/$', views.picklist_template_view, name='picklist_template'),
        ])),

        # --------------- urls to Experiment views ------------------------------
        url(r'^exps/', include([
            re_path(r'^$', views.experiments, name='experiments'),
            re_path(r'^delete_exp/(?P<pk_exp>\d+)/$', views.delete_experiment, name='delete_exp'),
            re_path(r'^delete_exps/(?P<pk_exp>(?:\d+/)+)/$', views.delete_experiments, name='delete_exps'),
            re_path(r'^(?P<pk_exp>\d+)/delete_exp_plates/$', views.delete_exp_plates, name='delete_exp_plates'),
            re_path(r'^(?P<pk_exp>\d+)/edit/$', ModalEditView.as_view(
                model=ExperimentForm.Meta.model, form_class=ExperimentForm, pk_url_kwarg='pk_exp'
                ), name='exp_edit'
                ),
            re_path(r'^new$', ModalCreateView.as_view(
                form_class=ExperimentForm, model=ExperimentForm.Meta.model), 
                {'decorators' : [login_required(login_url="/login"), ]},
                name='exp_new'),
            re_path(r'^modify_exps/$', SecureExperimentModifyFromTable.as_view(model_class=ExperimentForm.Meta.model), name='modify_exps'),
        ])),

        # --------------- urls to Plate views ------------------------------    
        url(r'^plates/', include([
            re_path(r'^(?P<pk_plate>\d+)/$', views.plate, name='plate'),
            re_path(r'^$', views.plates ,name='plates'),
            re_path(r'^(?P<pk_plate>\d+)/edit/$', ModalEditView.as_view(
                model=PlateForm.Meta.model, form_class=PlateForm, pk_url_kwarg='pk_plate'
                ), name='plate_edit'
                ),
            re_path(r'^modify_plates/$', SecurePlateModifyFromTable.as_view(model_class=PlateForm.Meta.model), name='modify_plates'),
        ])),
       
        # --------------- urls to Soak views ------------------------------  
        url(r'^soaks/', include([
            re_path(r'^(?P<pk_soak>\d+)/edit/$', views.soak_edit, name='soak__edit'),
        ])),  
        
        re_path(r'^well_edit/(?P<pk>\d+)/$', views.WellUpdateView.as_view(), name="well_edit")
    ]))
]