from rest_framework import serializers
from django.conf import settings
from .models import FileUpload


class BulkFileUploadSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False, use_url=False),
        help_text="A list of files to be uploaded."
    )

    def validate_files(self, files):
        if not files:
            raise serializers.ValidationError("No files were submitted.")

        max_upload_size = getattr(settings, "MAX_UPLOAD_SIZE", 10485760)  # Default: 10MB
        allowed_file_types = getattr(settings, "ALLOWED_FILE_TYPES", [
            'image/jpeg',
            'image/png',
            'application/pdf',
        ])

        for file in files:
            if file.size > max_upload_size:
                raise serializers.ValidationError(
                    f"File '{file.name}' exceeds the maximum upload size of "
                    f"{max_upload_size // 1024 // 1024}MB."
                )
            
            if file.content_type not in allowed_file_types:
                raise serializers.ValidationError(
                    f"File type '{file.content_type}' is not allowed for '{file.name}'. "
                    f"Allowed types are: {', '.join(allowed_file_types)}"
                )
        
        return files


from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class FileUploadSerializer(serializers.ModelSerializer):
    
    file_hash = serializers.CharField(read_only=True)
    file_size = serializers.IntegerField(read_only=True)
    file_type = serializers.CharField(read_only=True)
    upload_date = serializers.DateTimeField(read_only=True)
    uploaded_by = serializers.StringRelatedField(read_only=True)
    
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
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def get_is_duplicate(self, obj):
        return FileUpload.objects.filter(file_hash=obj.file_hash).count() > 1
    
    def validate_file(self, value):
        if not value:
            raise serializers.ValidationError("No file provided.")
        
        max_size = 100 * 1024 * 1024  # 100MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size ({value.size} bytes) exceeds maximum allowed size ({max_size} bytes)."
            )
        
        allowed_extensions = [
            'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif',
            'mp4', 'avi', 'mov', 'zip', 'rar', 'csv', 'xlsx', 'xls', 'mp3'
        ]
        
        file_extension = value.name.split('.')[-1].lower() if '.' in value.name else ''
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type '.{file_extension}' is not allowed. "
                f"Allowed types: {', '.join(allowed_extensions)}"
            )
        
        dangerous_extensions = ['exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'js']
        if file_extension in dangerous_extensions:
            raise serializers.ValidationError(
                f"File type '.{file_extension}' is not allowed for security reasons."
            )
        
        return value
    
    def validate_original_filename(self, value):
        if not value:
            raise serializers.ValidationError("Original filename is required.")
        
        if '..' in value or '/' in value or '\\' in value:
            raise serializers.ValidationError(
                "Filename contains invalid characters."
            )
        
        if len(value) > 255:
            raise serializers.ValidationError(
                "Filename is too long (maximum 255 characters)."
            )
        
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['uploaded_by'] = request.user
        
        if 'original_filename' not in validated_data and 'file' in validated_data:
            validated_data['original_filename'] = validated_data['file'].name
        
        instance = super().create(validated_data)
        
        if self.get_is_duplicate(instance):
            pass
        
        return instance


class FileListSerializer(serializers.ModelSerializer):
    file_size_display = serializers.CharField(source='get_file_size_display', read_only=True)
    uploaded_by = serializers.StringRelatedField(read_only=True)

    file_url = serializers.SerializerMethodField()
    file_hash = serializers.CharField(read_only=True)
    duplicate_info = serializers.SerializerMethodField()
    content_preview_url = serializers.SerializerMethodField()

    class Meta:
        model = FileUpload
        fields = [
            'id', 'original_filename', 'file_size', 'file_size_display',
            'file_type', 'upload_date', 'uploaded_by', 'last_accessed',
            'file_url', 'file_hash', 'duplicate_info', 'content_preview_url'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        fields_to_keep = {
            'id', 'original_filename', 'file_size', 'file_size_display',
            'file_type', 'upload_date', 'uploaded_by', 'last_accessed',
            'file_url'
        }
        
        request = self.context.get('request')
        if request:
            if request.query_params.get('preview', 'false').lower() == 'true':
                fields_to_keep.add('content_preview_url')
        
        # Remove any fields not in our final set.
        existing = set(self.fields.keys())
        for field_name in existing - fields_to_keep:
            self.fields.pop(field_name)

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

    def get_duplicate_info(self, obj):
        return obj.get_duplicate_info()

    def get_content_preview_url(self, obj):
        request = self.context.get('request')
        if request:
            from django.urls import reverse
            return request.build_absolute_uri(reverse('files:file-content-preview', kwargs={'pk': obj.id}))
        return None


class FileDetailSerializer(serializers.ModelSerializer):

    file_size_display = serializers.CharField(source='get_file_size_display', read_only=True)
    uploaded_by = serializers.StringRelatedField(read_only=True)
    file_url = serializers.SerializerMethodField()
    duplicate_info = serializers.SerializerMethodField()
    max_size = serializers.IntegerField(read_only=True)
    content_preview_url = serializers.SerializerMethodField()

    class Meta:
        model = FileUpload
        fields = [
            'id', 'file', 'original_filename', 'description',
            'file_hash', 'file_size', 'file_size_display', 'file_type',
            'upload_date', 'uploaded_by', 'file_url', 'last_accessed',
            'duplicate_info',
            'max_size',
            'content_preview_url'
        ]

    def get_file_url(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None

    def get_duplicate_info(self, obj):
        return obj.get_duplicate_info()

    def get_content_preview_url(self, obj):
        request = self.context.get('request')
        if request:
            from django.urls import reverse
            return request.build_absolute_uri(reverse('files:file-content-preview', kwargs={'pk': obj.id}))
        return None


        
        return super().create(validated_data)



class FileSearchSerializer(serializers.Serializer):
    search = serializers.CharField(
        required=False,
        max_length=255,
        allow_blank=True,
        help_text="Search in filename and description"
    )
    
    file_type = serializers.CharField(
        required=False,
        max_length=10,
        help_text="Filter by single file type"
    )
    
    file_types = serializers.ListField(
        child=serializers.CharField(max_length=10),
        required=False,
        allow_empty=True,
        help_text="Filter by multiple file types"
    )
    
    start_date = serializers.DateField(required=False, help_text="Filter for files uploaded on or after this date.")
    end_date = serializers.DateField(required=False, help_text="Filter for files uploaded on or before this date.")
    
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
            ('upload_date', 'Upload Date (Ascending)'),
            ('-upload_date', 'Upload Date (Descending)'),
            ('original_filename', 'Filename (A-Z)'),
            ('-original_filename', 'Filename (Z-A)'),
            ('file_size', 'File Size (Smallest First)'),
            ('-file_size', 'File Size (Largest First)'),
        ],
        default='-upload_date',
        help_text="Ordering field"
    )
    
    def validate(self, data):
        """
        Custom validation to ensure logical consistency of filter parameters.
        """
        # Validate file size range
        min_size = data.get('min_size')
        max_size = data.get('max_size')
        
        if min_size is not None and max_size is not None:
            if min_size > max_size:
                raise serializers.ValidationError({
                    'min_size': 'Minimum size cannot be greater than maximum size.'
                })
        
        file_type = data.get('file_type')
        file_types = data.get('file_types', [])
        
        if file_type and file_types:
            raise serializers.ValidationError({
                'file_type': 'Cannot specify both file_type and file_types'
            })
        
        if file_type and not file_types:
            data['file_types'] = [file_type]
        
        return data
    
    def validate_file_type(self, value):
        """Validate single file type."""
        if value:
            return value.lower()
        return value
    
    def validate_file_types(self, value):
        """Validate multiple file types."""
        if value:
            return [ft.lower() for ft in value]
        return value

class BulkDeleteSerializer(serializers.Serializer):
    
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
        if not value:
            raise serializers.ValidationError(
                "Bulk deletion requires explicit confirmation."
            )
        return value
    
    def validate_file_ids(self, value):
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