from functools import wraps, partial
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url

from .models import Project, Experiment, Plate
from import_ZINC.models import Library

def request_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Modified from https://docs.djangoproject.com/en/2.2/_modules/django/contrib/auth/decorators/#user_passes_test.
    Decorator for views that checks that the request passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the request object and returns True if the request passes.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request):
                return view_func(request)
            path = request.build_absolute_uri()
            resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)
            # If the login url is the same scheme and net location then just
            # use the path as the "next" url.
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if ((not login_scheme or login_scheme == current_scheme) and
                    (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(
                path, resolved_login_url, redirect_field_name)
        return _wrapped_view
    return decorator

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