# class CrystalScreen(models.Model):
# 	name = models.CharField(max_length=100,)
# 	manufacturer = models.CharField(max_length=100, default='')
# 	date_dispensed = models.DateField(default=date.today())

qia = ['JCSG I', 'JCSG II', 'JCSG III', 'JCSG IV']

for t in qia:
	CrystalScreen.objects.create(name=t,manufacturer='Qiagen')