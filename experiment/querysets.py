# common querysets that views will need 

from .models import Project, Experiment, Soak
from lib.models import Library, Compound
from django.contrib.auth.models import User, Group

#-------------------------------------------------Library querysets --------------------------------------------------------------

# libraries accessible to users; 
def user_accessible_libs(user):
    user_collab_projects = user.collab_projects.filter()
    collab_exps = Experiment.objects.filter(project_id__in=[p.id for p in user_collab_projects])
    collab_libs = Library.objects.filter(experiments__in=collab_exps)
    user_libs = user.libraries
    libs = Library.objects.filter(id__in=[lib.id for lib in user_libs.union(collab_libs)])
    return libs

#-------------------------------------------------Experiment querysets -----------------------------------------------------------

#-------------------------------------------------Project querysets --------------------------------------------------------------
# returns queryset of projects explicitly owned by user with experiments
def user_projects_with_exps(user):
    return user.projects.exclude(experiments__isnull=True)

#returns queryset of projects that are accesible (ie owned by user or in collaboration with)
def user_accessible_projects(user):
    return Project.objects.filter(id__in=[p.id for p in user.projects.all().union(user.collab_projects.all())])

def user_editable_projects(user):
    return Project.objects.filter(id__in=[p.id for p in user.projects.all().union(user.editor_projects.all())])
    
#-------------------------------------------------User queryset ------------------------------------------------------------------
def user_collaborators(user):
    return User.objects.filter(collab_projects__in=user.projects.all())
