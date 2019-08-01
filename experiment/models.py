from django.db import models
from datetime import date
from django.contrib.auth.models import User, Group
from django.utils import timezone
from import_ZINC.models import Library, Compound
from .exp_view_process import formatSoaks, ceiling_div, chunk_list, split_list, getWellIdx, getSubwellIdx
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Project(models.Model):
    name = models.CharField(max_length=30)
    owner = models.ForeignKey(User, related_name='projects',on_delete=models.CASCADE)
    dateTime = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=300)
    collaborators = models.ManyToManyField(User, related_name='collab_projects',blank=True) 
    
    # takes in exc list of column names to exclude
    def getExperimentsTable(self, exc=[]):
        from .tables import ExperimentsTable
        # might want to implement try catch
        return ExperimentsTable(self.experiments.all(), exclude=exc)

    def getCollaboratorsTable(self,exc=[]):
        from .tables import CollaboratorsTable
        # might want to implement try catch
        return CollaboratorsTable(self.collaborators.all(), exclude=exc)

    #get list of libraries used in project's experiments
    def getLibrariesTable(self, exc=[]):
        from .tables import LibrariesTable
        qs = Library.objects.filter(experiments__in=self.experiments.all()).union(
            Library.objects.filter(isTemplate=True))
        return LibrariesTable(qs)

    class Meta:
        get_latest_by = "dateTime"

    def get_absolute_url(self):
        return "/proj/%i/" % self.id
        
class Experiment(models.Model):
    name = models.CharField(max_length=30)
    library = models.ForeignKey(Library, related_name='experiments',
        on_delete=models.CASCADE, null=True, blank=True)#need to create Library model
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name='experiments')
    description = models.CharField(max_length=300)
    dateTime = models.DateTimeField(auto_now_add=True)
    protein = models.CharField(max_length=100)
    owner = models.ForeignKey(User, related_name='experiments',on_delete=models.CASCADE)

    # Arguments
    # - source_params: {
    #                   'num_wells':# of wells/plate, 
    #                   'num_subwells':# of subwells/well
    #                   }
    # - dest_params: same thing as above but for destination plates
    def formatSoaks(self, num_src_plates,
        num_dest_plates, s_num_wells=384,d_num_wells=96, d_num_subwells=3):
       

        qs_soaks = self.soaks.select_related('dest__parentWell__plate','src__plate',
            ).prefetch_related('transferCompound__library',
            ).order_by('id')

        soaks_lst = [soak for soak in qs_soaks]
        src_wells = [0]*num_src_plates*s_num_wells
        dest_subwells = [0]*num_dest_plates*d_num_wells*d_num_subwells
        subwells = [0]*3 #three subwells locations

        for j in range(len(soaks_lst)):
            s = soaks_lst[j]
            src = s.src # source Well
            src_well_idx = src.wellIdx
            src_plate_idx = src.plate.plateIdxExp
            s_w_idx = getWellIdx(src_plate_idx,src_well_idx, s_num_wells)
            dest = s.dest
            dest_subwell_idx = dest.idx
            dest_parentwell_idx = dest.parentWell.wellIdx
            dest_plate_idx = dest.parentWell.plate.plateIdxExp
            d_sw_idx = getSubwellIdx(dest_plate_idx,dest_parentwell_idx,
                dest_subwell_idx, d_num_wells,d_num_subwells) # MAKE MODULAR
            compound = s.transferCompound
            src_wells[s_w_idx] = {
                                'well_id':src.id, 
                                'well_name':src.name, 
                                'compound':compound.nameInternal,
                                'dest_subwell_id':dest.id,
                                'soak_id':s.id
                                }


            dest_subwells[d_sw_idx] = {
                                'src_well_id': src.id,
                                'parentWell_id': dest.parentWell.id,
                                'parentWell_name': dest.parentWell.name,
                                'subwell_id':dest.id,
                                'subwell_idx':dest.idx,
                                'compound':compound.nameInternal,
                                }
            # except:
            #     break

        src_wells = chunk_list(src_wells,24)
        dest_subwells = chunk_list(dest_subwells,3) #group subwells 1-3 into well
        dest_subwells = chunk_list(dest_subwells,12) #group columns into row

        return {'src_plates':split_list(src_wells,num_src_plates), 
                'dest_plates':split_list(dest_subwells,num_dest_plates),
                }

    # takes in exc list of column names to exclude
    def getSoaksTable(self, exc=[]):
        from .tables import SoaksTable
        # might want to implement try catch
        return SoaksTable(self.soaks.all(), exclude=exc)

    # takes in exc list of column names to exclude
    def getPlatesTable(self, exc=[]):
        from .tables import PlatesTable
        # might want to implement try catch
        return getPlatesTable(self.soaks.all(), exclude=exc)

    def get_absolute_url(self):
        return "/exp/%i/" % self.id

    def __str__(self):
        return self.name
    class Meta:
        get_latest_by = "dateTime"


class CrystalScreen(models.Model):
    name = models.CharField(max_length=100,)
    manufacturer = models.CharField(max_length=100, default='')
    date_dispensed = models.DateField(default=timezone.now, blank=True)

    def __str__(self):
        return self.name


class Plate(models.Model):
    name = models.CharField(max_length=30, default="plate_name") #do I need unique?
    formatType = models.CharField(max_length=100)
    numCols = models.PositiveIntegerField(default=12)
    numRows = models.PositiveIntegerField(default=8)
    # x and y synonmous with row and col respectively
    xPitch = models.DecimalField(max_digits=10, decimal_places=3) # pitch in x direction of wells [mm]
    yPitch = models.DecimalField(max_digits=10, decimal_places=3) # pitch in y direction of wells [mm]
    plateHeight = models.DecimalField(max_digits=10, decimal_places=3) # height of plate
    plateWidth = models.DecimalField(max_digits=10, decimal_places=3) #width of plate
    plateLength = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    wellDepth = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    xOffsetA1 = models.DecimalField(max_digits=10, decimal_places=3) #x postion of center of well A1 relative to top left corner of plate
    yOffsetA1 = models.DecimalField(max_digits=10, decimal_places=3) #y postion of center of well A1 relative to top left corner of plate
    # experiments can have multiple plates, but plates can only have one experiment
    experiment = models.ForeignKey(Experiment, related_name='plates', on_delete=models.CASCADE, null=True, blank=True)
    isSource = models.BooleanField(default=False) #is it a source plate? if not, it's a dest plate
    isTemplate = models.BooleanField(default=False,null=True, blank=True) #is it a template we want build plates from?
    isCustom = models.BooleanField(default=False, null=True, blank=True) #is it a custom plate that the user modified (e.g. custom well offsets)
    # index of plate in certain experiment (needed for echo instruction generation)
    plateIdxExp = models.PositiveIntegerField(default=1,null=True, blank=True)
    dataSheetURL = models.URLField(max_length=200, null=True, blank=True)
    echoCompatible = models.BooleanField(default=False, null=True, blank=True)

    def importLibrary(self, file):
        return
    # returns number of reservoir wells
    @property 
    def numResWells(self):
        return self.numCols * self.numRows

    @property
    def wellDict(self):
        numWells = self.numResWells
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 
            'L', 'M', 'N','O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']

        wellNames = [None] *  numWells

        wellIdx = 0
        for rowIdx in range(self.numRows):
          for colIdx in range(self.numCols):
            let = letters[rowIdx]
            num = str(colIdx + 1)
            if (len(num)==1):
                num = "0" + num
            s = let + num
            wellNames[wellIdx] = s
            wellIdx += 1

        return dict(zip(wellNames, range(numWells))) 

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)

    @classmethod
    def createEchoSourcePlate(cls):
        instance = cls(
            name="",
            formatType="Echo 384-well source plate",
            numRows=16,
            numCols=24,
            xPitch = 4.5,
            yPitch = 4.5,
            plateLength = 127.76,
            plateWidth = 85.48,
            plateHeight = 10.48,
            xOffsetA1 = 12.13,
            yOffsetA1 = 8.99,
            isSource = True,
            echoCompatible=True,)
        instance.save()

        well_lst = [None]*len(instance.wellDict)
        for key, val in instance.wellDict.items():
            well_idx = val + 1
            well_lst[val] = Well(name=key, wellIdx=well_idx,
                maxResVol=130, minResVol=10, plate_id=instance.pk)
            # instance.wells.create(name=key, maxResVol=130, minResVol=10)
        Well.objects.bulk_create(well_lst)
        return instance

    @classmethod
    def create384SourcePlate(cls, name,
        formatType="Greiner 384 well microplate",
        numRows=16,
        numCols=24,
        xPitch = 4.5,
        yPitch = 4.5,
        width = 127.76,
        height = 85.48,
        xOffsetA1 = 12.13,
        yOffsetA1 = 8.99,
        isSource = True,):
        
        instance = cls(
            name=name,
            plateType=plateType,
            numRows=numRows,
            numCols=numCols,
            xPitch = xPitch,
            yPitch = yPitch,
            width = width,
            height = height,
            xOffsetA1 = xPosA1,
            yOffsetA1 = yPosA1,
            isSource = isSource)
        instance.save()
        well_lst = [None]*len(instance.wellDict)
        for key, val in instance.wellDict.items():
            well_idx = val + 1
            well_lst[val] = Well(name=key, wellIdx=well_idx,
                maxResVol=130, minResVol=10, plate_id=instance.pk)
            # instance.wells.create(name=key, maxResVol=130, minResVol=10)
        Well.objects.bulk_create(well_lst)
        return instance

    @classmethod
    def create96MRC3DestPlate(cls, name,
        plateType="Swiss MRC-3 96 well microplate",
        numRows=8,
        numCols=12,
        xPitch = 9,
        yPitch = 9,
        width = 127.5,
        height = 85.3,
        xOffsetA1 = 16.1,
        yOffsetA1 = 8.9,
        isSource = False):
        
    
        instance= cls(
            name=name,
            plateType=plateType,
            numRows=numRows,
            numCols=numCols,
            xPitch = xPitch,
            yPitch = yPitch,
            width = width,
            height = height,
            xOffsetA1 = xPosA1,
            yOffsetA1 = yPosA1,
            isSource = isSource)
        instance.save()
        well_lst = [None]*len(instance.wellDict)
        for key, val in instance.wellDict.items():
            well_idx = val + 1
            # instance.wells.create(name=key, maxResVol=130, minResVol=10)
            well_lst[val] = Well(name=key, wellIdx=well_idx,
                maxResVol=130, minResVol=10, plate_id=instance.pk)
            
        Well.objects.bulk_create(well_lst)
            
        for well in instance.wells.all():
            well.subwells.create(idx=1,xPos= -3.8,yPos=0.25,)
            well.subwells.create(idx=2,xPos= -3.8,yPos=4.25, )
            well.subwells.create(idx=3,xPos= 0, yPos=4.25, )
        return instance

@receiver(post_save, sender=Plate)
def createPlateWells(sender, instance, created, **kwargs):
    # creates appropriate number of wells for plate instance
    numResWells = instance.numResWells
    return 

class Well(models.Model):
    name = models.CharField(max_length=3) #format should be A1, X10, etc.
    compounds = models.ManyToManyField(Compound, related_name='wells', blank=True) #can a well have more than one compound???
    # compound = models.ForeignKey(Compound, on_delete=models.CASCADE, related_name='well',null=True, blank=True)
    maxResVol = models.DecimalField(max_digits=10, decimal_places=0)
    minResVol = models.DecimalField(max_digits=10, decimal_places=0)
    plate = models.ForeignKey(Plate, on_delete=models.CASCADE, related_name='wells',null=True, blank=True)
    crystal_screen = models.ForeignKey(CrystalScreen, on_delete=models.CASCADE,related_name='wells',null=True, blank=True)
    wellIdx = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.name

    class Meta:
        ordering = ('wellIdx',)

class SubWell(models.Model):
    #relative to A1 well center
    idx = models.PositiveIntegerField(default=1) #CHANGE TO 0-indexed?
    xPos = models.DecimalField(max_digits=10, decimal_places=2,default=0) # relative to center of 
    yPos = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    maxDropVol = models.DecimalField(max_digits=10, decimal_places=0,default=5.0) #in uL
    minDropVol = models.DecimalField(max_digits=10, decimal_places=0, default=0.5) #in uL
    parentWell = models.ForeignKey(Well,on_delete=models.CASCADE, related_name='subwells',null=True, blank=True)
    compounds = models.ManyToManyField(Compound, related_name='subwells', blank=True)
    protein = models.CharField(max_length=100, default="")
    #src_plate_well = models.CharField(max_length=20,default="")
    #expSrcWell = models.ForeignKey(Well, on_delete=models.CASCADE, related_name='dest_subwells',null=True,blank=True) #experiment source well 
    hasCrystal = models.BooleanField(default=False)

    def __str__(self):
        return "Subwell_" + str(self.idx)

    class Meta:
        ordering = ('idx',)

class Soak(models.Model):
    experiment = models.ForeignKey(Experiment,on_delete=models.CASCADE,null=True, blank=True, related_name='soaks',)
    
    dest = models.OneToOneField(SubWell, on_delete=models.CASCADE,null=True, blank=True, related_name='soak',)
    src = models.OneToOneField(Well, on_delete=models.CASCADE,null=True, blank=True, related_name='soak',)
    transferCompound = models.ForeignKey(Compound, on_delete=models.CASCADE,null=True, blank=True, related_name='soaks',)
    transferVol = models.PositiveIntegerField(default=25) # in nL
    #relative to center of subwell
    soakOffsetX = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    soakOffsetY = models.DecimalField(max_digits=10, decimal_places=2,default=0)


def createWellDict(numCol, numRow):
    numWells = numRow * numCol
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 
        'L', 'M', 'N','O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']

    wellNames = [None] *  numWells

    wellIdx = 0
    for colIdx in range(numCol):
      for rowIdx in range(numRow):
        s = letters[rowIdx] + str(colIdx + 1)
        wellNames[wellIdx] = s
        wellIdx += 1

    return dict(zip(wellNames, range(numWells)))

def enum_well_location(s):
    # format needs to be [letter][0-9][0-9]
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
                'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']
    lettersRange = range(len(letters))
    dic = dict(zip(letters, lettersRange))
    l, d = s[0], s[0:2]

    if len(s) != 3:
        return 
    else:
        return dic[l] + int(d)
