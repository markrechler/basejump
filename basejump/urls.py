from django.conf.urls import patterns, include, url, static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from invdb import views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
#handler404 = views.handler404

urlpatterns = patterns('',
#                       url(r'^logout', 'authenticator.views.logout_user', name='logout_user'),
 #                      url(r'^login', 'authenticator.views.login_user', name='login_user'),
                       url('^', include('authenticator.urls')),
                       url('^invdb/', include('invdb.urls')),
 #   url('^importer/', include('importer.urls')),
 #   url('^kickstart/', include('kickstart.urls')),
                       url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       url(r'^admin/', include(admin.site.urls)),
)
urlpatterns += staticfiles_urlpatterns()

