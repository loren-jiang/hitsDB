from . import factories
from log.tests.factories import UserFactory
from django.core.files.uploadedfile import SimpleUploadedFile

def make_file_models():
    """
    Make .csv, .json files to do basic model validation
    """
    user = UserFactory()
    ret = []
    with open('./test_data/example_init_data.json', 'r') as f:
        data = f.read()
        uploaded_file = SimpleUploadedFile("./test_data/example_init_data.json", bytes(data, 'utf-8'), content_type="application/json")
        ret.append(factories.PrivateFileJSONFactory(owner=user, local_upload=uploaded_file))
        f.close()

    with open('./test_data/example_library_plate_data.csv', 'r') as f:
        data = f.read()
        uploaded_file = SimpleUploadedFile("./test_data/example_library_plate_data.csv", bytes(data, 'utf-8'), content_type="text/csv")
        ret.append(factories.PrivateFileCSVFactory(owner=user, local_upload=uploaded_file))
        f.close()

    return ret
