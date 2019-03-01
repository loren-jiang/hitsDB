# from django.core.management.base import BaseCommand

# class Command(BaseCommand):
#     help = 'Create library of compounds from .csv file'

#     def add_arguments(self, parser):
#         parser.add_argument('file', nargs='+', type=str)

#     def add_arguments(self, parser):
#         parser.add_argument('name', nargs='+', type=str)

#     def handle(self, *args, **options):
#         # import the relevant model
#         from experiment.models import Compound, Library

        
#         # now do the things that you want with your models here
#         # os.system('export DJANGO_SETTINGS_MODULE=hitsDB.settings')
#         file = options['file']
#         name = options['name']

#         lib, created  = Library.objects.get_or_create(name=name,)
#         lib.groups.add(group)
#         df = pd.read_csv(file, index_col=0)
#         df..ix[:, 0] = df.index
#         df.index = (range(0,len(df.index)))

#         for index, row in df.iterrows():
#             try:
#                 cmpd, created = Compound.objects.get_or_create(
#                     nameInternal=row['nameInternal'],
#                     molWeight=row['molWeight'],
#                     concentration=row['concentration'],
#                     smiles=row['smiles'],
#                 )
#                 lib.compounds.add(cmpd)
#             except: # need to write more exception cases later...
#                 print('PROB with', index)
#         numCmpds = len(lib.compounds.all())
#         numWellsInPlate = plate.numCols * plate.numRows
#         numPlates = -(-numCmpds // numWellsInPlate) #ceiling division

#         for idx in range(len(numPlates)):
#             well = Well()
#             plate =Plate.objects.get_or_create()
#             lib.plates.add(plate, plate_id)


#         for idx, cmpd in enrumerate(lib.compounds.all()):
#             well =Well.objects.get_or_create(stuff, cmpd)
#             if idx >= :
#                 break
