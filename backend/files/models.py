from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class FileUpload(models.Model):
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, unique=True)
    file_size = models.BigIntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=50)