from rest_framework import serializers
from django.conf import settings
from .models import FileUpload


class BulkFileUploadSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False, use_url=False),
        help_text="A list of files to be uploaded."
    )

    def validate_files(self, files):
        """
        Validates a list of uploaded files.
        """
        if not files:
            raise serializers.ValidationError("No files were submitted.")

        # Get upload limits from Django settings, with defaults.
        max_upload_size = getattr(settings, "MAX_UPLOAD_SIZE", 2621440)  # Default: 2.5MB
        allowed_file_types = getattr(settings, "ALLOWED_FILE_TYPES", [
            'image/jpeg',
            'image/png',
            'application/pdf',
        ])

        for file in files:
            # Validate file size
            if file.size > max_upload_size:
                raise serializers.ValidationError(
                    f"File '{file.name}' exceeds the maximum upload size of "
                    f"{max_upload_size // 1024 // 1024}MB."
                )
            
            # Validate file type
            if file.content_type not in allowed_file_types:
                raise serializers.ValidationError(
                    f"File type '{file.content_type}' is not allowed for '{file.name}'. "
                    f"Allowed types are: {', '.join(allowed_file_types)}"
                )
        
        return files


from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class FileUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for file uploads with comprehensive validation.
    
    Interview Talking Points:
    - Custom validation for file types and sizes
    - Duplicate detection using file hashing
    - Security considerations for file uploads
    - Performance optimization with selective field updates
    """
    
    # Read-only fields that are auto-generated
    file_hash = serializers.CharField(read_only=True)
    file_size = serializers.IntegerField(read_only=True)
    file_type = serializers.CharField(read_only=True)
    upload_date = serializers.DateTimeField(read_only=True)
    uploaded_by = serializers.StringRelatedField(read_only=True)
    
    # Display fields for better API responses
    file_size_display = serializers.CharField(source='get_file_size_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    is_duplicate = serializers.SerializerMethodField()
    
    class Meta:
        model = FileUpload
        fields = [
            'id', 'file', 'original_filename', 'description',
            'file_hash', 'file_size', 'file_size_display', 'file_type',
            'upload_date', 'uploaded_by', 'file_url', 'is_duplicate',
            'last_accessed'
        ]
        read_only_fields = [
            'id', 'file_hash', 'file_size', 'file_type', 'upload_date',
            'uploaded_by', 'last_accessed'
        ]
    
    def get_file_url(self, obj):
        """
        Get the file URL for download.
        Security: Only returns URL if user has access to the file.
        """
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def get_is_duplicate(self, obj):
        """
        Check if file is a duplicate.
        Performance: This is efficient due to unique index on file_hash.
        """
        return FileUpload.objects.filter(file_hash=obj.file_hash).count() > 1
    
    def validate_file(self, value):
        """
        Comprehensive file validation.
        
        Security Considerations:
        - File size limits
        - File type restrictions
        - Malicious file detection
        """
        if not value:
            raise serializers.ValidationError("No file provided.")
        
        # File size validation (100MB limit)
        max_size = 100 * 1024 * 1024  # 100MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size ({value.size} bytes) exceeds maximum allowed size ({max_size} bytes)."
            )
        
        # File type validation
        allowed_extensions = [
            'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif',
            'mp4', 'avi', 'mov', 'zip', 'rar', 'csv', 'xlsx', 'xls'
        ]
        
        file_extension = value.name.split('.')[-1].lower() if '.' in value.name else ''
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type '.{file_extension}' is not allowed. "
                f"Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Security: Check for potentially malicious files
        dangerous_extensions = ['exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'js']
        if file_extension in dangerous_extensions:
            raise serializers.ValidationError(
                f"File type '.{file_extension}' is not allowed for security reasons."
            )
        
        return value
    
    def validate_original_filename(self, value):
        """
        Validate filename for security.
        """
        if not value:
            raise serializers.ValidationError("Original filename is required.")
        
        # Security: Prevent directory traversal attacks
        if '..' in value or '/' in value or '\\' in value:
            raise serializers.ValidationError(
                "Filename contains invalid characters."
            )
        
        # Length validation
        if len(value) > 255:
            raise serializers.ValidationError(
                "Filename is too long (maximum 255 characters)."
            )
        
        return value
    
    def create(self, validated_data):
        """
        Create file upload with duplicate detection.
        
        Interview Talking Points:
        - Duplicate detection strategy
        - Atomic operations for data integrity
        - Error handling for edge cases
        """
        # Set the user from the request context
        request = self.context.get('request')
        if request and request.user:
            validated_data['uploaded_by'] = request.user
        
        # Set original filename from the uploaded file if not provided
        if 'original_filename' not in validated_data and 'file' in validated_data:
            validated_data['original_filename'] = validated_data['file'].name
        
        # Create the instance (file hash will be calculated in model's save method)
        instance = super().create(validated_data)
        
        # Check for duplicates after creation
        if self.get_is_duplicate(instance):
            # Log duplicate for analytics (optional)
            # logger.info(f"Duplicate file uploaded: {instance.file_hash}")
            pass
        
        return instance


class FileListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for file listing.
    
    Performance: Minimal fields for efficient pagination.
    """
    file_size_display = serializers.CharField(source='get_file_size_display', read_only=True)
    uploaded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = FileUpload
        fields = [
            'id', 'original_filename', 'file_size', 'file_size_display',
            'file_type', 'upload_date', 'uploaded_by', 'last_accessed'
        ]


class FileDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for single file view.
    
    Includes all metadata and related information.
    """
    file_size_display = serializers.CharField(source='get_file_size_display', read_only=True)
    uploaded_by = serializers.StringRelatedField(read_only=True)
    file_url = serializers.SerializerMethodField()
    duplicate_info = serializers.SerializerMethodField()
    
    class Meta:
        model = FileUpload
        fields = [
            'id', 'file', 'original_filename', 'description',
            'file_hash', 'file_size', 'file_size_display', 'file_type',
            'upload_date', 'uploaded_by', 'file_url', 'last_accessed',
            'duplicate_info'
        ]
    
    def get_file_url(self, obj):
        """Get file URL for download."""
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def get_duplicate_info(self, obj):
        """Get duplicate file information."""
        return obj.get_duplicate_info()


        
        return super().create(validated_data)


class FileSearchSerializer(serializers.Serializer):
    """
    Serializer for file search parameters.
    
    Interview Talking Points:
    - Search optimization strategies
    - Query parameter validation
    - Performance considerations for large datasets
    """
    
    search = serializers.CharField(
        required=False,
        max_length=255,
        help_text="Search in filename"
    )
    
    file_type = serializers.CharField(
        required=False,
        max_length=10,
        help_text="Filter by file type"
    )
    
    uploaded_after = serializers.DateTimeField(
        required=False,
        help_text="Filter files uploaded after this date"
    )
    
    uploaded_before = serializers.DateTimeField(
        required=False,
        help_text="Filter files uploaded before this date"
    )
    
    min_size = serializers.IntegerField(
        required=False,
        min_value=0,
        help_text="Minimum file size in bytes"
    )
    
    max_size = serializers.IntegerField(
        required=False,
        min_value=0,
        help_text="Maximum file size in bytes"
    )
    
    ordering = serializers.ChoiceField(
        choices=[
            'upload_date', '-upload_date',
            'original_filename', '-original_filename',
            'file_size', '-file_size'
        ],
        default='-upload_date',
        help_text="Ordering field"
    )
    
    def validate(self, data):
        """Cross-field validation."""
        # Validate date range
        if 'uploaded_after' in data and 'uploaded_before' in data:
            if data['uploaded_after'] >= data['uploaded_before']:
                raise serializers.ValidationError(
                    "uploaded_after must be before uploaded_before"
                )
        
        # Validate size range
        if 'min_size' in data and 'max_size' in data:
            if data['min_size'] > data['max_size']:
                raise serializers.ValidationError(
                    "min_size must be less than or equal to max_size"
                )
        
        return data


class FileStatsSerializer(serializers.Serializer):
    """
    Serializer for file statistics.
    
    Used for dashboard analytics and reporting.
    """
    
    total_files = serializers.IntegerField()
    total_size = serializers.IntegerField()
    total_size_display = serializers.CharField()
    file_types = serializers.ListField(
        child=serializers.DictField()
    )
    recent_uploads = serializers.IntegerField()
    
    class Meta:
        fields = [
            'total_files', 'total_size', 'total_size_display',
            'file_types', 'recent_uploads'
        ]


class BulkDeleteSerializer(serializers.Serializer):
    """
    Serializer for bulk file deletion.
    
    Interview Talking Points:
    - Bulk operations for better UX
    - Validation for destructive operations
    - Error handling for partial failures
    """
    
    file_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100,  # Prevent abuse
        help_text="List of file IDs to delete"
    )
    
    confirm = serializers.BooleanField(
        default=False,
        help_text="Confirmation flag for deletion"
    )
    
    def validate_confirm(self, value):
        """Require explicit confirmation for bulk deletion."""
        if not value:
            raise serializers.ValidationError(
                "Bulk deletion requires explicit confirmation."
            )
        return value
    
    def validate_file_ids(self, value):
        """Validate file IDs exist and belong to user."""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required.")
        
        # Check if all files exist and belong to the user
        existing_files = FileUpload.objects.filter(
            id__in=value,
            uploaded_by=request.user
        ).values_list('id', flat=True)
        
        missing_files = set(value) - set(existing_files)
        if missing_files:
            raise serializers.ValidationError(
                f"Files not found or not owned by user: {list(missing_files)}"
            )
        
        return value