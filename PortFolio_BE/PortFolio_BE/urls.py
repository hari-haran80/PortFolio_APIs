from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('Auth/', include('Apps.Authentication_App.urls')),
    path('User/', include('Apps.Profile_App.urls')),
    path('Resume/', include('Apps.Resume_app.urls')),
    path('My-Own/', include('Apps.Projects_app.urls')),
    path('User/', include('Apps.Review_app.urls')),
    path('', include('Apps.Skills_app.urls')),
    path('User/', include('Apps.Theme_app.urls')),
    path('Contact/', include('Apps.Contact_App.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)