# File Manager - Web App

A simple file management system built with Django and React. Users can upload and manage files.

## What It Does

- **Upload files** with drag & drop
- **Duplicate detection** - automatically detects if you're uploading the same file twice
- **File search** - find files by name, type, or date
- **User management** - each user has their own files

## Tech Stack

- **Backend:** Django + Django REST Framework
- **Frontend:** React with TypeScript
- **Database:** PostgreSQL
- **File processing:** Celery + Redis for handling large uploads
- **Deployment:** Docker Compose

## How It Works

### File Upload
When you upload a file, the system creates a SHA-256 hash of the file content. This prevents duplicate uploads even if files have different names. The hash calculation is done in chunks to handle large files without eating up memory.

### Search & Performance
File listing uses cursor pagination instead of regular pagination. Database indexes on common search fields (filename, upload date, file type) make searches fast.

### Bulk Uploads
For multiple file uploads, I use Celery to process them in the background. This keeps the UI responsive while files are being processed.

## Quick Start

1. **Clone the project:**
   ```bash
   git clone https://github.com/aakash414/eduport-file-manager-task
   cd eduport-file-manager-task
   ```

2. **Start with Docker:**
   ```bash
   docker-compose up --build
   ```

3. **Access the app:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/
   - API docs: http://localhost:8000/docs/

## Project Structure

```
backend/
├── file_manager/          # Django project settings
├── files/                 # File management app
├── users/                 # User management
└── requirements.txt

frontend/
├── src/
│   ├── components/        # React components
│   ├── pages/             # Page components
│   ├── services/          # API calls
│   └── utils/             # Helper functions
├── public/
└── package.json
```

## Features

1. **Smart duplicate detection** - Uses file content, not just filename
2. **Fast search** - 
4. **Background processing** - Large uploads don't freeze the UI
5. **Clean API** - Easy to integrate with other tools

## What I Learned

- Cursor pagination is much faster than offset pagination for large datasets
- File hashing in chunks prevents memory issues with large files
- Celery is great for background tasks but increased a bit load on server
- Got to learn more about nginx,docker and docker compose
- First time setting up docker and aws on my one

## Known Issues

- File upload for mp3 not not working.
- Search could be more advanced (no regex support)
- Redis not properly utilized yet(only for task queue for celery currently)

## Future Improvements

- Bulk delete: This one was very close but due to time constraints I was not able to complete it.
- Better file preview for more file types
- Folder support
- File sharing via email/ link
