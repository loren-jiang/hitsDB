from . import factories
from log.tests.factories import UserFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from s3.models import PrivateFileJSON

def make_example_init_data():
    """
    """
    with open('./test_data/example_init_data.json', 'r') as f:
        data = f.read()
        uploaded_file = SimpleUploadedFile("./test_data/example_init_data.json", bytes(data, 'utf-8'), content_type="application/json")
        return PrivateFileJSON.objects.get_or_create(owner=UserFactory(), local_upload=uploaded_file)[0]

