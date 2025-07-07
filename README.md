# File Management System

This project is a comprehensive file management system built to fulfill the requirements of the provided technical assessment. It features a Django backend and a React frontend, containerized with Docker for setup and deployment.

## Core Features & Implementation Choices

This section details the implementation of each required feature, explaining the technical decisions made.

### 1. User Authentication

-   **Technology:** Implemented using Django's built-in session authentication.

### 2. File Upload & Duplicate Prevention

-   **Technology:** File uploads are handled through a REST API endpoint. Duplicate prevention is done using a SHA-256 hash of the file's content upon upload.
-   **Implementation:**
    -   The `FileUpload` model has a `file_hash` field with a `unique=True` constraint at the database level. This guarantees that no two records can have the same file hash, ensuring data integrity.
    -   Before saving a new file, its SHA-256 hash is computed in chunks to handle large files efficiently without consuming excessive memory.
    -   If a file with the same hash already exists, the database will raise an `IntegrityError`. The `FileUploadView` catches this specific error and returns a `409 Conflict` response to the client, indicating that the file is a duplicate.
-   **Reasoning:** This hash-based approach is highly effective for preventing duplicate file uploads. Using a database-level `unique` constraint is the most reliable way to enforce this rule.

### 3. File Management

-   **List & Search:**
    -   **Technology:** The file list is exposed via a paginated API endpoint. The search functionality allows filtering by filename, file type, and upload date.
    -   **Optimization:**
        -   **Database Indexing:** I've added database indexes to the `FileUpload` model on fields that are frequently used in queries, such as `uploaded_by`, `upload_date`, `file_type`, and `file_hash`. This significantly improves the performance of filtering and sorting operations.
        -   **Pagination:** I chose `CursorPagination` for the file list endpoint. It's more efficient for large datasets than traditional page number pagination, as it avoids expensive `COUNT` queries.
        -   **Caching:** I've implemented a caching layer using Redis. The file list and file type endpoints are cached to reduce database load and provide a faster response to the user. The cache is intelligently invalidated whenever a file is uploaded, updated, or deleted.

-   **Delete:**
    -   **Implementation:** Users can delete their own files via a `DELETE` request to the file's API endpoint. The backend ensures that users can only delete files they have uploaded.

### 4. API Documentation

-   **Technology:** I've used `drf-spectacular` to generate OpenAPI 3 documentation for the backend API.
-   **Reasoning:** Providing clear API documentation is crucial for any project. `drf-spectacular` automatically generates a comprehensive and interactive Swagger UI, which makes it easy to explore and test the API endpoints. The documentation is available at the `/api/docs/` endpoint.

## Bonus: Deployment with Docker

-   **Technology:** The entire application (backend, frontend, database, and Redis) is containerized using Docker and orchestrated with Docker Compose.
-   **Reasoning:**
    -   **Consistency:** Docker ensures that the application runs in a consistent environment, eliminating the "it works on my machine" problem.
    -   **Ease of Use:** With a single `docker-compose up` command, the entire stack is provisioned and started. This simplifies the setup process for both development and production.
    -   **Scalability:** The containerized setup makes it easy to scale individual components of the application in the future.

## Getting Started

### Prerequisites

-   [Docker](https://www.docker.com/get-started)
-   [Docker Compose](https://docs.docker.com/compose/install/)

### Running the Application

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/eduport-file-manager.git
    cd eduport-file-manager
    ```

2.  **Create an environment file:**
    ```bash
    cp .env.example .env
    ```
    Update the `.env` file with a new `SECRET_KEY`.

3.  **Build and run with Docker Compose:**
    ```bash
    docker-compose up --build
    ```

The application will be available at:

-   **Frontend:** [http://localhost:3000](http://localhost:3000)
-   **Backend API:** [http://localhost:8000/api/](http://localhost:8000/api/)
-   **API Docs:** [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

### Stopping the Application

```bash
docker-compose down
```
