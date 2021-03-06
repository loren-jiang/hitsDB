from functools import wraps, partial
from django.core.exceptions import PermissionDenied
from .models import Project, Experiment, Plate
from lib.models import Library
from .querysets import user_accessible_experiments, user_editable_experiments, user_accessible_projects, user_editable_projects

def is_user_accessible_project(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        proj = Project.objects.get(pk=kwargs['pk_proj'])
        qs = user_accessible_projects(request.user)
        if qs.filter(pk=proj.pk).exists():
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrapped

def is_user_editable_project(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        proj = Project.objects.get(pk=kwargs['pk_proj'])
        qs = user_editable_projects(request.user)
        if qs.filter(pk=proj.pk).exists():
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrapped

def is_users_project(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        proj = Project.objects.get(pk=kwargs['pk_proj'])
        if proj.owner.pk == request.user.pk:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrapped

def is_users_library(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        lib = Library.objects.get(pk=kwargs['pk_lib'])
        if lib.owner.pk == request.user.pk:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrapped

def is_users_experiment(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        exp = Experiment.objects.get(pk=kwargs['pk_exp'])
        if exp.owner.pk == request.user.pk:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrapped

def is_user_editable_experiment(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        pk_exp = kwargs.get('pk_exp')
        if pk_exp:
            exp = Experiment.objects.get(pk=pk_exp)
            if user_editable_experiments(request.user).filter(id=exp.id).exists():
                return func(request, *args, **kwargs)
            else:
                raise PermissionDenied
    return wrapped

def is_user_accessible_experiment(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        pk_exp = kwargs.get('pk_exp')
        if pk_exp:
            exp = Experiment.objects.get(pk=pk_exp)
            if user_accessible_experiments(request.user).filter(id=exp.id).exists():
                return func(request, *args, **kwargs)
            else:
                raise PermissionDenied
    return wrapped

def is_source_plate(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        p = Plate.objects.get(pk=kwargs['pk_plate'])
        if p.isSource:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    # wrap.__doc__ = func.__doc__
    # wrap.__name__ = func.__name__
    return wrapped

def is_dest_plate(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        p = Plate.objects.get(pk=kwargs['pk_plate'])
        if not(p.isSource):
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    # wrap.__doc__ = func.__doc__
    # wrap.__name__ = func.__name__
    return wrapped