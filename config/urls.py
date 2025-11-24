from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Pastebin API",
        default_version='v1',
        description="API documentation",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('users/', include('accounts.urls')),
    path('posts/', include('blogs.urls')),
    path('notifications/', include('notifications.urls')),

    # DRF-YASG Swagger UI and Redoc
    re_path(r'^$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Favicon redirect
urlpatterns += [
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico'))
]

# Serve media files in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
