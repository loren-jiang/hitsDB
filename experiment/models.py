from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from lib.models import Library, Compound
from .exp_view_process import formatSoaks, split_list, getWellIdx, getSubwellIdx
from django.db.models.signals import post_save, post_init, pre_save, m2m_changed, pre_delete, post_delete
from django.dispatch import receiver
from django.utils.functional import cached_property 
from my_utils.orm_functions import bulk_add, bulk_one_to_one_add
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db.models import Count, F, Value
from my_utils.utility_functions import chunk_list, items_at, ceiling_div, gen_circ_list, \
    PIX_TO_UM, UM_TO_PIX, IMG_SCALE, VolumeToRadius, RadiusToVolume, \
        mapUmToPix, mapPixToUm
import string
from datetime import datetime
from django.utils.timezone import make_aware
from s3.s3utils import PrivateMediaStorage
from s3.models import PrivateFile, PrivateFileJSON, PrivateFileCSV
import json 
import csv 
from django.db import transaction, IntegrityError
from django.urls import reverse, reverse_lazy
from functools import reduce 

class Project(models.Model):
    name = models.CharField(max_length=30)
    owner = models.ForeignKey(User, related_name='projects',on_delete=models.CASCADE)
    description = models.CharField(max_length=300, blank=True, null=True)
    collaborators = models.ManyToManyField(User, related_name='collab_projects',blank=True) 
    editors = models.ManyToManyField(User, related_name='editor_projects', blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    new_instance_viewname = 'proj_new'
    edit_instance_viewname = 'proj_edit'
    model_name = 'Project'

    class Meta:
        get_latest_by = "modified_date"
        constraints = [
            models.UniqueConstraint(fields=['name', 'owner'], name='unique_project_name_per_owner'),
        ]
    @classmethod
    def newInstanceUrl(cls):
        """
        Class method to return url to create new instance; compared to editInstanceUrl, this function should be a class method
        vs instance property because instance data (self.pk) is not needed
        """
        return reverse(cls.new_instance_viewname)

    @property
    def editInstanceUrl(self):
        """
        Returns url to edit class instance; should be @property because instance data is needed
        """
        return reverse(self.edit_instance_viewname, kwargs={'pk_proj':self.pk})

    @classmethod
    def getModalFormData(cls):
        """
        Class method to return data needed for modal form to edit and make new instance of model
        """ 
        from my_utils.views_helper import build_modal_form_data as func
        return func(cls) 

    def getExperimentsTable(self, exc=[]):
        """
        Get table of project's experiments

        Parameters: 
        exc (list): List of columns to exclude; should be in Model fields

        Returns (django_tables2.Table)
        """
        from .tables import ExperimentsTable
        return ExperimentsTable(self.experiments.all(), exclude=exc)

    def getCollaboratorsTable(self,exc=[]):
        """
        Get table of project's collaborators

        Parameters: 
        exc (list): List of columns to exclude; should be in Model fields

        Returns (django_tables2.Table)
        """
        from .tables import CollaboratorsTable
        return CollaboratorsTable(self.collaborators.all(), exclude=exc)

    #get list of libraries used in project's experiments
    def getLibrariesTable(self, exc=[]):
        """
        Get table of libraries that are used project's experiments and libraries that are template (isTemplate=True)

        Parameters: 
        exc (list): List of columns to exclude; should be in Model fields

        Returns (django_tables2.Table)
        """
        from .tables import LibrariesTable
        libs_qs = Library.objects.filter(experiments__in=self.experiments.all()).union(
            Library.objects.filter(isTemplate=True))
        return LibrariesTable(libs_qs, exclude=exc)

    def get_absolute_url(self):
        return "/home/projects/%i/" % self.id

    def __str__(self):
        return self.name

def defaultSubwellLocations():
    """
    Callable for the ArrayField default to subwell_locations
    """
    return list([1])

class Experiment(models.Model):
    name = models.CharField(max_length=30,)
    library = models.ForeignKey(Library, related_name='experiments', on_delete=models.CASCADE, blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='experiments')
    description = models.CharField(max_length=300, blank=True, null=True)
    protein = models.CharField(max_length=100)
    owner = models.ForeignKey(User, related_name='experiments',on_delete=models.CASCADE)
    srcPlateType = models.ForeignKey('PlateType', null=True, blank=True, on_delete=models.CASCADE, related_name='experiments_src') #only one src plate type per experiment
    destPlateType = models.ForeignKey('PlateType', null=True, blank=True, on_delete=models.CASCADE, related_name='experiments_dest') #noly one dest plate type per experiment
    subwell_locations = ArrayField(
        models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(3), MinValueValidator(1)]),
        size=3, default=defaultSubwellLocations) 
    initDataJSON = JSONField(default=dict)
    initData = models.OneToOneField(PrivateFileJSON, null=True, blank=True, on_delete=models.CASCADE, related_name='experiment')
    picklist = models.OneToOneField(PrivateFileCSV, null=True, blank=True, on_delete=models.CASCADE, related_name='experiment')

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    prev_initData_id = None #prev library to check if initData file has changed
    prev_library_id = None #prev library to check if library has changed

    desired_soak_date = models.DateTimeField(blank=True, null=True) 
    soak_export_date = models.DateTimeField(blank=True, null=True)

    picklist_download_date = models.DateTimeField(blank=True, null=True)

    new_instance_viewname = 'exp_new'
    edit_instance_viewname = 'exp_edit'
    model_name = 'Experiment'
    
    @classmethod
    def newInstanceUrl(cls):
        """
        Class method to return url to create new instance; compared to editInstanceUrl, this function should be a class method
        vs instance property because instance data (self.pk) is not needed
        """
        return reverse(cls.new_instance_viewname)

    @property
    def editInstanceUrl(self):
        """
        Returns url to edit class instance; should be @property because instance data is needed
        """
        return reverse(self.edit_instance_viewname, kwargs={'pk_exp':self.pk})

    class Meta:
        get_latest_by="modified_date"
        constraints = [
            models.UniqueConstraint(fields=['name', 'project'], name='unique_experiment_name_per_project'),
        ]

    def get_absolute_url(self):
        return "/home/exps/%i/" % self.id

    def __str__(self):
        return self.name

    @property
    def soakTime(self):
        """
        Returns time difference between current datetime and export_date
        """
        if self.soak_export_date:
            return timezone.now - self.soak_export_date
        return None

    @property
    def initDataValid(self):
        """
        Return True if self.initData exists and has all the right initialization data
        """
        if bool(self.initData):
            return True
        return False

    @property
    def getCurrentStep(self):
        """
        Gets the current step of the experiment; used for rendering main experiment view
        """
        cond0 = self.srcPlateType_id and self.destPlateType_id and self.project_id # has srcPlateType and destPlateType
        # cond1 = self.libraryValid and self.initDataValid
        cond1 = self.initDataValid and self.soaks.count()
        cond2 = self.srcPlatesValid
        cond3 = self.destPlatesValid
        
        cond4 = self.soaksValid and self.soak_export_date
        conds = [cond0, cond1, cond2, cond3, cond4] # cond1 corresponds to step 1
        if all(conds[0:5]):
            return 5
        if all(conds[0:4]): 
            return 4
        if all(conds[0:3]):
            return 3
        if all(conds[0:2]):
            return 2
        if all(conds[0:1]):
            return 1
        return 0

    def getSoakPlatePairs(self):
        """
        Pairs experiment's soaks source plate and dest plate
        Returns (list) of pairs
        """
        pairs = []
        qs = self.usedSoaks.select_related('src__plate','dest__parentWell__plate')
            # ).annotate(src_plate_id=F('src__plate_id')
            # ).annotate(dest_plate_id=F('dest__parentWell__plate_id'))
        for s in qs:
            # s.__dict__
            if s.src and s.dest:
                pair = (s.src.plate, s.dest.parentWell.plate)
                if pair not in pairs:
                    pairs.append(pair)
        return pairs

    @property
    def soaksValid(self):
        """
        Returns True if experiment soaks exist and if each soak's dest subwell and source well exist,
        else returns False
        """
        usedSoaks = self.usedSoaks

        if not(usedSoaks.count()):
            return False
        return not(usedSoaks.filter(src__isnull=True).exists()) and not(usedSoaks.filter(dest__isnull=True).exists())
        # for s in usedSoaks.select_related('src__plate', 'dest__parentWell__plate'):
        #     if not(s.src_id and s.dest_id):
        #         return False
        # return True

    @property
    def libraryValid(self):
        """
        Returns True if experiment library has compounds, else False
        """
        return self.library and self.library.compounds.count()

    @property
    def srcPlatesValid(self):
        return bool(self.plates.filter(isSource=True).count())
    
    @property
    def destPlatesValid(self):
        """
        Returns True if all dest plates have drop images, else False
        """
        dest_plates = self.plates.filter(isSource=False).prefetch_related('drop_images')
        if not(dest_plates):
            return False
        for p in dest_plates:
            if not(p.drop_images.count()):
                return False
        return True
    @property
    def platesValid(self):
        """
        Returns True if dest plates and source plates are valid, else False
        """
        return self.destPlatesValid and self.srcPlatesValid

    @property
    def libCompounds(self):
        """
        Returns compounds in experiment library ordered by id
        """
        if self.library.compounds.first():
            return self.library.compounds.order_by('id')
        else:
            return Compound.objects.none() #empty queryset

    @property
    def numSrcPlates(self):
        """
        Returns number of source plates
        """
        return self.plates.filter(isSource=True).count()
    
    @property
    def numDestPlates(self):
        """
        Returns number of dest plates
        """
        return self.plates.filter(isSource=False).count()

    def expNumSrcPlates(self):
        """
        Returns expected number of source plates based on number of compounds in library
        """
        src_plate_type = self.srcPlateType
        num_src_wells = src_plate_type.numCols * src_plate_type.numRows
        return ceiling_div(self.libCompounds.count(), num_src_wells)
  
    def expNumDestPlates(self):
        """
        Returns expected number of dest plates based on number of compounds in library
        """
        num_subwells  = len(self.subwell_locations)
        dest_plate_type = self.destPlateType
        num_dest_wells = dest_plate_type.numCols * dest_plate_type.numRows
        return ceiling_div(self.libCompounds.count(),num_dest_wells * num_subwells)

    @property
    def usedSoaks(self):
        """
        Returns the experiment's used soaks ordered by destination well 
        """
        return self.soaks.filter(useSoak=True).order_by(
            'dest__parentWell__plate__plateIdxExp',
            'dest__parentWell__name',
            'dest__idx')

    @property
    def destSubwells(self):
        """
        Returns ordered subwells in the experiment's destination plates
        """
        return SubWell.objects.filter(parentWell__plate__in=
            self.plates.filter(isSource=False)).order_by('parentWell__plate__plateIdxExp', 'parentWell__name', 'idx')

    @property
    def srcWells(self):
        """
        Returns ordered wells in the experiment's source plates
        """
        return Well.objects.filter(plate__in=self.plates.filter(isSource=True)).order_by('plate__plateIdxExp', 'name')
    
    @property
    def srcWellsWithCompounds(self):
        """
        Returns the wells in the experiment's source plates with compounds
        """
        return self.srcWells.exclude(compound__isnull=True)
    
    def processPicklist(self):
        """
        Process uploaded picklist file and updates soaks accordingly
        """
        from .utils.experiment_utils import processPicklist as func
        if getattr(self, 'picklist'):
            return func(self, self.picklist.local_upload.file) 

    def importTemplateSourcePlates(self, templateSrcPlates):
        """
        Makes new source plates from template source plates, usually with compounds

        Parameters:
        templateSrcPlates (list): list of plates that are template and source
        """
        plates = self.makeSrcPlates(len(templateSrcPlates))
        for p1, p2 in zip(plates, templateSrcPlates):
            p1.copyCompoundsFromOtherPlate(p2)

    def createSrcPlatesFromLibFile(self, numPlates, file):
        """
        Creates source plates from CSV file (https://docs.google.com/spreadsheets/d/1FRBm6wVNSpwg4d3zGCYKLQkEZjf4BP9JL0YkEJzSojw/edit?usp=sharing)
        Then update wells with the appropriate compounds specified from csv file

        Parameters:
        numPlates (int): number of empty plates to make
        file (uploaded file): CSV file to update wells with appropriate compounds (see example file above)
        """
        from .utils.experiment_utils import createSrcPlatesFromLibFile as func
        return func(self, numPlates, file)

    def priorityInterleaveSrcWellsToSoaks(self, src_wells=[], soaks=[]):
        from .utils.experiment_utils import priorityInterleaveSrcWellsToSoaks as func
        return func(self, src_wells, soaks)

    def interleaveSrcWellsToSoaks(self, src_wells=[], soaks=[]):
        """
        Match soaks to source wells interleaved by plate id

        Parameters:
        src_wells (list): List of an experiment's source wells with compounds
        soaks (list): List of an experiment's used soaks 

        Returns:
        None
        """
        from .utils.experiment_utils import interleaveSrcWellsToSoaks as func
        return func(self, src_wells, soaks)

    def matchSrcWellsToSoaks(self, src_wells=[], soaks=[]):
        """
        Match soaks to source wells by looping through one-by-one
        
        Parameters:
        src_wells (list): List of an experiment's source wells with compounds
        soaks (list): List of an experiment's used soaks 

        Returns:
        None
        """
        from .utils.experiment_utils import matchSrcWellsToSoaks as func
        return func(self, src_wells, soaks)
    
    def generateSoaks(self, transferVol=25, soakOffsetX=0, soakOffsetY=0):
        self.soaks.all().delete() #start from fresh
        ct = 0
        cmpds = self.libCompounds
        list_soaks = [None]*cmpds.count()
        list_src_wells = [w for w in self.srcWells.order_by('id')]
        list_dest_subwells = [w for w in self.destSubwells.order_by('id')]
        # a = chunk_list(list_dest_subwells, 3)
        s_w_idxs = list(map(lambda x: x-1, self.subwell_locations))
        
        list_dest_subwells = items_at(lst=list_dest_subwells, 
            chunk_size=self.destPlateType.numSubwells, idxs=s_w_idxs)
        for c in cmpds:
            src_well = list_src_wells[ct]
            dest_subwell = list_dest_subwells[ct]
            dest_subwell.hasCrystal = True
            soak = Soak(experiment_id=self.id,src=src_well,dest=dest_subwell, transferCompound=c, 
                soakOffsetX=soakOffsetX, soakOffsetY=soakOffsetY, transferVol=transferVol)
            list_soaks[ct] = soak
            ct += 1
        Soak.objects.bulk_create(list_soaks)

        cmpds_pks = [c.pk for c in cmpds]
        src_wells_pks = [w.pk for w in list_src_wells]
        dest_subwells_pks = [s_w.pk for s_w in list_dest_subwells]
        WellCompoundRelation = Well.compounds.through
        SubWellCompoundRelation = SubWell.compounds.through
        bulk_one_to_one_add(WellCompoundRelation, src_wells_pks, cmpds_pks,
            "well_id","compound_id")
        bulk_one_to_one_add(SubWellCompoundRelation, dest_subwells_pks, cmpds_pks,
            "subwell_id","compound_id")
        return
    
    def groupSoaks(self):
        src_plate_ids = [p.id for p in self.plates.filter(isSource=True)]
        chunk_size = self.srcPlateType.numResWells * len(self.subwellLocations)
        grouped_soaks = []
        for id in src_plate_ids:
            grouped_soaks.append(
                chunk_list(self.soaks.filter(src__plate_id=id), chunk_size)
            )
        return grouped_soaks

    #create the source plate and dest plates given the library size
    # num_subwells should be lte to dest_plate_type.numSubwells
    def generateSrcDestPlates(self):
        try:
            # exp_compounds = self.library.compounds.order_by('id')
            self.plates.all().delete() #start from fresh 
            src_plate_type = self.srcPlateType
            dest_plate_type = self.destPlateType
            num_compounds = self.libCompounds.count()
            num_subwells = len(self.subwell_locations)
            num_src_wells = src_plate_type.numCols * src_plate_type.numRows
            num_dest_wells = dest_plate_type.numCols * dest_plate_type.numRows
            num_src_plates = ceiling_div(num_compounds,num_src_wells)
            num_dest_plates = ceiling_div(num_compounds,num_dest_wells * num_subwells)
            src_plates_to_create = [None]*num_src_plates
            dest_plates_to_create = [None]*num_dest_plates
            # loop through and create the appropriate number of plates 
            for i in range(num_src_plates):
                src_plates_to_create[i] = Plate(name='src_'+str(i+1),plateType=src_plate_type, 
                    experiment_id=self.id, isSource=True, plateIdxExp=i+1)
                # src_plates_to_create[i].save()
            for i in range(num_dest_plates):
                dest_plates_to_create[i] = Plate(name='dest_'+str(i+1),plateType=dest_plate_type, 
                    experiment_id=self.id,isSource=False, plateIdxExp=i+1)
                # dest_plates_to_create[i].save()
            plates = Plate.objects.bulk_create(src_plates_to_create + dest_plates_to_create) #bulk create Plate objects
            for p in plates:
                p.createPlateWells() # bulk_create doesn't send signals so need to call explicitly
            return True
        except Exception as e:
            #print(e)
            return False
    
    def makeSrcPlates(self, num_plates):
        from .utils.experiment_utils import makeSrcPlates as func
        return func(self, num_plates)

    def makeDestPlates(self, num_plates):
        from .utils.experiment_utils import makeDestPlates as func
        return func(self, num_plates)

    def makePlates(self, num_plates, plate_type, plates_init_data=None):
        from .utils.experiment_utils import makePlates as func
        return func(self, num_plates, plate_type, plates_init_data=None)

    def createPlatesSoaksFromInitDataJSON(self):
        from .utils.experiment_utils import createPlatesSoaksFromInitDataJSON as func
        return func(self)
 
    # def formattedSoaks(self, qs_soaks,
    #                 s_num_rows=16, s_num_cols = 24, 
    #                 d_num_rows=8, d_num_cols=12, d_num_subwells=3):
    #     from .utils.experiment_utils import formattedSoaks as func
    #     return func(self, qs_soaks, s_num_rows, s_num_cols, d_num_rows, d_num_cols, d_num_subwells)

    # takes in exc list of column names to exclude
    def getSoaksTable(self, exc=[]):
        from .tables import SoaksTable
        qs = self.soaks.select_related('dest__parentWell__plate','src__plate',
            ).prefetch_related('transferCompound',).order_by('id')
        return SoaksTable(qs, exclude=exc)

    def getDestPlatesGUITable(self, exc=[]):
        from .tables import DestPlatesForGUITable
        return DestPlatesForGUITable(self.plates.filter(isSource=False), exclude=exc)
    # takes in exc list of column names to exclude
    def getSrcPlatesTable(self, exc=[]):
        from .tables import PlatesTable
        # might want to implement try catch
        return PlatesTable(self.plates.filter(isSource=True), exclude=exc)

    def getDestPlatesTable(self, exc=[]):
        from .tables import PlatesTable
        # might want to implement try catch
        return PlatesTable(self.plates.filter(isSource=False), exclude=exc)


class Ingredient(models.Model):
    name = models.CharField(max_length=100,)
    manufacturer = models.CharField(max_length=100, default='')
    date_dispensed = models.DateField(default=timezone.now, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Plate(models.Model):
    name = models.CharField(max_length=50)
    plateType = models.ForeignKey('PlateType', related_name='plates', on_delete=models.SET_NULL, null=True, blank=True)
    experiment = models.ForeignKey(Experiment, related_name='plates', on_delete=models.SET_NULL, null=True, blank=True)
    isSource = models.BooleanField(default=False) #is it a source plate? if not, it's a dest plate
    plateIdxExp = models.PositiveIntegerField(default=1,null=True, blank=True)
    dataSheetURL = models.URLField(max_length=200, null=True, blank=True)
    echoCompatible = models.BooleanField(default=False)
    rockMakerId = models.CharField(max_length=10, unique=True,  null=True, blank=True) #only dest plate should have rockMakerId
    isTemplate = models.BooleanField(default=False) #template plates can be copied; should only apply for source plates

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(User, related_name='plates_create', on_delete=models.SET_NULL, null=True, blank=True)
    
    new_instance_viewname = 'plate_new'
    edit_instance_viewname = 'plate_edit'
    model_name = 'Plate'

    class Meta:
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(fields=['plateIdxExp', 'isSource', 'experiment'], name='unique_src_dest_plate_idx'),
            models.CheckConstraint(check=~(models.Q(isSource=False) & models.Q(isTemplate=True)), 
                name='source_can_only_be_template'),
            models.CheckConstraint(check=~(models.Q(isSource=True) & models.Q(rockMakerId__isnull=False)), 
                name='dest_can_only_have_rockMakerId'),
        ]
        # unique_together = ('plateIdxExp', 'isSource', 'experiment')

    def __str__(self):
        string = ''
        # if self.isTemplate:
        #     string += 'Template: '
        return string + ' ' + self.name + ' (plate id: ' + str(self.id) + ')'

    def get_absolute_url(self):
        return "/home/plates/%i/" % self.id
    
    @property
    def editInstanceUrl(self):
        """
        Returns url to edit class instance; should be @property because instance data is needed
        """
        return reverse(self.edit_instance_viewname, kwargs={'pk_plate':self.pk})

    @property
    def subwells(self):
        return SubWell.objects.filter(parentWell__in=self.wells.filter())
    @property
    def numCols(self):
        return self.plateType.numCols
    @property
    def numRows(self):
        return self.plateType.numRows
    @property
    def numSubwells(self):
        return self.plateType.numSubwells
    # returns number of reservoir wells
    @property 
    def numResWells(self):
        if self.plateType:
            return self.plateType.numCols * self.plateType.numRows

    @property
    def compounds(self):
        return Compound.objects.filter(my_wells__in=self.wells.all()).order_by('my_wells__name')

    # creates appropriate wells for plate instance
    def createPlateWells(self):
        """
        """
        from .utils.plate_utils import createPlateWells as func
        return func(self)

    def updateCompounds(self, compounds, compound_dict={}):
        """
        """
        from .utils.plate_utils import updateCompounds as func
        return func(self, compounds, compound_dict)

    def copyCompoundsFromOtherPlate(self, plate):
        """
        Takes other plate (isTemplate must be True) and copy its compounds in the appropriate well locations
        """
        from .utils.plate_utils import copyCompoundsFromOtherPlate as func
        return func(self, plate)

    def removeDropImages(self):
        from .utils.plate_utils import removeDropImages as func
        return func(self)

class PlateType(models.Model):
    name = models.CharField(max_length=50, unique=True) 
    numCols = models.PositiveIntegerField(default=12, 
        validators=[
            MaxValueValidator(99),
            MinValueValidator(12)
        ])
    numRows = models.PositiveIntegerField(default=8, 
        validators=[
            MaxValueValidator(99),
            MinValueValidator(8)
        ])
    isSource = models.BooleanField(default=False) #is it a source plate? if not, it's a dest plate
    numSubwells = models.PositiveIntegerField(default=0) # num subwells per well
    # x and y synonmous with row and col respectively
    xPitch = models.DecimalField(max_digits=10, decimal_places=3) # pitch in x direction of wells [mm]
    yPitch = models.DecimalField(max_digits=10, decimal_places=3) # pitch in y direction of wells [mm]
    plateHeight = models.DecimalField(max_digits=10, decimal_places=3) # height of plate
    plateWidth = models.DecimalField(max_digits=10, decimal_places=3) #width of plate
    plateLength = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    wellDepth = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    xOffsetA1 = models.DecimalField(max_digits=10, decimal_places=3) #x postion of center of well A1 relative to top left corner of plate
    yOffsetA1 = models.DecimalField(max_digits=10, decimal_places=3) #y postion of center of well A1 relative to top left corner of plate
    dataSheetURL = models.URLField(max_length=200, null=True, blank=True)
    echoCompatible = models.BooleanField(default=False, null=True, blank=True)
    isSBS = models.BooleanField(default=True)

    maxResVol = models.DecimalField(max_digits=10, decimal_places=0, default=1000) #in uL
    minResVol = models.DecimalField(max_digits=10, decimal_places=0, default=50) #in uL

    maxDropVol = models.DecimalField(max_digits=10, decimal_places=0,default=5.0) #in uL
    minDropVol = models.DecimalField(max_digits=10, decimal_places=0, default=0.5) #in uL

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    # returns number of reservoir wells
    @property 
    def numResWells(self):
        """
        TODO: write DOCSTRING
        """
        return self.numCols * self.numRows
    
    @property
    def numSubwellsTotal(self):
        """
        TODO: write DOCSTRING
        """
        return self.numResWells * self.numSubwells

    @property
    def wellDict(self):
        """
        TODO: write DOCSTRING
        """
        from .utils.plate_utils import createWellDict
        return createWellDict(self.numRows, self.numCols)

    def __str__(self):
        return self.name

    @classmethod
    def createEchoSourcePlate(cls):
        try: 
            instance = cls(
                name="Echo 384-well source plate",
                numRows=16,
                numCols=24,
                xPitch = 4.5,
                yPitch = 4.5,
                plateLength = 127.76,
                plateWidth = 85.48,
                plateHeight = 10.48,
                xOffsetA1 = 12.13,
                yOffsetA1 = 8.99,
                echoCompatible=True,
                isSource=True,
                dataSheetURL=''
            )
            instance.save()
        except:
            pass
        return instance

    @classmethod
    def create96MRC3DestPlate(cls):
        try:
            instance = cls(
                name="Swiss MRC-3 96 well microplate",
                numRows=8,
                numCols=12,
                numSubwells = 3,
                xPitch = 9,
                yPitch = 9,
                plateLength = 127.5,
                plateWidth = 85.3,
                plateHeight = 11.7,
                xOffsetA1 = 16.1,
                yOffsetA1 = 8.9,
                echoCompatible=True,
                isSource=False,
                dataSheetURL=''
            )
            instance.save()
        except:
            pass
        return instance

class Well(models.Model):
    validWellName = RegexValidator(regex=r'^[A-Z]\d{2}$', message='Enter valid well name')
    name = models.CharField(max_length=3, 
        validators=[validWellName]
        ) #format should be A01, X10, etc.
    compound = models.ForeignKey(Compound, related_name='my_wells', null=True, blank=True, on_delete=models.SET_NULL)
    compounds = models.ManyToManyField(Compound, related_name='wells', blank=True) #can a well have more than one compound???
    maxResVol = models.DecimalField(max_digits=10, decimal_places=0)
    minResVol = models.DecimalField(max_digits=10, decimal_places=0)
    plate = models.ForeignKey(Plate, on_delete=models.CASCADE, related_name='wells')
    screen_ingredients = models.ManyToManyField(Ingredient, related_name='wells', blank=True)
    wellIdx = models.PositiveIntegerField(default=0)
    wellRowIdx = models.PositiveIntegerField(default=0)
    wellColIdx = models.PositiveIntegerField(default=0)
    min_priority = 1
    max_priority = 10
    priority = models.PositiveIntegerField(default=10, validators=[MinValueValidator(min_priority), MaxValueValidator(max_priority)])
    edit_instance_viewname = 'well_edit'

    @property
    def editInstanceUrl(self):
        return reverse(self.edit_instance_viewname, kwargs={'pk':self.pk})
        
    @classmethod
    def getPriorityRange(cls):
        return range(cls.min_priority, cls.max_priority + 1)

    @property
    def numSubwells(self):
        return self.subwells.count()

    def __str__(self):
        return str(self.plate.plateIdxExp) + '_' + self.name

    class Meta:
        ordering = ('name', )
        # ordering = ('wellRowIdx','wellColIdx')
        constraints = [
            models.UniqueConstraint(fields=['plate_id', 'name'], name='unique_well_name_in_plate')
        ]
        # unique_together = ('plate', 'name',) #ensure that each plate has unique well names

class SubWell(models.Model):
    validSubwellName = RegexValidator(regex=r'^[A-Z]\d{2}_[123]$', message='Enter valid well name')
    name = models.CharField(max_length=5, 
        validators=[validSubwellName]
        )
    idx = models.PositiveIntegerField(default=1) #CHANGE TO 0-indexed?
    xPos = models.DecimalField(max_digits=10, decimal_places=2,default=0) # relative to center of well
    yPos = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    maxDropVol = models.DecimalField(max_digits=10, decimal_places=0,default=5.0) #in uL
    minDropVol = models.DecimalField(max_digits=10, decimal_places=0, default=0.5) #in uL
    parentWell = models.ForeignKey(Well,on_delete=models.CASCADE, related_name='subwells')
    compounds = models.ManyToManyField(Compound, related_name='subwells', blank=True)
    protein = models.CharField(max_length=100, default="")
    hasCrystal = models.BooleanField(default=True)
    useSoak = models.BooleanField(default=False)

    def __str__(self):
        return self.name
        # return repr(self.parentWell) + "_" + str(self.idx)

    class Meta:
        ordering = ('idx',)
        constraints = [
            models.UniqueConstraint(fields=['parentWell_id', 'idx'], name='unique_subwell_in_well')
        ]
        unique_together = ('parentWell', 'idx',) 

class Soak(models.Model):
    experiment = models.ForeignKey(Experiment,on_delete=models.CASCADE,null=True, blank=True, related_name='soaks',)
    
    dest = models.OneToOneField(SubWell, on_delete=models.CASCADE,null=True, blank=True, related_name='soak',)
    src = models.OneToOneField(Well, on_delete=models.SET_NULL,null=True, blank=True, related_name='soak',)
    transferCompound = models.ForeignKey(Compound, on_delete=models.CASCADE,null=True, blank=True, related_name='soaks',)
    
    soakOffsetX = models.DecimalField(max_digits=10, decimal_places=2,default=0, validators=[MinValueValidator(0.0)])
    soakOffsetY = models.DecimalField(max_digits=10, decimal_places=2,default=0, validators=[MinValueValidator(0.0)])
    soakVolume = models.DecimalField(max_digits=10, decimal_places=2, default=25, validators=[MinValueValidator(0.0)]) # in nL

    drop_x = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um
    drop_y = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um
    drop_radius = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um

    well_x = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um
    well_y = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um
    well_radius = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um

    drop_x_initial = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um
    drop_y_initial = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um
    drop_radius_initial = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um

    well_x_initial = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um
    well_y_initial = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um
    well_radius_initial = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um

    useSoak = models.BooleanField(default=False)
    saveCount = models.PositiveIntegerField(default=0)
    saveTimeStamp = models.DateTimeField(null=True, blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    
    storage_position = models.PositiveIntegerField(null=True, blank=True)
    storage_barcode = models.CharField(max_length=100, default='')
    storage_location = models.CharField(max_length=20, default='')
    storage = models.ForeignKey('XtalContainer', on_delete=models.SET_NULL, null=True, blank=True, related_name='soaks')

    isMounted = models.BooleanField(default=False)
    mountedTimeStamp = models.DateTimeField(null=True, blank=True)

    shifterComment = models.CharField(max_length=100, default='')
    shifterCrystalID = models.CharField(max_length=10, default='')
    shifterArrivalTime = models.DateTimeField(null=True, blank=True)
    shifterDepartureTime = models.DateTimeField(null=True, blank=True)

    barcode = models.CharField(max_length=50, default='')
    shifterExternalComment = models.CharField(max_length=100, default='')

    @property
    def transferVol(self):
        return RadiusToVolume(float(self.drop_radius) * UM_TO_PIX) #arg should be in um, return should be in uL

    @property 
    def offset_XY_um(self):
        """Retuns the computed offset of the target soak relative to the target well"""
        drop_xyr = self.drop_XYR_um
        well_xyr = self.well_XYR_um
        return [drop_xyr[0] - well_xyr[0], drop_xyr[1] - well_xyr[1]]

    @property
    def soak_XYR_um(self):
        """"""
        return list(map(lambda x: float(x), [self.soakOffsetX, self.soakOffsetY, VolumeToRadius(self.soakVolume)]))

    @property
    def well_XYR_um(self):
        """Returns the target well x, y, and radius in pixels"""
        return list(map(lambda x: float(x), [self.well_x, self.well_y, self.well_radius]))

    @property
    def well_XYR_pix(self):
        """Returns the target well x, y, and radius in pixels"""
        return mapUmToPix([self.well_x, self.well_y, self.well_radius])
    
    @property
    def drop_XYR_um(self):
        """Returns the target drop x, y, and radius in pixels"""
        return list(map(lambda x: float(x), [self.drop_x, self.drop_y, self.drop_radius]))

    @property
    def drop_XYR_pix(self):
        """Returns the target drop x, y, and radius in pixels"""
        return mapUmToPix([self.drop_x, self.drop_y, self.drop_radius])

    def __str__(self):
        return "soak_" + str(self.id)
        # return self.experiment.name + "_soak_" + str(self.id)

class XtalContainer(models.Model):
    name = models.CharField(unique=True, null=True, blank=True, max_length=25)
    type = models.CharField(max_length=25, default='') #Must be 'puck' or 'cane'

    class Meta:
        constraints = [
            models.CheckConstraint(check=(models.Q(type__in=['puck', 'cane'])), name="type_is_puck_or_cane"), 
        ]

# SIGNALS -----------------------------------------------------
# @receiver(m2m_changed, sender=Project.editors.through)
# def ensure_editor_is_collaborator(sender, instance, action, reverse, model, pk_set, using, **kwargs ):
#     """
#     If project's editor is not a collaborator, add as collaborator
#     """
#     if action == 'post_add':
#         instance.collaborators.add(*[u for u in User.objects.filter(pk__in=list(pk_set))])

# @receiver(post_save, sender=Project)
# def process_project_post_save(sender, instance, created, **kwargs):
#     """
#     """
#     if created:
#         users_in_groups = User.objects.filter(groups__in=instance.owner.groups.all())
#         instance.collaborators.add([u for u in users_in_groups])

@receiver(post_save, sender=Experiment)
def process_experiment_post_save(sender, instance, created, **kwargs):
    """
    If initData PrivateFile exists, try to create plates and soaks from it
    """
    def delete_plates_soaks_on_library_change(instance, created):
        if instance.prev_library_id != instance.library_id and not(created):
            instance.plates.all().delete()
            instance.soaks.all().delete()
            reset = {'srcPlateType':None, 'destPlateType':None, 'subwell_locations':[]}
            Experiment.objects.filter(id=instance.id).update(**reset) # does not call save() so no signals emitted

    def experiment_update_state(instance, created):
        if instance.prev_library_id != instance.library_id and not(created):
            instance.prev_library_id = instance.library_id
        if instance.prev_initData_id != instance.initData_id and not(created):
            instance.prev_initData_id = instance.initData_id

    def create_plates_and_soaks_init_data(instance, created):
        if instance.initData_id and (instance.prev_initData_id != instance.initData_id or created):
            # try:
                # read file and save to JSON field initDataJSON
            post_save.disconnect(process_experiment_post_save, sender=Experiment) 
            try:
                # data_json = reduce(lambda s1,s2: s1 + str(s2, encoding='utf-8').replace("'", "\""), instance.initData.local_upload.chunks(), '')
                data_json = ""
                for c in instance.initData.local_upload.chunks():
                    data_json += str(c, encoding='utf-8').replace("'", "\"")
                instance.initDataJSON = json.loads(data_json)
            except(TypeError, OverflowError, ValueError):
                instance.initData = None
                instance.initDataJSON = None
            instance.save()

            instance.createPlatesSoaksFromInitDataJSON()
            post_save.connect(process_experiment_post_save, sender=Experiment)

    create_plates_and_soaks_init_data(instance, created)
    experiment_update_state(instance, created)


@receiver(post_init, sender=Experiment)
def remember_experiment_state(sender, instance, **kwargs):
    if instance.library:    
        instance.prev_library_id = instance.library.id
    if instance.initData:
        instance.prev_initData_id = instance.initData.id

@receiver(pre_delete, sender=Experiment)
def process_experiment_pre_delete(sender, instance, **kwargs):
    def delete_plates(sender, instance):
        """
        Deletes experiment's plates, with the exception of source plates that are templates
        """
        exp = instance
        dest_plates = exp.plates.filter(isSource=False) 
        dest_plates.delete()
        src_plates = exp.plates.filter(isSource=True)
        for p in src_plates:
            if p.isTemplate:
                exp.plates.remove(p)
            else:
                p.delete()
    delete_plates(sender, instance)

@receiver(pre_save, sender=Soak)
def increment_save_count(sender, instance, **kwargs):
    instance.saveCount += 1

@receiver(post_save, sender=Plate)
def createPlateWellsPostSave(sender, instance, created, **kwargs):
    """
    On post_save signal, create wells based on instance's plateType
    """
    if created: # we only want to create wells and subwells once for plates on model creation
        instance.createPlateWells()
    return 

@receiver(post_save, sender=Plate)
def sourcePlateSetToTemplatePostCreate(sender, instance, created, **kwargs):
    """
    On post_save signal, set isTemplate to True if plate is created and is a source plate
    """
    if instance.isSource and created:
        instance.isTemplate = True
        post_save.disconnect(sourcePlateSetToTemplatePostCreate, sender=Plate)
        instance.save()
        post_save.connect(sourcePlateSetToTemplatePostCreate, sender=Plate)
    return 
