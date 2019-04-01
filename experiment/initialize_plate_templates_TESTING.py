from experiment.models import Plate, Experiment, Library, Well, SubWell, Compound
from django.contrib.auth.models import Group, User

default_source_plate = Plate.create384SourcePlate(name="default_source_plate")
default_source_plate.isTemplate = True 
default_source_plate.save()

default_dest_plate = Plate.create96MRC3DestPlate(name="default_dest_plate")
default_dest_plate.isTemplate = True
default_dest_plate.save()

# default_group = Group.objects.get(id=1)
# test_library = default_group.libraries.create(name="test_library",)

# for i in range(384*2):
# 	test_compound = Compound(nameInternal="test_compound"+str(i), smiles="DMSO"+str(i))
# 	test_compound.save()
# 	test_library.compounds.add(test_compound)


