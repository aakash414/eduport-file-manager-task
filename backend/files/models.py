# models.py
import hashlib
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from .utils import user_directory_path, validate_file_size, validate_file_type



class FileUpload(models.Model):
    
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='uploaded_files',
        db_index=True
    )
    
    file = models.FileField(
        upload_to=user_directory_path,
        validators=[validate_file_size, validate_file_type],
        help_text="Upload file (max 100MB)"
    )
    
    original_filename = models.CharField(
        max_length=255,
        help_text="Original filename as uploaded by user"
    )
    
    # File hash for duplicate detection (SHA256 for security)
    file_hash = models.CharField(
        max_length=64,  # SHA256 produces 64 character hex string
        unique=True,    # Prevents duplicate files across entire system
        db_index=True,  # Index for fast duplicate checking
        help_text="SHA256 hash of file content for duplicate detection"
    )
    
    # File size in bytes
    file_size = models.BigIntegerField(
        help_text="File size in bytes"
    )
    
    # Upload timestamp
    upload_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True  # Index for sorting by upload date
    )
    
    # File type derived from extension
    file_type = models.CharField(
        max_length=10,
        db_index=True,  # Index for filtering by file type
        help_text="File extension/type"
    )
    
    # Optional: File description
    description = models.TextField(
        blank=True,
        null=True,
                help_text="Optional file description"
    )

    # Mime type of the file
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="MIME type of the file"
    )

    # last modified timestamp
    last_modified = models.DateTimeField(
        auto_now=True,
        help_text="Last time file was modified"
    )
    
    # Track file access for analytics (optional)
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
                help_text="Last time file was accessed"
    )

    view_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times the file has been viewed"
    )

    duplicate_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='duplicates',
        help_text="Link to the original file if this is a duplicate"
    )
    
    class Meta:
        ordering = ['-upload_date']  # Most recent first
        indexes = [
            # Composite index for user + upload date (common query pattern)
            models.Index(fields=['uploaded_by', '-upload_date']),
            # Index for searching by filename
            models.Index(fields=['original_filename']),
            # Index for file type filtering
            models.Index(fields=['file_type']),
            # Index for sorting by file size
            models.Index(fields=['file_size']),
        ]
        verbose_name = "File Upload"
        verbose_name_plural = "File Uploads"
    
    def __str__(self):
        return f"{self.original_filename} (uploaded by {self.uploaded_by.username})"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_type = self.get_file_type()

            if hasattr(self.file, 'content_type'):
                self.mime_type = self.file.content_type

            if not self.file_hash:
                self.file_hash = self.calculate_file_hash()
                self.file_size = self.file.size

        super().save(*args, **kwargs)
    
    @staticmethod
    def calculate_file_hash_from_file(file_obj):
        if not file_obj:
            return None
        hasher = hashlib.sha256()
        file_obj.seek(0)
        for chunk in file_obj.chunks():
            hasher.update(chunk)
        file_obj.seek(0)
        return hasher.hexdigest()

    def calculate_file_hash(self):
        return self.calculate_file_hash_from_file(self.file)
    
    def get_file_type(self):
        if '.' in self.original_filename:
            return self.original_filename.split('.')[-1].lower()
        return 'unknown'
    
    def get_file_size_display(self):
        if self.file_size < 1024:
            return f"{self.file_size} bytes"
        elif self.file_size < 1024**2:
            return f"{self.file_size/1024:.1f} KB"
        elif self.file_size < 1024**3:
            return f"{self.file_size/(1024**2):.1f} MB"
        else:
            return f"{self.file_size/(1024**3):.1f} GB"
    
    def is_duplicate(self):
        if not self.file_hash:
            return False
        
        return FileUpload.objects.filter(file_hash=self.file_hash).exists()
    
    def get_duplicate_info(self):
        if not self.is_duplicate():
            return None
        
        original = FileUpload.objects.filter(file_hash=self.file_hash).first()
        return {
            'original_filename': original.original_filename,
            'uploaded_by': original.uploaded_by.username,
            'upload_date': original.upload_date,
        }
    
    def mark_accessed(self):
        self.last_accessed = timezone.now()
        self.save(update_fields=['last_accessed'])
    
    @classmethod
    def get_user_files(cls, user, search_query=None, file_type=None):
        queryset = cls.objects.filter(uploaded_by=user)
        
        if search_query:
            queryset = queryset.filter(
                original_filename__icontains=search_query
            )
        
        if file_type:
            queryset = queryset.filter(file_type=file_type)
        
        return queryset
    
    @classmethod
    def get_file_type_stats(cls, user):
        from django.db.models import Count
        
        return cls.objects.filter(uploaded_by=user).values('file_type').annotate(
            count=Count('id')
        ).order_by('-count')


class FileAccessLog(models.Model):
    file_upload = models.ForeignKey(
        FileUpload,
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='file_access_logs'
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    access_type = models.CharField(
        max_length=50,
        default='view',
        db_index=True
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )
    
    user_agent = models.TextField(
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['file_upload', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.access_type} by {self.user.username if self.user else 'Anonymous'} at {self.timestamp}"