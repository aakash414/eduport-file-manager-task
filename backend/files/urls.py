from django.urls import path
from . import views


app_name = 'files'

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    # Core
    path('upload/', views.FileUploadView.as_view(), name='file-upload'),
    path('', views.FileListView.as_view(), name='file-list'),
    path('types/', views.FileTypesView.as_view(), name='file-types'),
    path('<int:pk>/', views.FileDetailView.as_view(), name='file-detail'),
    path('<int:pk>/download/', views.FileDownloadView.as_view(), name='file-download'),
    path('<int:pk>/content-preview/', views.FileContentPreviewView.as_view(), name='file-content-preview'),
    
    # Bulk operations
    path('bulk-upload/', views.BulkFileUploadView.as_view(), name='bulk_file_upload'),
    
]