from functools import wraps, partial
from django.core.exceptions import PermissionDenied
from .models import Project, Experiment, Plate
from import_ZINC.models import Library

def is_users_project(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        proj = Project.objects.get(pk=kwargs['pk_proj'])
        if proj.owner.pk == request.user.pk:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    # wrap.__doc__ = func.__doc__
    # wrap.__name__ = func.__name__
    return wrapped

def is_users_library(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        lib = Library.objects.get(pk=kwargs['pk_lib'])
        if lib.owner.pk == request.user.pk:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    # wrap.__doc__ = func.__doc__
    # wrap.__name__ = func.__name__
    return wrapped

def is_users_experiment(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        exp = Experiment.objects.get(pk=kwargs['pk_exp'])
        if exp.owner.pk == request.user.pk:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    # wrap.__doc__ = func.__doc__
    # wrap.__name__ = func.__name__
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