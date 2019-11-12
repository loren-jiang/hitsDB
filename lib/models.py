from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import date
import json
import csv
from django.urls import reverse, reverse_lazy
from itertools import compress
from my_utils.orm_functions import bulk_add
from itertools import compress
from my_utils.utility_functions import chunks
from .validators import validate_prefix
# from my_utils.views_helper import build_modal_form_context

# Create your models here.

class Compound(models.Model):
    chemicalName = models.CharField(max_length=300,null=True, blank=True)
    chemicalFormula = models.CharField(max_length=100, default='')
    zinc_id = models.CharField(max_length=30, unique=True, validators=[validate_prefix("ZINC"), validate_prefix("zinc")])
    smiles = models.CharField(max_length=300,null=True, blank=True)
    # zincURL = models.URLField(null=True, blank=True)
    molWeight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) #g/mol
    concentration = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True) #percent
    purity = models.PositiveSmallIntegerField(default=100, validators=[MaxValueValidator(100), MinValueValidator(0)])
    active = models.BooleanField(default=True)
    
    # def save(self, *args, **kwargs):
    #     if self.zinc_id:
    #         self.zincURL = self.get_absolute_url()
    #     super(Compound, self).save(*args, **kwargs)

    def __str__(self):
        return self.zinc_id

    def get_absolute_url(self):
        return 'https://zinc15.docking.org/substances/' + self.zinc_id + '/'
    
    @property
    def zincURL(self):
        return self.get_absolute_url()

class Library(models.Model):
    name = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=300, default='')
    isCommerical = models.BooleanField(default=False)
    sourceURL = models.URLField(null=True, blank=True)
    groups = models.ManyToManyField(Group, related_name='group_libraries', blank=True)
    owner = models.ForeignKey(User, related_name='libraries', on_delete=models.CASCADE,null=True, blank=True)
    isTemplate = models.BooleanField(default=False)
    supplier = models.CharField(max_length=100, null=True, blank=True)
    # library can have many compounds; compound can have many libraries
    compounds = models.ManyToManyField(Compound, related_name='libraries', blank=True)
    active = models.BooleanField(default=True)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    new_instance_viewname = 'lib_new'
    edit_instance_viewname = 'lib_edit'
    model_name = 'Library'

    def get_absolute_url(self):
        return "/libraries/%i/" % self.id

    def __str__(self):
        return self.name

    @classmethod
    def newInstanceUrl(cls):
        """
        Class method to return url to create new instance; compared to editInstanceUrl, this function should be a class method
        vs instance property because instance data (self.pk) is not needed
        """
        return reverse(cls.new_instance_viewname, kwargs={'form_class':"lib_new_form"})

    @property
    def editInstanceUrl(self):
        """
        Returns url to edit class instance; should be @property because instance data is needed
        """
        return reverse(self.edit_instance_viewname, kwargs={'pk_lib':self.pk})

    @classmethod
    def getModalFormData(cls):
        """
        Class method to return data needed for modal form to edit and make new instance of model
        """ 
        new_id = cls.new_instance_viewname
        edit_id = cls.edit_instance_viewname
        model_name = cls.model_name
    
        return {
            'new': {
                'url_class': '%s_url' % new_id,
                'modal_id': '%s_modal' % new_id,
                'form_class': '%s_form' % new_id,
                'button': {'id': new_id, 'text': 'New %s' % model_name,'class': 'btn-primary ' + '%s_url' % new_id, 
                    'href':reverse(new_id, kwargs={'form_class':"%s_form" % new_id})},
            },
            'edit': {
                'url_class': '%s_url' % edit_id,
                'modal_id': '%s_modal' % edit_id, 
                'form_class': '%s_form' % edit_id,
                # 'button': {'id': edit_id, 'text': 'Edit %s' % model_name,'class': 'btn-primary ' + '%s_url' % edit_id, 
                #     'href':reverse(edit_id, kwargs={'form_class':"%s_form" % edit_id})},
            }
            
        }

    @property
    def numCompounds(self):
        """
        Instance property that returns the number of compounds in library
        """
        return self.compounds.all().count()

    def insertCompoundsFromChunk(self, serialized_data):
        """
        Takes chunked data and add compounds to library

        Parameters:
        serialized_data (list): list of serialzied compounds to be added to library

        Returns (tuple) of compounds added to library (list of compounds created, list of compounds already existing)
        """
        from .serializers import NoSaveCompoundSerializer
        num = len(serialized_data)
        obj_lst = [None for k in range(num)]
    
        for i in range(num):
            data = serialized_data[i]
            fields = NoSaveCompoundSerializer.__dict__['_declared_fields']
            data = { k: data[k] for k in fields }
            serialize = NoSaveCompoundSerializer(data=data)
            if serialize.is_valid(raise_exception=True):
                obj_lst[i]=serialize.save()

        compounds_lst = [c for c in obj_lst if c is not None] #filter out None elems just in case

        # Greedy solution, but will not support updating compounds in the future
        # compounds_created = Compound.bulk_create(compounds_lst, ignore_conflicts=True)
        
        # check zinc_ids to see if they exist already in database
        # filter to find compounds not in db
        filt = [Compound.objects.filter(zinc_id=c.zinc_id).exists() for c in compounds_lst] 

        compounds_to_be_created = list(compress(compounds_lst, [not i for i in filt]))
        compounds_existing = list(compress(compounds_lst, filt))
        compounds_created = Compound.objects.bulk_create(compounds_to_be_created, ignore_conflicts=True)
        # optionally, we can bulk update here I think...
        return [c for c in compounds_created], [c for c in compounds_existing]

    # import file (.json or .csv) of compounds
    def newCompoundsFromFile(self, f, chunk_size=1000):
        """
        Takes file (.json or .csv) of compounds and adds them to library

        Parameters:
        f (uploaded file): file of compounds 
        chunk_size (int): number of rows to parse per chunk
        
        Returns (tuple) of (relations created, created compounds, exitsting compounds)
        """
        if self.compounds.all().exists():
            self.compounds.all().delete() #delete all library compounds to start from fresh
        file_name = f.name
        relations = []
        created = []
        existed = []
        rows = []
        is_csv = file_name.endswith(".csv")
        if is_csv:
            reader = csv.DictReader(f)
            rows = chunks(list(reader), chunk_size)
        else: # if file is .json
            rows = f.chunks(chunk_size)

        for chunk in rows:
            chunk_serialized = chunk if is_csv else json.loads(chunk) 
            compounds_to_create, compounds_existing = self.insertCompoundsFromChunk(chunk_serialized)
            lib = self
            LibCompoundRelation = Library.compounds.through
            # list of zinc codes for all compounds created and existing
            ZINC_lst = [c.zinc_id for c in compounds_to_create] + [c.zinc_id for c in compounds_existing]
            qs = Compound.objects.filter(zinc_id__in=ZINC_lst).prefetch_related("libraries")
            compound_pks = [c.pk for c in qs]
            lib_pks = [lib.pk]
            rels = bulk_add(LibCompoundRelation, lib_pks, compound_pks,
                    "library_id","compound_id")
            relations.extend(rels)
            created.extend(compounds_to_create)
            existed.extend(compounds_existing)
        return relations, created, existed
