"""hitsDB URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# hitsDB/urls.py
from django.conf.urls import include, url
from django.urls import path, re_path
from django.contrib import admin
# Add this import
from django.contrib.auth import views as authviews
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from log import views, forms

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'', include('log.urls')),
    re_path(r'', include('experiment.urls')),
    re_path(r'^register/$', views.register, name='register'),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'),
    url(r'^reset_password/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.reset_password, name='reset_password'),
    re_path(r'^user_recover/$',views.user_recover, name='user_recover'),
    re_path(r'^login/$', authviews.LoginView.as_view(template_name= 'login.html', authentication_form= forms.LoginForm)),
    re_path(r'^logout/$', authviews.LogoutView.as_view(next_page= '/login')), 
]
