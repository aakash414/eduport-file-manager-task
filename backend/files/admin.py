from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import FileUpload, FileAccessLog


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    # List view configuration
    list_display = [
        'original_filename',
        'uploaded_by',
        'file_type',
        'get_file_size_display',
        'upload_date',
        'has_duplicates',
        'download_link'
    ]
    
    list_filter = [
        'file_type',
        'upload_date',
        'uploaded_by',
    ]
    
    search_fields = [
        'original_filename',
        'uploaded_by__username',
        'uploaded_by__email',
        'file_hash',
    ]
    
    # Detail view configuration
    fieldsets = (
        ('File Information', {
            'fields': ('file', 'original_filename', 'description')
        }),
        ('Metadata', {
            'fields': ('file_hash', 'file_size', 'file_type', 'upload_date'),
            'classes': ('collapse',)
        }),
        ('User Information', {
            'fields': ('uploaded_by',)
        }),
        ('Access Tracking', {
            'fields': ('last_accessed',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = [
        'file_hash',
        'file_size',
        'file_type',
        'upload_date',
        'last_accessed'
    ]
    
    # Pagination
    list_per_page = 25
    
    # Ordering
    ordering = ['-upload_date']
    
    def has_duplicates(self, obj):
        """Check if file has duplicates."""
        count = FileUpload.objects.filter(file_hash=obj.file_hash).count()
        if count > 1:
            return format_html(
                '<span style="color: red;">Yes ({})</span>',
                count
            )
        return 'No'
    has_duplicates.short_description = 'Has Duplicates'
    
    def download_link(self, obj):
        """Provide download link for the file."""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">Download</a>',
                obj.file.url
            )
        return 'No file'
    download_link.short_description = 'Download'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('uploaded_by')
    
    # Custom actions
    actions = ['mark_as_accessed', 'show_duplicate_info']
    
    def mark_as_accessed(self, request, queryset):
        """Mark selected files as accessed."""
        updated = 0
        for obj in queryset:
            obj.mark_accessed()
            updated += 1
        
        self.message_user(
            request,
            f'{updated} file(s) marked as accessed.'
        )
    mark_as_accessed.short_description = 'Mark selected files as accessed'
    
    def show_duplicate_info(self, request, queryset):
        """Show duplicate information for selected files."""
        for obj in queryset:
            if obj.is_duplicate():
                info = obj.get_duplicate_info()
                self.message_user(
                    request,
                    f'File "{obj.original_filename}" is a duplicate of "{info["original_filename"]}" '
                    f'uploaded by {info["uploaded_by"]} on {info["upload_date"]}'
                )
            else:
                self.message_user(
                    request,
                    f'File "{obj.original_filename}" is not a duplicate.'
                )
    show_duplicate_info.short_description = 'Show duplicate information'

