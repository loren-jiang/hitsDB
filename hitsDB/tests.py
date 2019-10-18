from django.test import TestCase
from .urls import urlpatterns
from django.contrib.auth.models import User

# # Create your tests here.

class Tests(TestCase):
    def setUp(self):
        self.urls = urlpatterns
        self.client.force_login(User.objects.get_or_create(username='testuser')[0])

    # def test_url_responses(self):
    #     for url in self.urls:
    #         print(url.__dict__) 