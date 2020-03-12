# common querysets that views will need

from django.apps import apps 
Soak = apps.get_model('experiment', 'Soak')
Library = apps.get_model('lib', 'Library')
Compound = apps.get_model('lib', 'Compound')
Plate = apps.get_model('experiment', 'Plate')
Well = apps.get_model('experiment', 'Well')
SubWell = apps.get_model('experiment', 'SubWell')
Experiment = apps.get_model('experiment', 'Experiment')
Project = apps.get_model('experiment', 'Project')
XtalContainer = apps.get_model('experiment', 'XtalContainer')
# from .models import Project, Experiment,Plate, Soak
from lib.models import Library, Compound
from django.contrib.auth.models import User, Group

#-------------------------------------------------Library querysets --------------------------------------------------------------
def project_libraries(proj):
    libs_qs = Library.objects.filter(experiments__in=proj.experiments.all())
    return libs_qs

def user_accessible_libs(user):
    """
    Returns queryset of libraries that are accessible (ie owned by user or in collaboration with)
    """
    collab_libs = Library.objects.filter(experiments__in=user_accessible_experiments(user))
    user_libs = user.libraries
    libs = Library.objects.filter(id__in=[lib.id for lib in user_libs.union(collab_libs)])
    return libs

def user_editable_libs(user):
    """
    Returns queryset of libraries that are editable (ie owned by user or in collaboration with)
    """
    collab_libs = Library.objects.filter(experiments__in=user_editable_experiments(user))
    user_libs = user.libraries
    libs = Library.objects.filter(id__in=[lib.id for lib in user_libs.union(collab_libs)])
    return libs

#-------------------------------------------------Experiment querysets -----------------------------------------------------------
def user_accessible_experiments(user):
    """
    Returns queryset of exeriments that are accesible (ie owned by user or in collaboration with)
    """
    accesible_exps = Experiment.objects.filter(project__in=user_accessible_projects(user))
    return Experiment.objects.filter(id__in=accesible_exps)

def user_editable_experiments(user):
    """
    Returns queryset of projects that are editable (ie owned by user or an editor)
    """
    editable_exps = Experiment.objects.filter(project__in=user_editable_projects(user))
    # user_exps = user.experiments.all()
    # lst = [e.id for e in editable_exps] + [e.id for e in user_exps]
    # return Experiment.objects.filter(id__in=lst)
    return Experiment.objects.filter(id__in=editable_exps)

#-------------------------------------------------Project querysets --------------------------------------------------------------
def user_projects_with_exps(user):
    """
    Returns queryset of projects explicitly owned by user with experiments
    """
    return user.projects.exclude(experiments__isnull=True)

def user_accessible_projects(user):
    """
    Returns queryset of projects that are accesible (ie owned by user or in collaboration with)
    """
    return Project.objects.filter(id__in=[p.id for p in user.projects.all().union(user.collab_projects.all())])

def user_editable_projects(user):
    """
    Returns queryset of projects that are editable (ie owned by user or an editor)
    """
    return Project.objects.filter(id__in=[p.id for p in user.projects.all().union(user.editor_projects.all())])
    
#-------------------------------------------------User queryset ------------------------------------------------------------------
def user_collaborators(user):
    """
    Returns queryset of users that are collaborators in user's projects
    """
    return User.objects.filter(collab_projects__in=user.projects.all())

def user_editors(user):
    """
    Returns queryset of users that are editors in user's projects
    """
    return User.objects.filter(editor_projects__in=user.projects.all())

#-------------------------------------------------Plate queryset ------------------------------------------------------------------
def user_editable_plates(user):
    """
    Returns queryset of plates that are editable to user
    """
    user_plates = user.plates.all()
    user_editable = Plate.objects.filter(experiment__in=user_editable_experiments(user))
    ids = [p.id for p in user_plates.union(user_editable)]
    return Plate.objects.filter(id__in=ids)

def user_accessible_plates(user):
    """
    Returns queryset of plates that are accesible to user
    """
    return Plate.objects.filter(experiment__in=user_accessible_experiments(user))

#-------------------------------------------------Soak queryset ------------------------------------------------------------------
def plate_soaks(plate):
    if type(plate) == Plate:
        if not(plate.isSource):
            return Soak.objects.filter(dest__parentWell__plate=plate)
        else:
            return Soak.objects.filter(src__plate=plate)
    return Soak.objects.none()

def soaks_contained(exp):
    """
    Returns queryset of experiment soaks that have storage and storage_position
    """
    return exp.soaks.filter(storage__isnull=False, storage_position__isnull=False)