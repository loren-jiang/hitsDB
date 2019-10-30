from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, **options):
        # now do the things that you want with your models here
        import pandas as pd
        # os.system('export DJANGO_SETTINGS_MODULE=hitsDB.settings')

        # import the relevant model
        from experiment.models import Compound, Library

        libraryName ='DSI_poised_Enamine'
        lib = Library.objects.get(name=libraryName)

        file = 'C:/Users/loren/Downloads/DSI_poised_Enamine_fragment_library - 2016772(18-10-2017).csv'
        df = pd.read_csv(file, index_col=0)
        df['nameInternal'] = df.index
        df.index = (range(0,len(df.index)))
        #print(df.head())
        #print("\n")
        for index, row in df.iterrows():
            try:
                obj, created = Compound.objects.get_or_create(
                    nameInternal=row['nameInternal'],
                    wellLocation=row['wellLocation'],
                    molWeight=row['molWeight'],
                    chemFormula='temp',
                    zinc_id='temp',
                    concentration=row['concentration'],
                    smiles=row['smiles'],
                )
                lib.compounds.add(obj)
            except: # need to write more exception cases...
                #print('PROB with', index)