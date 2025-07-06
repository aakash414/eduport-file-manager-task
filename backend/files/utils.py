from django.core.exceptions import ValidationError


def user_directory_path(instance, filename):
    ext = filename.split('.')[-1] if '.' in filename else ''
    clean_filename = f"{instance.file_hash[:16]}.{ext}" if ext else instance.file_hash[:16]
    
    return f'uploads/user_{instance.uploaded_by.id}/{clean_filename}'


def validate_file_size(value):
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
