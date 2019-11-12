from .models import Library
from functools import wraps, partial
from django.core.exceptions import PermissionDenied

def is_users_library(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        lib = Library.objects.get(pk=kwargs['pk_lib'])
        if lib.owner.pk == request.user.pk:
            return func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrapped