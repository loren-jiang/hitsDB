# Python file for common imports shared among model classes
from django.db import models
from datetime import date
from django.contrib.auth.models import User, Group
from django.utils import timezone
from import_ZINC.models import Library, Compound
from experiment.exp_view_process import formatSoaks, ceiling_div, chunk_list, split_list, getWellIdx, getSubwellIdx
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.functional import cached_property 
from orm_custom.custom_functions import bulk_add, bulk_one_to_one_add