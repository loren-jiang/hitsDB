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
from django.conf import settings
from django.conf.urls import include, url
from django.urls import path, re_path
from django.contrib import admin


handler404 = 'experiment.views.handler404'
handler500 = 'experiment.views.handler500'

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'', include('xtal_img.urls')),
    re_path(r'', include('s3.urls')),
    re_path(r'', include('log.urls')),
    re_path(r'', include('experiment.urls')),
    re_path(r'', include('lib.urls')),
   
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),

        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns
