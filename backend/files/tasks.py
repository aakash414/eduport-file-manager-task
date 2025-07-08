import logging
from celery import shared_task
from django.core.files.base import ContentFile
from django.db import IntegrityError
from .models import FileUpload
from .serializers import FileUploadSerializer
from .utils import invalidate_user_file_cache
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

@shared_task
def process_bulk_upload(user_id, files_data):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found for bulk upload.")
        return

    successful_uploads = 0
    for file_data in files_data:
        try:
            uploaded_file = ContentFile(file_data['content'], name=file_data['name'])
            
            serializer_data = {
                'original_filename': file_data['name'],
                'file': uploaded_file
            }

            serializer = FileUploadSerializer(data=serializer_data, context={'request': None}) # No request in task
            
            if serializer.is_valid():
                serializer.save(uploaded_by=user)
                successful_uploads += 1
            else:
                logger.error(f"Failed to serialize file {file_data['name']} for user {user_id}: {serializer.errors}")

        except IntegrityError:
            logger.warning(f"Duplicate file detected during background processing for user {user_id}: {file_data['name']}")
        except Exception as e:
            logger.error(f"Error processing file {file_data['name']} for user {user_id} in background: {str(e)}", exc_info=True)

    if successful_uploads > 0:
        invalidate_user_file_cache(user)
        logger.info(f"Successfully processed {successful_uploads} files for user {user_id}.")
