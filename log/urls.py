# log/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views, forms
from django.contrib.auth.models import User
from django.contrib.auth import views as authviews

urlpatterns = [
    re_path(r'^manage_user/$', views.manage_user, name='manage_user'), 
    re_path(r'^manage_user/deactivate_user/$', views.deactivate_user, name='deactivate_user'),
    re_path(r'^register/$', views.register, name='register'),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'),
    url(r'^reset_password/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.reset_password, name='reset_password'),
    re_path(r'^user_recover/$',views.user_recover, name='user_recover'),
    re_path(r'^login/$', authviews.LoginView.as_view(template_name= 'log/login.html', authentication_form= forms.LoginForm)),
    re_path(r'^logout/$', authviews.LogoutView.as_view(next_page= '/login')),
 
]