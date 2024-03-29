from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from api import routers as api_routers
from views import urls as base_urls
from apps.person.views import urls as person_urls
from apps.resume.views import urls as resume_urls
from apps.helpdesk.views import urls as helpdesk_urls

urlpatterns = [
    path('', include(base_urls)),
    path('api/', include(api_routers)),
    path('person/', include(person_urls)),
    path('resume/', include(resume_urls)),
    path('helpdesk/', include(helpdesk_urls)),
    path('admin/', admin.site.urls),
]

urlpatterns += static(settings.MEDIA_URL,
                      document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL,
                      document_root=settings.STATIC_ROOT)

# Remove admin sidebar nav sidebar
# https://docs.djangoproject.com/en/3.1/ref/contrib/admin/#django.contrib.admin.AdminSite.enable_nav_sidebar
admin.site.enable_nav_sidebar = False

if settings.DEBUG and not settings.IS_UNIX:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
