from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.http import HttpResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('files/', include('files.urls')),
    path('health/', lambda request: HttpResponse('OK')),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'files.views.custom_404'
handler500 = 'files.views.custom_500'
