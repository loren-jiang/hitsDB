import datetime as dt
from django.utils import timezone
from random import randint
from django.template.defaultfilters import slugify
import factory
from factory import DjangoModelFactory, lazy_attribute
import faker

faker = faker.Factory.create() 

class GroupFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: 'group_%d' % n)

    class Meta:
        model = 'auth.Group'

class UserFactory(DjangoModelFactory):
    first_name = lazy_attribute(lambda o: faker.first_name())
    last_name = lazy_attribute(lambda o: faker.last_name())
    # username = lazy_attribute(lambda o: slugify(o.first_name + '.' + o.last_name))
    username = factory.Sequence(lambda n: 'user%d' % n)
    email = lazy_attribute(lambda o: o.username + "@example.com")
    is_active = True
    is_staff = False
    is_superuser = False
    password = factory.PostGenerationMethodCall('set_password', 'coygth14')
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            self.groups.add(*extracted)

    @lazy_attribute
    def date_joined(self):
        return timezone.now() - dt.timedelta(days=randint(5, 50))

    last_login = lazy_attribute(lambda o: o.date_joined + dt.timedelta(days=4))

    class Meta:
        model = 'auth.User'

class SuperUserFactory(UserFactory):
    is_staff = True
    is_superuser = True
