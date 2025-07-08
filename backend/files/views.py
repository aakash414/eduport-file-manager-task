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
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.pagination import CursorPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.contrib.postgres.search import SearchVector, SearchQuery
from .tasks import process_bulk_upload
from .utils import invalidate_user_file_cache

from .models import FileUpload
from .serializers import (
    BulkFileUploadSerializer,
    FileUploadSerializer, FileListSerializer, FileDetailSerializer,
    FileSearchSerializer,
    BulkDeleteSerializer
)


logger = logging.getLogger(__name__)





@method_decorator(csrf_exempt, name='dispatch')
class BulkFileUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist('files')
        if not files:
            return Response({"error": "No files provided"}, status=status.HTTP_400_BAD_REQUEST)

        files_data = []
        for uploaded_file in files:
            # Read file content to pass to Celery task
            # This ensures the data is JSON-serializable
            files_data.append({
                'name': uploaded_file.name,
                'content': uploaded_file.read(),
            })

        # Delegate the processing to the Celery task
        process_bulk_upload.delay(request.user.id, files_data)

        return Response({
            'message': 'Your files are being processed. They will appear in your file list shortly.',
        }, status=status.HTTP_202_ACCEPTED)


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
    def get_serializer_class(self):

        if self.request.query_params.get('detailed', 'false').lower() == 'true':
            return FileDetailSerializer
        return FileListSerializer
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
        
        search_serializer = FileSearchSerializer(data=request.query_params)
        if not search_serializer.is_valid():
            return Response(search_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Generating new file list for user {request.user.id}")
        response = super().list(request, *args, **kwargs)
        
        if response.status_code == 200:
            cache.set(cache_key, response.data, 60 * 15)
        return response
    
    def get_queryset(self):
        queryset = FileUpload.objects.filter(uploaded_by=self.request.user).select_related('uploaded_by')
        
        search_serializer = FileSearchSerializer(data=self.request.query_params)
        if not search_serializer.is_valid():
            return queryset.none()
        
        search_data = search_serializer.validated_data
        
        search_term = search_data.get('search')
        if search_term:
            queryset = queryset.filter(
                Q(original_filename__icontains=search_term) |
                Q(description__icontains=search_term)
            )
        
        file_types = search_data.get('file_types', [])
        if file_types:
            queryset = queryset.filter(file_type__in=file_types)
    
        start_date = search_data.get('start_date')
        if start_date:
            queryset = queryset.filter(upload_date__date__gte=start_date)

        end_date = search_data.get('end_date')
        if end_date:
            queryset = queryset.filter(upload_date__date__lte=end_date)
    
        if search_data.get('min_size') is not None:
            queryset = queryset.filter(file_size__gte=search_data.get('min_size'))
    
        if search_data.get('max_size') is not None:
            queryset = queryset.filter(file_size__lte=search_data.get('max_size'))
        
        ordering = search_data.get('ordering', '-upload_date')
        queryset = queryset.order_by(ordering)
        
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
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return FileUpload.objects.filter(uploaded_by=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        try:
            file_upload = self.get_object()
            
            file_upload.mark_accessed()
            
            logger.info(
                f"File downloaded: {file_upload.original_filename} "
                f"by user {request.user.username}"
            )
            
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

@method_decorator(xframe_options_exempt, name='dispatch')
class FileContentPreviewView(APIView):
    permission_classes = [IsAuthenticated]

    PREVIEWABLE_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']
    PREVIEWABLE_VIDEO_EXTENSIONS = ['mp4', 'webm', 'ogg']
    PREVIEWABLE_AUDIO_EXTENSIONS = ['mp3', 'wav', 'ogg']
    PREVIEWABLE_PDF_EXTENSIONS = ['pdf']
    PREVIEWABLE_TEXT_EXTENSIONS = ['txt', 'md', 'csv', 'log', 'json', 'xml', 'html', 'css', 'js', 'py', 'java', 'cpp', 'c', 'h']

    PREVIEWABLE_MIME_PREFIXES = ['image/', 'video/', 'audio/']
    PREVIEWABLE_MIME_TYPES = ['application/pdf', 'text/plain']

    MAX_PREVIEW_SIZE = 10 * 1024 * 1024  
    MAX_TEXT_PREVIEW_CHARS = 50000  

    def get(self, request, pk):
        try:
            file_obj = get_object_or_404(
                FileUpload,
                id=pk,
                uploaded_by=request.user
            )

            file_path = file_obj.file.path
            if not os.path.exists(file_path):
                logger.error(f"File not found on disk for pk={pk}: {file_path}")
                return Response({'error': 'File not found on disk'}, status=status.HTTP_404_NOT_FOUND)
            if file_obj.file_size > self.MAX_PREVIEW_SIZE:
                logger.warning(f"File too large for preview for pk={pk}, size={file_obj.file_size}")
                return Response({'error': 'File is too large for preview'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

            file_ext = file_obj.original_filename.split('.')[-1].lower() if '.' in file_obj.original_filename else ''
            mime_type = file_obj.mime_type.lower() if file_obj.mime_type else ''

            is_previewable = False
            if mime_type:
                if any(mime_type.startswith(prefix) for prefix in self.PREVIEWABLE_MIME_PREFIXES):
                    is_previewable = True
                elif mime_type in self.PREVIEWABLE_MIME_TYPES:
                    is_previewable = True
            
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

            if mime_type == 'text/plain':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(self.MAX_TEXT_PREVIEW_CHARS)
            else:
                with open(file_path, 'rb') as f:
                    content = f.read()

            response = HttpResponse(content, content_type=mime_type)
            response['Content-Disposition'] = f'inline; filename=\"{file_obj.original_filename}\"' 
            return response

        except Http404:
            return Response({'error': 'File not found or you do not have permission to view it'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error generating file preview for pk={pk}: {str(e)}", exc_info=True)
            return Response({'error': 'An unexpected error occurred while generating the preview.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([permissions.AllowAny]) 
def health_check(request):
    return Response({'status': 'ok', 'message': 'Service is healthy.'}, status=status.HTTP_200_OK)
    
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
    serializer = BulkDeleteSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    file_ids = serializer.validated_data['file_ids']
    
    try:
        with transaction.atomic():
            files_to_delete = FileUpload.objects.filter(
                id__in=file_ids,
                uploaded_by=request.user
            )
            
            deleted_count = files_to_delete.count()
            filenames = list(files_to_delete.values_list('original_filename', flat=True))
            
            files_to_delete.delete()
            
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
@permission_classes([permissions.AllowAny])
def shared_file_download(request, token):
    try:
        share_link = get_object_or_404(FileShareLink, token=token)
        
        if share_link.is_expired():
            logger.warning(f"Expired share link download attempted: {token}")
            return Response(
                {'error': 'This share link has expired.'},
                status=status.HTTP_410_GONE
            )
        
        if not share_link.is_active:
            logger.warning(f"Inactive share link download attempted: {token}")
            return Response(
                {'error': 'This share link is no longer active.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        share_link.increment_access_count()
        
        file_upload = share_link.file_upload
        logger.info(
            f"Shared file downloaded: {file_upload.original_filename} "
            f"via token {token} from IP {request.META.get('REMOTE_ADDR')}"
        )
        
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

def format_file_size(size_bytes):
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
