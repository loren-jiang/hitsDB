# xtal_img/urls.py
from django.conf.urls import url
from django.urls import path, re_path
from . import views

from django.conf import settings
from django.views.static import serve

urlpatterns = [
    re_path(r'^plate/(?P<pk_plate>\d+)/drop_images_upload/$', views.DropImagesUploadView.as_view(), name='drop_images_upload'),
    re_path(r'^image-gui/(?P<user_id>\d+)/(?P<plate_id>\d+)/(?P<file_name>.*)/$',views.DropImageViewGUI, name='imageGUI'),
    re_path(r'^image-gui/upload_drop_image/$',views.upload_drop_image, name='upload_drop_image'),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]