from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.contrib import admin
from authenticator import views
admin.autodiscover()

#handler404 = views.handler404

urlpatterns = patterns('authenticator.views',
                       url(r'^logout', 'logout_user', name='logout_user'),
                       url(r'^login', 'login_user', name='login_user'),
                       url(r'^$', 'index', name='index'),
)

urlpatterns += staticfiles_urlpatterns()

