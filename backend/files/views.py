# files/views.py
import hashlib
import json
import logging
import os
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.pagination import CursorPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FileUpload
from .serializers import (
    BulkFileUploadSerializer,
    FileUploadSerializer, FileListSerializer, FileDetailSerializer,
    FileSearchSerializer, FileStatsSerializer,
    BulkDeleteSerializer
)


logger = logging.getLogger(__name__)


def invalidate_user_file_cache(user):
    """Invalidates all file-related caches for a given user."""
    cache.incr(f'user_{user.id}_file_list_version')
    cache.delete(f'user_{user.id}_file_types')
    logger.info(f"Invalidated file cache for user {user.id}")


@method_decorator(csrf_exempt, name='dispatch')
class BulkFileUploadView(generics.CreateAPIView):
    serializer_class = BulkFileUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        files = serializer.validated_data['files']
        atomic_mode = request.query_params.get('atomic', 'false').lower() == 'true'
        
        if atomic_mode:
            response = self._atomic_upload(request, files)
        else:
            response = self._partial_upload(request, files)
        
        if response.status_code in [status.HTTP_201_CREATED, status.HTTP_207_MULTI_STATUS]:
            invalidate_user_file_cache(request.user)
            
        return response

    def _atomic_upload(self, request, files):
        successful_uploads = []
        failed_uploads = []
        
        for uploaded_file in files:
            try:
                file_hash = FileUpload.calculate_file_hash_from_file(uploaded_file)
                if FileUpload.objects.filter(file_hash=file_hash).exists():
                    failed_uploads.append({'filename': uploaded_file.name, 'error': f"Duplicate file detected: {uploaded_file.name}"})
                uploaded_file.seek(0)
            except Exception as e:
                failed_uploads.append({'filename': uploaded_file.name, 'error': str(e)})
        
        if failed_uploads:
            return Response({'error': 'Atomic bulk upload failed validation.', 'failed_uploads': failed_uploads}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                for uploaded_file in files:
                    file_hash = FileUpload.calculate_file_hash_from_file(uploaded_file)
                    uploaded_file.seek(0)
                    file_upload = FileUpload.objects.create(uploaded_by=request.user, file=uploaded_file, original_filename=uploaded_file.name, file_size=uploaded_file.size, file_type=uploaded_file.content_type, file_hash=file_hash)
                    successful_uploads.append({'filename': uploaded_file.name, 'file_id': file_upload.id, 'message': 'Upload successful.'})
            return Response({'message': 'Atomic bulk upload completed successfully.', 'successful_uploads': successful_uploads}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Atomic bulk upload failed during save: {str(e)}")
            return Response({'error': 'A critical error occurred during the save process.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _partial_upload(self, request, files):
        successful_uploads = []
        failed_uploads = []
        
        for uploaded_file in files:
            try:
                file_hash = FileUpload.calculate_file_hash_from_file(uploaded_file)
                uploaded_file.seek(0)
                if FileUpload.objects.filter(file_hash=file_hash).exists():
                    failed_uploads.append({'filename': uploaded_file.name, 'error': f"Duplicate file detected: {uploaded_file.name}"})
                    continue
                file_upload = FileUpload.objects.create(uploaded_by=request.user, file=uploaded_file, original_filename=uploaded_file.name, file_size=uploaded_file.size, file_type=uploaded_file.content_type, file_hash=file_hash)
                successful_uploads.append({'filename': uploaded_file.name, 'file_id': file_upload.id, 'message': 'Upload successful.'})
            except (IntegrityError, ValidationError) as e:
                failed_uploads.append({'filename': uploaded_file.name, 'error': str(e)})
            except Exception as e:
                logger.error(f"Unexpected error uploading {uploaded_file.name}: {str(e)}")
                failed_uploads.append({'filename': uploaded_file.name, 'error': f"Unexpected error: {str(e)}"})
        
        if successful_uploads and not failed_uploads:
            status_code = status.HTTP_201_CREATED
            message = 'Bulk upload completed successfully.'
        elif successful_uploads and failed_uploads:
            status_code = status.HTTP_207_MULTI_STATUS
            message = 'Bulk upload completed with some failures.'
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            message = 'Bulk upload failed. No files were uploaded.'
        
        return Response({'message': message, 'successful_uploads': successful_uploads, 'failed_uploads': failed_uploads}, status=status_code)


class FileUploadView(generics.CreateAPIView):
    serializer_class = FileUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except IntegrityError:
            uploaded_file = request.data.get('file')
            if not uploaded_file:
                return Response({"error": "File data not provided."}, status=status.HTTP_400_BAD_REQUEST)
            file_hash = FileUpload.calculate_file_hash_from_file(uploaded_file)
            existing_file = FileUpload.objects.filter(file_hash=file_hash).first()
            if existing_file:
                message = "You have already uploaded this exact file." if existing_file.uploaded_by == request.user else "A file with the same content already exists."
                return Response({"error": "Duplicate file detected.", "detail": message, "existing_file_id": existing_file.id}, status=status.HTTP_409_CONFLICT)
            logger.error("An unexpected IntegrityError occurred during file upload.", exc_info=True)
            return Response({"error": "A database conflict occurred."}, status=status.HTTP_409_CONFLICT)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
        invalidate_user_file_cache(self.request.user)


class FileCursorPagination(CursorPagination):
    ordering = '-upload_date'
    page_size = 10


class FileTypesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        cache_key = f'user_{request.user.id}_file_types'
        cached_types = cache.get(cache_key)
        if cached_types is not None:
            return Response(cached_types)

        file_types = FileUpload.objects.filter(uploaded_by=request.user).values_list('file_type', flat=True).distinct().order_by('file_type')
        unique_types = sorted([ft for ft in file_types if ft])
        
        cache.set(cache_key, unique_types, 60 * 60) # Cache for 1 hour
        return Response(unique_types)


class FileListView(generics.ListAPIView):
    serializer_class = FileListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = FileCursorPagination

    def list(self, request, *args, **kwargs):
        version = cache.get(f'user_{request.user.id}_file_list_version', 1)
        query_params = request.query_params.dict()
        sorted_params = json.dumps(sorted(query_params.items()))
        params_hash = hashlib.md5(sorted_params.encode('utf-8')).hexdigest()
        cache_key = f'user_{request.user.id}_file_list_v{version}_{params_hash}'

        cached_response = cache.get(cache_key)
        if cached_response:
            logger.info(f"Serving file list from cache for user {request.user.id}")
            return Response(cached_response)

        logger.info(f"Generating new file list for user {request.user.id}")
        response = super().list(request, *args, **kwargs)
        
        if response.status_code == 200:
            cache.set(cache_key, response.data, 60 * 15) # Cache for 15 minutes
        
        return response

    def get_queryset(self):
        queryset = FileUpload.objects.filter(uploaded_by=self.request.user).select_related('uploaded_by')
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(Q(original_filename__icontains=search_query) | Q(description__icontains=search_query))
        
        file_types = self.request.query_params.getlist('file_type') or self.request.query_params.getlist('file_type[]')
        if file_types:
            queryset = queryset.filter(file_type__in=[ft.lower() for ft in file_types])
        
        uploaded_after = self.request.query_params.get('uploaded_after', None)
        if uploaded_after:
            queryset = queryset.filter(upload_date__gte=uploaded_after)
        
        uploaded_before = self.request.query_params.get('uploaded_before', None)
        if uploaded_before:
            queryset = queryset.filter(upload_date__lte=uploaded_before)
        
        ordering = self.request.query_params.get('ordering', '-upload_date')
        valid_ordering_fields = ['upload_date', '-upload_date', 'original_filename', '-original_filename', 'file_size', '-file_size']
        if ordering in valid_ordering_fields:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-upload_date')
        
        return queryset


class FileDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FileDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return FileUpload.objects.filter(uploaded_by=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.mark_accessed()
        logger.info(f"File {instance.id} accessed by user {request.user.id}")
        return super().retrieve(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save()
        invalidate_user_file_cache(self.request.user)

    def perform_destroy(self, instance):
        if instance.file and os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
        instance.delete()
        invalidate_user_file_cache(self.request.user)


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
