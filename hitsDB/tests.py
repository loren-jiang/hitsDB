from django.test import TestCase
from .urls import urlpatterns
from django.contrib.auth.models import User

# # Create your tests here.

class Tests(TestCase):
    def setUp(self):
        self.urls = urlpatterns
        self.client.force_login(User.objects.get_or_create(username='testuser')[0])
