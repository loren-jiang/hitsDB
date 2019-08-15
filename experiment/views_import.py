# common imports for views
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers import serialize
from django.views.generic.base import TemplateView
from django.db import transaction
from django.forms.models import model_to_dict
from django.contrib.auth.decorators import user_passes_test