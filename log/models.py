from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver

# Profle class serves to 'extend' admin User class in case we want extra fields 
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, null=True)
    primary_group = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True)
        
@receiver(post_save, sender=User)
def process_user_post_save(sender, instance, created, **kwargs):
    def create_user_profile(instance, created):
        if created:
            Profile.objects.create(user=instance)

    def save_user_profile(instance):
        profile = instance.profile
        if profile.primary_group and not(profile.primary_group in instance.groups.all()):
            instance.groups.add(profile.primary_group)
        profile.save()

    create_user_profile(instance, created)
    save_user_profile(instance)