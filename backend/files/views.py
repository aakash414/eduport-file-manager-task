# files/views.py
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import CursorPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum, F, Window
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.contrib.auth.models import User
from datetime import timedelta
import logging
import os
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import FileUpload
from .serializers import (
    BulkFileUploadSerializer,
    FileUploadSerializer, FileListSerializer, FileDetailSerializer,
    FileSearchSerializer, FileStatsSerializer,
    BulkDeleteSerializer
)

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class BulkFileUploadView(generics.CreateAPIView):
    """
    API endpoint for bulk file uploads.

    This view handles the upload of multiple files in a single request.
    It ensures that the entire upload process is atomic, meaning that if one
    file fails to upload, all other uploads in the same batch are rolled back.

    Key Features:
    - **Transactional Integrity**: Uses `transaction.atomic()` to ensure all-or-nothing uploads.
    - **Detailed Reporting**: Returns a detailed report of successful and failed uploads.
    - **Security**: Inherits permission classes to ensure only authenticated users can upload.
    - **Validation**: Leverages `BulkFileUploadSerializer` for robust validation of each file.
    """
    serializer_class = BulkFileUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        files = serializer.validated_data['files']
        successful_uploads = []
        failed_uploads = []

        try:
            with transaction.atomic():
                for uploaded_file in files:
                    try:
                        # Create a FileUpload instance for each file.
                        file_upload = FileUpload.objects.create(
                            uploaded_by=request.user,
                            file=uploaded_file,
                            original_filename=uploaded_file.name,
                            file_size=uploaded_file.size,
                            file_type=uploaded_file.content_type,
                        )
                        successful_uploads.append({
                            'filename': uploaded_file.name,
                            'file_id': file_upload.id,
                            'message': 'Upload successful.'
                        })
                    except Exception as e:
                        # If a single file fails, record the error and re-raise to trigger a rollback.
                        failed_uploads.append({
                            'filename': uploaded_file.name,
                            'error': str(e)
                        })
                        # This exception will cause the transaction to be rolled back.
                        raise

        except Exception as e:
            # This block catches the exception from the transaction, logs it, and returns a failure response.
            logger.error(f"Bulk upload failed and was rolled back: {str(e)}")
            return Response({
                'error': 'Bulk upload failed. The entire transaction has been rolled back.',
                'details': str(e),
                'failed_files': failed_uploads
            }, status=status.HTTP_400_BAD_REQUEST)

        # If the transaction completes successfully, return a success response.
        return Response({
            'message': 'Bulk upload completed.',
            'successful_uploads': successful_uploads,
            'failed_uploads': failed_uploads  # This will be empty if all files succeeded.
        }, status=status.HTTP_201_CREATED)





class FileUploadView(generics.CreateAPIView):
    """
    API endpoint for file uploads.
    
    Interview Talking Points:
    - Multipart file handling
    - Security validations
    - Duplicate detection
    - Error handling for edge cases
    """
    serializer_class = FileUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        """
        Custom create logic with logging and analytics.
        """
        try:
            # Save the file with current user
            file_upload = serializer.save(uploaded_by=self.request.user)
            
            # Log successful upload
            logger.info(
                f"File uploaded successfully: {file_upload.original_filename} "
                f"by user {self.request.user.username}"
            )
            
            # Check for duplicates and log if found
            if FileUpload.objects.filter(file_hash=file_upload.file_hash).count() > 1:
                logger.warning(
                    f"Duplicate file uploaded: {file_upload.file_hash} "
                    f"by user {self.request.user.username}"
                )
            
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            raise
    
    def create(self, request, *args, **kwargs):
        """
        Enhanced create with better error handling.
        """
        try:
            response = super().create(request, *args, **kwargs)
            
            # Add success message
            response.data['message'] = 'File uploaded successfully'
            
            return response
            
        except Exception as e:
            logger.error(f"File upload error: {str(e)}")
            return Response(
                {'error': 'File upload failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class FileCursorPagination(CursorPagination):
    ordering = '-upload_date'
    page_size = 10


class FileListView(generics.ListAPIView):
    """
    API endpoint for listing user's files with search and filtering.
    
    This view is optimized for performance with:
    - **Cursor Pagination**: For efficient navigation of large datasets.
    - **Caching**: Caches responses to reduce database load.
    - **Optimized Queries**: Uses `select_related` to prevent N+1 problems.
    - **Advanced Filtering**: Supports filtering by name, type, date, and size.
    """
    serializer_class = FileListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = FileCursorPagination
    
    @method_decorator(cache_page(60 * 5)) # Cache results for 5 minutes
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        """
        Builds a filtered and optimized queryset based on query parameters.
        """
        queryset = FileUpload.objects.filter(
            uploaded_by=self.request.user
        ).select_related('uploaded_by')

        # Search functionality (case-insensitive)
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(original_filename__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # File type filtering for multiple values
        file_types = self.request.query_params.getlist('file_type') or self.request.query_params.getlist('file_type[]')
        if file_types:
            # file_type in the DB is now standardized to a lowercase extension.
            queryset = queryset.filter(file_type__in=[ft.lower() for ft in file_types])
        
        # Date range filtering
        uploaded_after = self.request.query_params.get('uploaded_after', None)
        if uploaded_after:
            queryset = queryset.filter(upload_date__gte=uploaded_after)
        
        uploaded_before = self.request.query_params.get('uploaded_before', None)
        if uploaded_before:
            queryset = queryset.filter(upload_date__lte=uploaded_before)
        
        # Size filtering (in bytes)
        min_size = self.request.query_params.get('min_size', None)
        if min_size:
            queryset = queryset.filter(file_size__gte=int(min_size))
        
        max_size = self.request.query_params.get('max_size', None)
        if max_size:
            queryset = queryset.filter(file_size__lte=int(max_size))
        
        # Ordering - cursor pagination requires a consistent ordering
        ordering = self.request.query_params.get('ordering', '-upload_date')
        valid_ordering_fields = [
            'upload_date', '-upload_date', 
            'original_filename', '-original_filename', 
            'file_size', '-file_size'
        ]
        if ordering in valid_ordering_fields:
            queryset = queryset.order_by(ordering)
        else:
            # Default ordering for cursor pagination
            queryset = queryset.order_by('-upload_date')
        
        return queryset


class FileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for file detail operations.
    
    Interview Talking Points:
    - Permission-based access control
    - Atomic updates
    - Soft deletion considerations
    - Access logging
    """
    serializer_class = FileDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Ensure users can only access their own files."""
        return FileUpload.objects.filter(uploaded_by=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve file with access logging.
        """
        instance = self.get_object()
        
        # Update last accessed timestamp
        instance.mark_accessed()
        
        # Log file access
        logger.info(
            f"File accessed: {instance.original_filename} "
            f"by user {request.user.username}"
        )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """
        Update file with validation.
        """
        try:
            response = super().update(request, *args, **kwargs)
            logger.info(
                f"File updated: {self.get_object().original_filename} "
                f"by user {request.user.username}"
            )
            return response
        except Exception as e:
            logger.error(f"File update failed: {str(e)}")
            return Response(
                {'error': 'File update failed.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete file with logging.
        """
        instance = self.get_object()
        filename = instance.original_filename
        
        try:
            # Delete the file
            response = super().destroy(request, *args, **kwargs)
            
            logger.info(
                f"File deleted: {filename} by user {request.user.username}"
            )
            
            return Response(
                {'message': f'File "{filename}" deleted successfully.'},
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Exception as e:
            logger.error(f"File deletion failed: {str(e)}")
            return Response(
                {'error': 'File deletion failed.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FileDownloadView(generics.RetrieveAPIView):
    """
    API endpoint for file downloads.
    
    Interview Talking Points:
    - Secure file serving
    - Access control
    - Download analytics
    - Performance considerations
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Ensure users can only download their own files."""
        return FileUpload.objects.filter(uploaded_by=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Serve file for download with proper headers.
        """
        try:
            file_upload = self.get_object()
            
            # Update access tracking
            file_upload.mark_accessed()
            
            # Log download
            logger.info(
                f"File downloaded: {file_upload.original_filename} "
                f"by user {request.user.username}"
            )
            
            # Serve file
            response = HttpResponse(
                file_upload.file.read(),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{file_upload.original_filename}"'
            response['Content-Length'] = file_upload.file_size
            
            return response
            
        except Exception as e:
            logger.error(f"File download failed: {str(e)}")
            raise Http404("File not found or access denied.")

class FileDetailedInfoView(APIView):
    """
    Retrieve comprehensive information about a specific file.
    Includes metadata, file info, access tracking, and system information.
    Different from FileDetailView which handles CRUD operations.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            file_obj = get_object_or_404(
                FileUpload.objects.select_related('uploaded_by'),
                id=pk,
                uploaded_by=request.user
            )

            # Update view count and last accessed timestamp atomically
            FileUpload.objects.filter(id=pk).update(
                view_count=F('view_count') + 1,
                last_accessed=timezone.now()
            )

            # Refresh the object from the database to get the updated values
            file_obj.refresh_from_db()

            # Get file system info safely
            file_path = file_obj.file.path
            file_stats = os.stat(file_path) if os.path.exists(file_path) else None

            # Prepare detailed response payload
            data = {
                'id': file_obj.id,
                'original_filename': file_obj.original_filename,
                'file_size': file_obj.file_size,
                'file_type': file_obj.file_type,
                'mime_type': file_obj.mime_type,
                'file_hash': file_obj.file_hash,
                'upload_date': file_obj.upload_date,
                'last_modified': file_obj.last_modified,
                'last_accessed': file_obj.last_accessed,
                'view_count': file_obj.view_count,
                'file_url': request.build_absolute_uri(file_obj.file.url),
                'user': {
                    'id': file_obj.uploaded_by.id,
                    'username': file_obj.uploaded_by.username,
                },
                'is_duplicate': file_obj.is_duplicate(),
                'duplicate_of': file_obj.duplicate_of.id if file_obj.duplicate_of else None,
                'file_exists': os.path.exists(file_path) if file_path else False,
                'system_info': {
                    'created_time': file_stats.st_ctime if file_stats else None,
                    'modified_time': file_stats.st_mtime if file_stats else None,
                    'access_time': file_stats.st_atime if file_stats else None,
                    'size_on_disk': file_stats.st_size if file_stats else None,
                } if file_stats else None,
                'permissions': {
                    'can_download': True,
                    'can_delete': True,

                }
            }
            return Response(data, status=status.HTTP_200_OK)

        except FileUpload.DoesNotExist:
            logger.warning(f"File not found for pk={pk} and user={request.user.username}")
            return Response({'error': 'File not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Error retrieving file details for pk={pk}: {str(e)}", exc_info=True)
            return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FileContentPreviewView(APIView):
    """
    Generate and stream preview content for supported file types.
    This view returns the raw file content (or a truncated version for text)
    to be rendered by the browser in the frontend modal.
    """
    permission_classes = [IsAuthenticated]

    # Define previewable types by extension as a fallback
    PREVIEWABLE_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']
    PREVIEWABLE_VIDEO_EXTENSIONS = ['mp4', 'webm', 'ogg']
    PREVIEWABLE_AUDIO_EXTENSIONS = ['mp3', 'wav', 'ogg']
    PREVIEWABLE_PDF_EXTENSIONS = ['pdf']
    PREVIEWABLE_TEXT_EXTENSIONS = ['txt', 'md', 'csv', 'log', 'json', 'xml', 'html', 'css', 'js', 'py', 'java', 'cpp', 'c', 'h']
    
    # Also define by MIME type for when it's available
    PREVIEWABLE_MIME_PREFIXES = ['image/', 'video/', 'audio/']
    PREVIEWABLE_MIME_TYPES = ['application/pdf', 'text/plain']

    MAX_PREVIEW_SIZE = 10 * 1024 * 1024  # 10MB max for preview
    MAX_TEXT_PREVIEW_CHARS = 50000  # 50,000 characters for text preview

    def get(self, request, pk):
        try:
            # 1. Fetch the file object, ensuring ownership
            file_obj = get_object_or_404(
                FileUpload,
                id=pk,
                uploaded_by=request.user
            )

            # 2. Check if file exists on disk
            file_path = file_obj.file.path
            if not os.path.exists(file_path):
                logger.error(f"File not found on disk for pk={pk}: {file_path}")
                return Response({'error': 'File not found on disk'}, status=status.HTTP_404_NOT_FOUND)

            # 3. Check if file size is within preview limits
            if file_obj.file_size > self.MAX_PREVIEW_SIZE:
                logger.warning(f"File too large for preview for pk={pk}, size={file_obj.file_size}")
                return Response({'error': 'File is too large for preview'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

            # 4. Determine if the file type is previewable (more robustly)
            file_ext = file_obj.original_filename.split('.')[-1].lower() if '.' in file_obj.original_filename else ''
            mime_type = file_obj.mime_type.lower() if file_obj.mime_type else ''

            is_previewable = False
            # First, try to use the MIME type if it exists and is recognized
            if mime_type:
                if any(mime_type.startswith(prefix) for prefix in self.PREVIEWABLE_MIME_PREFIXES):
                    is_previewable = True
                elif mime_type in self.PREVIEWABLE_MIME_TYPES:
                    is_previewable = True
            
            # If MIME type check fails or mime_type is empty, fall back to extension
            if not is_previewable:
                if file_ext in self.PREVIEWABLE_IMAGE_EXTENSIONS:
                    is_previewable = True
                    if not mime_type: mime_type = f'image/{file_ext}'
                elif file_ext in self.PREVIEWABLE_PDF_EXTENSIONS:
                    is_previewable = True
                    if not mime_type: mime_type = 'application/pdf'
                elif file_ext in self.PREVIEWABLE_TEXT_EXTENSIONS:
                    is_previewable = True
                    # Always force text/plain for security, regardless of original mime type
                    mime_type = 'text/plain'

            if not is_previewable:
                logger.warning(f"Unsupported preview file type for pk={pk}, mime='{mime_type}', ext='{file_ext}'")
                return Response({'error': 'This file type is not supported for preview'}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

            # 5. Read content and serve the file
            if mime_type == 'text/plain':
                # For text files, return a truncated part
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(self.MAX_TEXT_PREVIEW_CHARS)
            else:
                # For binary files (image, pdf, etc.), return the whole file
                with open(file_path, 'rb') as f:
                    content = f.read()

            # 6. Create and return the HttpResponse
            response = HttpResponse(content, content_type=mime_type)
            response['Content-Disposition'] = f'inline; filename=\"{file_obj.original_filename}\"' 
            return response

        except Http404:
            return Response({'error': 'File not found or you do not have permission to view it'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error generating file preview for pk={pk}: {str(e)}", exc_info=True)
            return Response({'error': 'An unexpected error occurred while generating the preview.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bulk_delete_files(request):
    """
    API endpoint for bulk file deletion.
    
    Interview Talking Points:
    - Bulk operations for better UX
    - Transaction management
    - Error handling for partial failures
    - Security considerations
    """
    serializer = BulkDeleteSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    file_ids = serializer.validated_data['file_ids']
    
    try:
        with transaction.atomic():
            # Get files to delete
            files_to_delete = FileUpload.objects.filter(
                id__in=file_ids,
                uploaded_by=request.user
            )
            
            deleted_count = files_to_delete.count()
            filenames = list(files_to_delete.values_list('original_filename', flat=True))
            
            # Delete files
            files_to_delete.delete()
            
            # Log bulk deletion
            logger.info(
                f"Bulk deletion: {deleted_count} files deleted "
                f"by user {request.user.username}"
            )
            
            return Response({
                'message': f'Successfully deleted {deleted_count} files.',
                'deleted_files': filenames
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Bulk deletion failed: {str(e)}")
        return Response(
            {'error': 'Bulk deletion failed. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def file_stats(request):
    """
    API endpoint for file statistics.
    
    Interview Talking Points:
    - Analytics and reporting
    - Efficient aggregation queries
    - Dashboard data provision
    """
    try:
        user_files = FileUpload.objects.filter(uploaded_by=request.user)
        
        # Basic statistics
        total_files = user_files.count()
        total_size = user_files.aggregate(total=Sum('file_size'))['total'] or 0
        
        # File type statistics
        file_types = list(user_files.values('file_type').annotate(
            count=Count('id'),
            size=Sum('file_size')
        ).order_by('-count'))
        
        # Recent uploads (last 7 days)
        recent_date = timezone.now() - timedelta(days=7)
        recent_uploads = user_files.filter(upload_date__gte=recent_date).count()
        
        # Format file size
        def format_size(size_bytes):
            if size_bytes < 1024:
                return f"{size_bytes} bytes"
            elif size_bytes < 1024**2:
                return f"{size_bytes/1024:.1f} KB"
            elif size_bytes < 1024**3:
                return f"{size_bytes/(1024**2):.1f} MB"
            else:
                return f"{size_bytes/(1024**3):.1f} GB"
        
        stats_data = {
            'total_files': total_files,
            'total_size': total_size,
            'total_size_display': format_size(total_size),
            'file_types': file_types,
            'recent_uploads': recent_uploads
        }
        
        serializer = FileStatsSerializer(stats_data)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"File stats retrieval failed: {str(e)}")
        return Response(
            {'error': 'Failed to retrieve file statistics.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



        return Response({
            'file_id': file_upload.id,
            'filename': file_upload.original_filename,
            'file_size': file_upload.file_size,
            'file_size_display': share_link._format_file_size(file_upload.file_size),
            'file_type': file_upload.file_type,
            'upload_date': file_upload.upload_date,
            'description': file_upload.description,
            'download_url': f'/api/files/shared/{token}/download/',
            'expires_at': share_link.expires_at,
            'access_count': share_link.access_count
        })
        
    except FileShareLink.DoesNotExist:
        logger.warning(f"Invalid share link accessed: {token}")
        return Response(
            {'error': 'Invalid share link.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Shared file access failed: {str(e)}")
        return Response(
            {'error': 'Failed to access shared file.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def shared_file_download(request, token):
    """
    API endpoint for downloading shared files.
    
    Interview Talking Points:
    - Secure file serving without authentication
    - Token validation
    - Access tracking
    - Performance considerations for public access
    """
    try:
        share_link = get_object_or_404(FileShareLink, token=token)
        
        # Check if link is expired
        if share_link.is_expired():
            logger.warning(f"Expired share link download attempted: {token}")
            return Response(
                {'error': 'This share link has expired.'},
                status=status.HTTP_410_GONE
            )
        
        # Check if link is still active
        if not share_link.is_active:
            logger.warning(f"Inactive share link download attempted: {token}")
            return Response(
                {'error': 'This share link is no longer active.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update access count
        share_link.increment_access_count()
        
        # Log download
        file_upload = share_link.file_upload
        logger.info(
            f"Shared file downloaded: {file_upload.original_filename} "
            f"via token {token} from IP {request.META.get('REMOTE_ADDR')}"
        )
        
        # Serve file
        response = HttpResponse(
            file_upload.file.read(),
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{file_upload.original_filename}"'
        response['Content-Length'] = file_upload.file_size
        
        return response
        
    except FileShareLink.DoesNotExist:
        logger.warning(f"Invalid share link download attempted: {token}")
        raise Http404("Invalid share link.")
    except Exception as e:
        logger.error(f"Shared file download failed: {str(e)}")
        raise Http404("File not found or access denied.")


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def duplicate_files_cleanup(request):
    """
    API endpoint for cleaning up duplicate files.
    
    Interview Talking Points:
    - Database optimization
    - Bulk operations
    - User choice in cleanup
    - Storage management
    """
    try:
        # Find duplicate files for the user
        user_files = FileUpload.objects.filter(uploaded_by=request.user)
        
        # Group files by hash to find duplicates
        duplicate_groups = {}
        for file_upload in user_files:
            if file_upload.file_hash in duplicate_groups:
                duplicate_groups[file_upload.file_hash].append(file_upload)
            else:
                duplicate_groups[file_upload.file_hash] = [file_upload]
        
        # Filter to only groups with duplicates
        actual_duplicates = {
            hash_val: files for hash_val, files in duplicate_groups.items()
            if len(files) > 1
        }
        
        if not actual_duplicates:
            return Response({
                'message': 'No duplicate files found.',
                'duplicates': []
            })
        
        # Format duplicate information
        duplicate_info = []
        for hash_val, files in actual_duplicates.items():
            # Sort by upload date (keep oldest)
            files.sort(key=lambda x: x.upload_date)
            original = files[0]
            duplicates = files[1:]
            
            duplicate_info.append({
                'file_hash': hash_val,
                'original_file': {
                    'id': original.id,
                    'filename': original.original_filename,
                    'upload_date': original.upload_date,
                },
                'duplicate_files': [
                    {
                        'id': dup.id,
                        'filename': dup.original_filename,
                        'upload_date': dup.upload_date,
                    } for dup in duplicates
                ],
                'potential_savings': sum(dup.file_size for dup in duplicates)
            })
        
        # If cleanup is requested
        if request.data.get('cleanup', False):
            total_deleted = 0
            total_saved_space = 0
            
            with transaction.atomic():
                for hash_val, files in actual_duplicates.items():
                    files.sort(key=lambda x: x.upload_date)
                    duplicates_to_delete = files[1:]  # Keep oldest
                    
                    for dup in duplicates_to_delete:
                        total_saved_space += dup.file_size
                        dup.delete()
                        total_deleted += 1
            
            logger.info(
                f"Duplicate cleanup: {total_deleted} files deleted, "
                f"{total_saved_space} bytes saved by user {request.user.username}"
            )
            
            return Response({
                'message': f'Cleanup completed. {total_deleted} duplicate files deleted.',
                'files_deleted': total_deleted,
                'space_saved': total_saved_space,
                'space_saved_display': FileListView()._format_file_size(total_saved_space)
            })
        
        # Return duplicate information for user review
        return Response({
            'message': f'Found {len(actual_duplicates)} sets of duplicate files.',
            'duplicates': duplicate_info,
            'total_potential_savings': sum(
                info['potential_savings'] for info in duplicate_info
            )
        })
        
    except Exception as e:
        logger.error(f"Duplicate cleanup failed: {str(e)}")
        return Response(
            {'error': 'Failed to process duplicate files.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def advanced_search(request):
    """
    API endpoint for advanced file search.
    
    Interview Talking Points:
    - Complex query building
    - Search optimization
    - Full-text search capabilities
    - Performance with large datasets
    """
    try:
        queryset = FileUpload.objects.filter(uploaded_by=request.user)
        
        # Build complex search query
        search_params = request.query_params
        
        # Text search across multiple fields
        if search_params.get('q'):
            search_term = search_params.get('q')
            queryset = queryset.filter(
                Q(original_filename__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(file_type__icontains=search_term)
            )
        
        # Date range search
        if search_params.get('date_from'):
            queryset = queryset.filter(upload_date__gte=search_params.get('date_from'))
        
        if search_params.get('date_to'):
            queryset = queryset.filter(upload_date__lte=search_params.get('date_to'))
        
        # Size range search
        try:
            if search_params.get('size_min'):
                size_min_kb = int(search_params.get('size_min'))
                queryset = queryset.filter(file_size__gte=size_min_kb * 1024)
            
            if search_params.get('size_max'):
                size_max_kb = int(search_params.get('size_max'))
                queryset = queryset.filter(file_size__lte=size_max_kb * 1024)
        except (ValueError, TypeError):
            # Ignore if size params are not valid integers
            pass
        # File type filter
        if search_params.get('file_types'):
            file_types = search_params.get('file_types').split(',')
            queryset = queryset.filter(file_type__in=file_types)
        
        # Recently accessed filter
        if search_params.get('recently_accessed'):
            days = int(search_params.get('recently_accessed', 7))
            recent_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(last_accessed__gte=recent_date)
        
        # Sort results
        sort_by = search_params.get('sort', '-upload_date')
        if sort_by in ['upload_date', '-upload_date', 'original_filename', 
                      '-original_filename', 'file_size', '-file_size', 
                      'last_accessed', '-last_accessed']:
            queryset = queryset.order_by(sort_by)
        
        # Apply pagination
        paginator = FileUploadPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        # Serialize results
        serializer = FileListSerializer(paginated_queryset, many=True)
        
        return paginator.get_paginated_response(serializer.data)
        
    except Exception as e:
        logger.error(f"Advanced search failed: {str(e)}")
        return Response(
            {'error': 'Search failed. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def file_quick_metadata(request, file_id):
    """
    Get lightweight metadata for a file without updating view tracking.
    Optimized for quick information retrieval and UI tooltips.
    Complements your existing FileDetailView for different use cases.
    """
    try:
        file_obj = get_object_or_404(
            FileUpload,
            id=file_id,
            user=request.user
        )
        
        # Basic metadata without updating view count
        metadata = {
            'id': file_obj.id,
            'filename': file_obj.filename,
            'original_filename': file_obj.original_filename,
            'file_size': file_obj.file_size,
            'file_type': file_obj.file_type,
            'mime_type': file_obj.mime_type,
            'upload_date': file_obj.upload_date,
            'last_modified': file_obj.last_modified,
            'view_count': file_obj.view_count,
            'is_duplicate': file_obj.is_duplicate,
            'file_extension': file_obj.filename.split('.')[-1].lower() if '.' in file_obj.filename else '',
            'size_formatted': format_file_size(file_obj.file_size),
        }
        
        return Response(metadata, status=status.HTTP_200_OK)
        
    except FileUpload.DoesNotExist:
        return Response(
            {'error': 'File not found'},
            status=status.HTTP_404_NOT_FOUND
        )


def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

from django.http import JsonResponse

def custom_404(request, exception=None):
    return JsonResponse({
        'status_code': 404,
        'error': 'The resource was not found'
    }, status=404)

def custom_500(request):
    return JsonResponse({
        'status_code': 500,
        'error': 'Internal server error'
    }, status=500)
