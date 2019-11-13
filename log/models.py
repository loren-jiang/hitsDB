from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
# taken from https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
# Profle class serves to 'extend' admin User class in case we want extra fields 
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True, null=True)

    # # returns profile/user projects as django tables 2
    # # argument should be request for pagination to work properly
    # def getProjects(self, excludeCols=[]):
    #     user_proj_qs = self.user.projects.all()
    #     user_collab_proj_qs = self.user.collab_projects.all()
    #     projectsTable = ProjectsTable(data=user_proj_qs.union(user_collab_proj_qs),exclude=excludeCols)
    #     return projectsTable
        
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    # if instance.profile:
    #     instance.profile.save()

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()