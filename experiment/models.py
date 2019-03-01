from django.db import models
from django.contrib.auth.models import User, Group

# Create your models here.
class Compound(models.Model):
	nameInternal = models.CharField(max_length=100, unique=True)
	chemFormula = models.CharField(max_length=100, default='')
	manufacturer = models.CharField(max_length=100, default='')
	#not all smiles have unique zincID, or perhaps vice versa
	zinc_id = models.CharField(max_length=30, default='')
	smiles = models.CharField(max_length=200, unique=True)
	molWeight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	concentration = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	# Well = models.CharField(max_length=5)
	chemName = models.CharField(max_length=1000, default='')
	def __str__(self):
		return str({'nameInternal':self.nameInternal,
				'chemFormula':self.chemFormula,
				'smiles':self.smiles,})	

class SubWell(models.Model):
	#relative to A1 well center
	idx = models.PositiveIntegerField(default=1)
	xPos = models.DecimalField(max_digits=10, decimal_places=2,default=0)
	yPos = models.DecimalField(max_digits=10, decimal_places=2,default=0)
	maxDropVol = models.DecimalField(max_digits=10, decimal_places=0) #in uL
	minDropVol = models.DecimalField(max_digits=10, decimal_places=0) #in uL
	def __str__(self):
		return str((self.idx, self.xPos, self.yPos))

class Well(models.Model):
	name = models.CharField(max_length=3,unique=True) #format should be A01, X10, etc.
	compounds = models.ForeignKey(Compound, on_delete=models.CASCADE, related_name='+', null=True, blank=True) #can a well have more than one compound???
	subWells = models.ForeignKey(SubWell,on_delete=models.CASCADE, related_name='+',null=True, blank=True)
	maxResVol = models.DecimalField(max_digits=10, decimal_places=0)
	minResVol = models.DecimalField(max_digits=10, decimal_places=0)
	def __str__(self):
		return self.name
		
class Plate(models.Model):
	name = models.CharField(max_length=30, unique=True) #do I need unique?
	numCols = models.PositiveIntegerField(default=12)
	numRows = models.PositiveIntegerField(default=8)
	xPitch = models.DecimalField(max_digits=10, decimal_places=3) # pitch in x direction of wells [mm]
	yPitch = models.DecimalField(max_digits=10, decimal_places=3) # pitch in y direction of wells [mm]
	height = models.DecimalField(max_digits=10, decimal_places=3) # height of plate
	width = models.DecimalField(max_digits=10, decimal_places=3) #width of plate
	xPosA1 = models.DecimalField(max_digits=10, decimal_places=3) #x postion of well A1 relative to top left corner of plate
	yPosA1 = models.DecimalField(max_digits=10, decimal_places=3) #y postion of well A1 relative to top left corner of plate
	wells = models.ForeignKey(Well, on_delete=models.CASCADE,related_name='+', null=True, blank=True)
	def __str__(self):
		return self.name


class Library(models.Model):
	name = models.CharField(max_length=30, unique=True)
	description = models.CharField(max_length=300, default='')
	compounds = models.ForeignKey(Compound, related_name='compounds', on_delete=models.CASCADE, null=True, blank=True)
	groups = models.ForeignKey(Group, related_name='libraries', on_delete=models.CASCADE, null=True, blank=True)
	# library --> plate -- > well --> compound
	plates = models.ForeignKey(Plate, related_name='libraries', on_delete=models.CASCADE, null=True, blank=True)

	def __str__(self):
		return self.name

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

# def get_default_source_plate():
# 	plate384, created = Plate.objects.get_or_create(
# 		name="greiner 384 well microplate",
# 		numRows=16,
# 		numCols=24,
# 		maxResVol = 130,
# 		minResVol = 10,
# 		xPitc = 4.5,
# 		yPitch = 4.5,
# 		width = 127.76,
# 		height = 85.48,
# 		xPosA1 = 12.13,
# 		yPosA1 = 8.99,
# 		)
# 	return plate384.id

# def get_default_dest_plate():
# 	subwell1 = SubWell.objects.get_or_create(
# 		idx = 0,
# 		xPos = 4.21, #in mm
# 		yPos = 1.55, #in mm
# 		maxDropVol = 5, #in uL
# 		minDropVol = 1, #in uL
# 		)

# 	subwell2 = SubWell.objects.get_or_create(
# 		idx = 1,
# 		xPos = 4.21, #in mm
# 		yPos = -1.55, #in mm
# 		maxDropVol = 5, #in uL
# 		minDropVol = 1, #in uL
# 		)
# 	plate96, created = Plate.objects.get_or_create(
# 		name="swiss mrc 2-well microplate",
# 		numRows=8,
# 		numCols=12,
# 		maxResVol = 100,
# 		minResVol = 50,
# 		xOffset = 9.03,
# 		yOffset = 9.03,
# 		xLength = 127.5,
# 		yLength = 85.3,
# 		xPosA1 = 14.1,
# 		yPosA1 = 11.04,
# 		)
# 	plate96.subWells.add(subwell1[0])
# 	plate96.subWells.add(subwell2[0])

# 	return plate96.id

class Experiment(models.Model):
	name = models.CharField(max_length=30)
	# need to add more fields probs like library
	library = models.ForeignKey(Library, related_name='experiments',
		on_delete=models.CASCADE, null=True, blank=True)#need to create Library model

	description = models.CharField(max_length=300)
	dateTime = models.DateTimeField(auto_now_add=True)
	protein = models.CharField(max_length=30)
	owner = models.ForeignKey(User, related_name='experiments',on_delete=models.CASCADE)
	
	# sourcePlates = models.ForeignKey(Plate, related_name='source_plate_experiments',
	# 	default=get_default_source_plate, on_delete=models.CASCADE, null=True, blank=True) 
	# destPlates = models.ForeignKey(Plate, related_name='dest_plate_experiments', 
	# 	default=get_default_dest_plate, on_delete=models.CASCADE, null=True, blank=True)
	sourcePlates = models.ForeignKey(Plate, related_name='source_plate_experiments', on_delete=models.CASCADE, null=True, blank=True) 
	destPlates = models.ForeignKey(Plate, related_name='dest_plate_experiments', on_delete=models.CASCADE, null=True, blank=True)

	def __str__(self):
		return self.name