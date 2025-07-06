# models.py
import hashlib
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


def user_directory_path(instance, filename):
    """
    File will be uploaded to MEDIA_ROOT/uploads/user_<id>/<filename>
    This provides user-specific file organization and prevents filename conflicts.
    """
    # Get file extension to preserve it
    ext = filename.split('.')[-1] if '.' in filename else ''
    
    # Create a clean filename using the hash and original extension
    clean_filename = f"{instance.file_hash[:16]}.{ext}" if ext else instance.file_hash[:16]
    
    return f'uploads/user_{instance.uploaded_by.id}/{clean_filename}'


def validate_file_size(value):
    """
    Validate uploaded file size (max 100MB for this example).
    Adjust the limit based on your requirements.
    """
    max_size = 100 * 1024 * 1024  # 100MB in bytes
    if value.size > max_size:
        raise ValidationError(f'File size cannot exceed {max_size // (1024*1024)}MB')


def validate_file_type(value):
    """
    Validate file type based on extension.
    Add/remove extensions based on your security requirements.
    """
    allowed_extensions = [
        'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 
        'mp4', 'avi', 'mov', 'zip', 'rar', 'csv', 'xlsx', 'xls'
    ]
    
    ext = value.name.split('.')[-1].lower() if '.' in value.name else ''
    if ext not in allowed_extensions:
        raise ValidationError(f'File type "{ext}" is not allowed')


class FileUpload(models.Model):
    """
    Model for storing uploaded files with duplicate detection.
    
    Key Features:
    - File hash for duplicate detection
    - User-specific file organization
    - Comprehensive metadata storage
    - Database indexing for performance
    """
    
    # Foreign key to User model for ownership
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='uploaded_files',
        db_index=True  # Index for efficient queries by user
    )
    
    # File field with custom upload path and validation
    file = models.FileField(
        upload_to=user_directory_path,
        validators=[validate_file_size, validate_file_type],
        help_text="Upload file (max 100MB)"
    )
    
    # Original filename as provided by user
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
        ]
        verbose_name = "File Upload"
        verbose_name_plural = "File Uploads"
    
    def __str__(self):
        return f"{self.original_filename} (uploaded by {self.uploaded_by.username})"
    
    def save(self, *args, **kwargs):
        """
        Override save method to automatically calculate file hash and metadata.
        This is called before saving to database.
        """
        if self.file:
            # Always set file_type from the filename for consistency
            self.file_type = self.get_file_type()

            # Set mime_type if available
            if hasattr(self.file, 'content_type'):
                self.mime_type = self.file.content_type

            # Calculate hash and size only if not already present (for new files)
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
        """
        Extract file type from filename.
        """
        if '.' in self.original_filename:
            return self.original_filename.split('.')[-1].lower()
        return 'unknown'
    
    def get_file_size_display(self):
        """
        Return human-readable file size.
        Useful for displaying in templates.
        """
        if self.file_size < 1024:
            return f"{self.file_size} bytes"
        elif self.file_size < 1024**2:
            return f"{self.file_size/1024:.1f} KB"
        elif self.file_size < 1024**3:
            return f"{self.file_size/(1024**2):.1f} MB"
        else:
            return f"{self.file_size/(1024**3):.1f} GB"
    
    def is_duplicate(self):
        """
        Check if this file is a duplicate of an existing file.
        Used before saving to handle duplicate detection.
        """
        if not self.file_hash:
            return False
        
        return FileUpload.objects.filter(file_hash=self.file_hash).exists()
    
    def get_duplicate_info(self):
        """
        Get information about the original file if this is a duplicate.
        """
        if not self.is_duplicate():
            return None
        
        original = FileUpload.objects.filter(file_hash=self.file_hash).first()
        return {
            'original_filename': original.original_filename,
            'uploaded_by': original.uploaded_by.username,
            'upload_date': original.upload_date,
        }
    
    def mark_accessed(self):
        """
        Update last_accessed timestamp.
        Call this when file is downloaded or viewed.
        """
        self.last_accessed = timezone.now()
        self.save(update_fields=['last_accessed'])
    
    @classmethod
    def get_user_files(cls, user, search_query=None, file_type=None):
        """
        Get files for a specific user with optional filtering.
        This method encapsulates common query patterns.
        """
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
        """
        Get file type statistics for a user.
        Useful for dashboard/analytics.
        """
        from django.db.models import Count
        
        return cls.objects.filter(uploaded_by=user).values('file_type').annotate(
            count=Count('id')
        ).order_by('-count')


class FileAccessLog(models.Model):
    """
    Model for logging file access events.
    This helps in tracking downloads, views, and other interactions.
    """
    
    # Link to the file that was accessed
    file_upload = models.ForeignKey(
        FileUpload,
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    
    # User who accessed the file (can be null if anonymous)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='file_access_logs'
    )
    
    # Timestamp of the access event
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Type of access (e.g., 'download', 'view')
    access_type = models.CharField(
        max_length=50,
        default='view',
        db_index=True
    )
    
    # IP address of the user
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )
    
    # User agent string from the request
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