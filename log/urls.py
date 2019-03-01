# log/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views
from django.contrib.auth.models import User

urlpatterns = [
	re_path(r'^$', views.user_home, name='user_home'),
    re_path(r'^home/$', views.user_home, name='user_home'),
    re_path(r'^manage_user/$', views.manage_user, name='manage_user'), 
    re_path(r'^manage_user/deactivate_user/$', views.deactivate_user, name='deactivate_user')
 
]