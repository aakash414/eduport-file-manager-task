# files/urls.py
from django.urls import path
from . import views


app_name = 'files'

urlpatterns = [
    # Core file operations
    path('upload/', views.FileUploadView.as_view(), name='file-upload'),
    path('', views.FileListView.as_view(), name='file-list'),
    path('<int:pk>/', views.FileDetailView.as_view(), name='file-detail'),
    path('<int:pk>/download/', views.FileDownloadView.as_view(), name='file-download'),
    path('<int:pk>/content-preview/', views.FileContentPreviewView.as_view(), name='file-content-preview'),
    
    # Bulk operations
    path('bulk-upload/', views.BulkFileUploadView.as_view(), name='bulk_file_upload'),
    path('bulk-delete/', views.bulk_delete_files, name='bulk-delete'),
    path('duplicates/', views.duplicate_files_cleanup, name='duplicate-cleanup'),
    
    # Statistics and analytics
    path('stats/', views.file_stats, name='file-stats'),
    
    # Advanced search
    path('advanced-search/', views.advanced_search, name='advanced_search'),
    

]