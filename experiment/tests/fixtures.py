from . import factories
from log.tests.factories import UserFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from s3.models import PrivateFileJSON
import os

# Look for your absolute directory path
absolute_path = os.path.dirname(os.path.abspath(__file__))
path_to_eg_init_data = './test_data/eg_exp_init.json'

def example_init_data():
    """
    """
    with open(path_to_eg_init_data, 'r') as f:
        data = f.read()
        uploaded_file = SimpleUploadedFile(path_to_eg_init_data, bytes(data, 'utf-8'), content_type="application/json")
        return PrivateFileJSON.objects.get_or_create(owner=UserFactory(), local_upload=uploaded_file)[0]

def experiment_with_init_data():
    """
    Experiment with step 1 completed
    """
    exp = factories.ExperimentFactory()
    init_data = example_init_data()
    exp.initData = init_data
    exp.save()
    os.remove("./media/" + str(init_data.local_upload)) 
    return exp

def experiment_with_source_plates():
    """
    Experiment with step 1,2 completed
    """
    exp = experiment_with_init_data()
    with open('./test_data/eg_library_plate_data.csv', newline='') as f:
        exp.createSrcPlatesFromLibFile(2, f)
    return exp

def experiment_with_dest_plates():
    """
    Experiment with step 1,2,3 completed
    """
    exp = experiment_with_source_plates()
    return exp

def experiment_with_matched_soaks():
    """
    Experiment with step 1,2,3 completed
    """
    exp = experiment_with_source_plates()
    exp.matchSrcWellsToSoaks()
    return exp
