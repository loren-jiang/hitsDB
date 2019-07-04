from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import date

# Create your models here.
class Compound(models.Model): #doesnt need to be unique?
    # nameInternal = models.CharField(max_length=100, unique=True) 
    commonName = models.CharField(max_length=100, default='')
    chemFormula = models.CharField(max_length=100, default='')
    # manufacturer = models.CharField(max_length=100, default='')
    # library = models.ForeignKey(Library, related_name='compounds', on_delete=models.CASCADE, null=True, blank=True)
    #not all smiles have unique zincID, or perhaps vice versa
    zinc_id = models.CharField(max_length=30, null=True, blank=True, unique=True)
    smiles = models.CharField(max_length=200,null=True, blank=True)
    zincURL = models.URLField(null=True, blank=True)
    molWeight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    concentration = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # chemName = models.CharField(max_length=1000, default='')
    active = models.BooleanField(default=True)
    def __str__(self):
        return self.zinc_id


class Library(models.Model):
    name = models.CharField(max_length=30, unique=True)
    # name = models.CharField(max_length=30, )
    description = models.CharField(max_length=300, default='')
    isCommerical = models.BooleanField(default=False)
    sourceURL = models.URLField(null=True, blank=True)
    groups = models.ManyToManyField(Group, related_name='libraries', blank=True)
    owner = models.ForeignKey(User, related_name='library', on_delete=models.CASCADE,null=True, blank=True)
    isTemplate = models.BooleanField(default=False)
    supplier = models.CharField(max_length=100, default='')
    # library can have many compounds; compound can have many libraries
    compounds = models.ManyToManyField(Compound, related_name='libraries', blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

