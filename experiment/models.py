from django.db import models
from datetime import date
from django.contrib.auth.models import User, Group
from django.utils import timezone

# Create your models here.
class Library(models.Model):
    name = models.CharField(max_length=30, unique=True)
    # name = models.CharField(max_length=30, )
    description = models.CharField(max_length=300, default='')
    groups = models.ManyToManyField(Group, related_name='libraries',)
    isTemplate = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class Project(models.Model):
    name = models.CharField(max_length=30)
    owner = models.ForeignKey(User, related_name='projects',on_delete=models.CASCADE)
    dateTime = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=300)
    collaborators = models.ManyToManyField(User, related_name='collab_projects',blank=True)

    class Meta:
        get_latest_by = "dateTime"
        
class Experiment(models.Model):
    name = models.CharField(max_length=30)
    library = models.ForeignKey(Library, related_name='experiments',
        on_delete=models.CASCADE, null=True, blank=True)#need to create Library model
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name='experiments')
    description = models.CharField(max_length=300)
    dateTime = models.DateTimeField(auto_now_add=True)
    protein = models.CharField(max_length=100)
    owner = models.ForeignKey(User, related_name='experiments',on_delete=models.CASCADE)
    
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

class Compound(models.Model): #doesnt need to be unique?
    # nameInternal = models.CharField(max_length=100, unique=True) 
    nameInternal = models.CharField(max_length=100,)
    chemFormula = models.CharField(max_length=100, default='')
    manufacturer = models.CharField(max_length=100, default='')
    library = models.ForeignKey(Library, related_name='compounds', on_delete=models.CASCADE, null=True, blank=True)
    #not all smiles have unique zincID, or perhaps vice versa
    zinc_id = models.CharField(max_length=30, default='')
    smiles = models.CharField(max_length=200, unique=True)
    molWeight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    concentration = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    chemName = models.CharField(max_length=1000, default='')
    def __str__(self):
        return self.nameInternal


class Plate(models.Model):
    name = models.CharField(max_length=30, default="plate_name") #do I need unique?
    plateType = models.CharField(max_length=100)
    numCols = models.PositiveIntegerField(default=12)
    numRows = models.PositiveIntegerField(default=8)
    xPitch = models.DecimalField(max_digits=10, decimal_places=3) # pitch in x direction of wells [mm]
    yPitch = models.DecimalField(max_digits=10, decimal_places=3) # pitch in y direction of wells [mm]
    height = models.DecimalField(max_digits=10, decimal_places=3) # height of plate
    width = models.DecimalField(max_digits=10, decimal_places=3) #width of plate
    xPosA1 = models.DecimalField(max_digits=10, decimal_places=3) #x postion of well A1 relative to top left corner of plate
    yPosA1 = models.DecimalField(max_digits=10, decimal_places=3) #y postion of well A1 relative to top left corner of plate
    # experiments can have multiple plates, but plates can only have one experiment
    experiment = models.ForeignKey(Experiment, related_name='plates', on_delete=models.CASCADE, null=True, blank=True)
    isSource = models.BooleanField(default=False) #is it a source plate?
    isTemplate = models.BooleanField(default=False) #is it a template we want build plates from?
    # index of plate in certain experiment (needed for echo instruction generation)
    plateIdxExp = models.PositiveIntegerField(default=1)

    @property
    def wellDict(self):
        numWells = self.numRows * self.numCols
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 
            'L', 'M', 'N','O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']

        wellNames = [None] *  numWells

        wellIdx = 0
        for rowIdx in range(self.numRows):
          for colIdx in range(self.numCols):
            s = letters[rowIdx] + str(colIdx + 1)
            wellNames[wellIdx] = s
            wellIdx += 1

        return dict(zip(wellNames, range(numWells)))

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)

    @classmethod
    def create384SourcePlate(cls, name,
        plateType="Greiner 384 well microplate",
        numRows=16,
        numCols=24,
        xPitch = 4.5,
        yPitch = 4.5,
        width = 127.76,
        height = 85.48,
        xPosA1 = 12.13,
        yPosA1 = 8.99,
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
            xPosA1 = xPosA1,
            yPosA1 = yPosA1,
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
        xPosA1 = 16.1,
        yPosA1 = 8.9,
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
            xPosA1 = xPosA1,
            yPosA1 = yPosA1,
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

class Well(models.Model):
    name = models.CharField(max_length=3) #format should be A1, X10, etc.
    compounds = models.ManyToManyField(Compound, related_name='wells', null=True, blank=True) #can a well have more than one compound???
    maxResVol = models.DecimalField(max_digits=10, decimal_places=0)
    minResVol = models.DecimalField(max_digits=10, decimal_places=0)
    plate = models.ForeignKey(Plate, on_delete=models.CASCADE, related_name='wells',null=True, blank=True)
    crystal_screen = models.ForeignKey(CrystalScreen, on_delete=models.CASCADE,related_name='wells',null=True, blank=True)
    wellIdx = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)

class SubWell(models.Model):
    #relative to A1 well center
    idx = models.PositiveIntegerField(default=1)
    xPos = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    yPos = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    maxDropVol = models.DecimalField(max_digits=10, decimal_places=0,default=5.0) #in uL
    minDropVol = models.DecimalField(max_digits=10, decimal_places=0, default=0.5) #in uL
    parentWell = models.ForeignKey(Well,on_delete=models.CASCADE, related_name='subwells',null=True, blank=True)
    compounds = models.ManyToManyField(Compound, related_name='subwells',null=True, blank=True)
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
############# DEFAULT MODEL CLASS CREATION ########## 
# #creates default source plate w/o compounds (can be added later)
# def get_default_source_plate():
#   plate384, created = Plate.objects.get_or_create(
#       name="greiner 384 well microplate",
#       numRows=16,
#       numCols=24,
#       maxResVol = 130,
#       minResVol = 10,
#       xPitch = 4.5,
#       yPitch = 4.5,
#       width = 127.76,
#       height = 85.48,
#       xPosA1 = 12.13,
#       yPosA1 = 8.99,
#       )

#   # create/add wells to plate object using for loop (dont need to add compounds yet)
#   return plate384.id

# def get_default_dest_plate():
#   subwell1 = SubWell.objects.get_or_create(
#       idx = 0,
#       xPos = 4.21, #in mm
#       yPos = 1.55, #in mm
#       maxDropVol = 5, #in uL
#       minDropVol = 1, #in uL
#       )

#   subwell2 = SubWell.objects.get_or_create(
#       idx = 1,
#       xPos = 4.21, #in mm
#       yPos = -1.55, #in mm
#       maxDropVol = 5, #in uL
#       minDropVol = 1, #in uL
#       )
#   plate96, created = Plate.objects.get_or_create(
#       name="swiss mrc 2-well microplate",
#       numRows=8,
#       numCols=12,
#       maxResVol = 100,
#       minResVol = 50,
#       xOffset = 9.03,
#       yOffset = 9.03,
#       xLength = 127.5,
#       yLength = 85.3,
#       xPosA1 = 14.1,
#       yPosA1 = 11.04,
#       )
#   plate96.subWells.add(subwell1[0])
#   plate96.subWells.add(subwell2[0])

#   return plate96.id

