# Eduport - File Manager

This is a file manager application built with a React frontend and a Django backend.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Node.js](https://nodejs.org/en/download/) (v18 or later)
- [Python](https://www.python.org/downloads/) (v3.10 or later)
- [Poetry](https://python-poetry.org/docs/#installation) (for backend local development)

## Docker

The recommended way to run this project is using Docker.

### Running the application

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/eduport-file-manager.git
    cd eduport-file-manager
    ```

2.  **Create an environment file:**

    Create a `.env` file in the root of the project and add the following environment variables:

    ```env
    POSTGRES_DB=eduport
    POSTGRES_USER=user
    POSTGRES_PASSWORD=password
    ```

3.  **Build and run the application:**

    ```bash
    docker-compose up --build
    ```

    The application will be available at the following URLs:

    -   **Frontend:** [http://localhost:3000](http://localhost:3000)
    -   **Backend:** [http://localhost:8000](http://localhost:8000)

### Stopping the application

To stop the application, press `Ctrl+C` in the terminal where `docker-compose` is running, and then run:

```bash
docker-compose down
```

## Local Development

If you prefer to run the frontend and backend separately without Docker, follow these instructions.

### Backend

1.  **Navigate to the backend directory:**

    ```bash
    cd backend
    ```

2.  **Create a virtual environment and install dependencies:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Create an environment file:**

    Create a `.env` file in the `backend` directory and add the following environment variables:

    ```env
    DATABASE_URL=postgres://user:password@localhost:5432/eduport
    ```

4.  **Run database migrations:**

    ```bash
    python manage.py migrate
    ```

5.  **Run the development server:**

    ```bash
    python manage.py runserver
    ```

    The backend will be running at [http://localhost:8000](http://localhost:8000).

### Frontend

1.  **Navigate to the frontend directory:**

    ```bash
    cd frontend
    ```

2.  **Install dependencies:**

    ```bash
    npm install
    ```

3.  **Run the development server:**

    ```bash
    npm run dev
    ```

    The frontend will be running at [http://localhost:3000](http://localhost:3000).

## Environment Variables

The following environment variables are used by the application:

-   `POSTGRES_DB`: The name of the PostgreSQL database.
-   `POSTGRES_USER`: The username for the PostgreSQL database.
-   `POSTGRES_PASSWORD`: The password for the PostgreSQL database.
-   `DATABASE_URL`: The connection string for the PostgreSQL database (used in local development).

## Technologies Used

-   **Frontend:**
    -   [React](https://reactjs.org/)
    -   [Vite](https://vitejs.dev/)
    -   [TypeScript](https://www.typescriptlang.org/)
    -   [ESLint](https://eslint.org/)
-   **Backend:**
    -   [Django](https://www.djangoproject.com/)
    -   [Django REST Framework](https://www.django-rest-framework.org/)
    -   [PostgreSQL](https://www.postgresql.org/)
    -   [Gunicorn](https://gunicorn.org/)
-   **DevOps:**
    -   [Docker](https://www.docker.com/)
    -   [Docker Compose](https://docs.docker.com/compose/)

## Project Structure

```
.
├── backend
│   ├── Dockerfile
│   ├── manage.py
│   ├── requirements.txt
│   ├── file_manager
│   ├── files
│   └── users
├── frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── src
│   └── public
├── .gitignore
├── docker-compose.yml
└── README.md
```

## API Endpoints

The backend provides the following API endpoints:

-   `GET /api/files/`: List all files.
-   `POST /api/files/`: Upload a new file.
-   `GET /api/files/<id>/`: Retrieve a specific file.
-   `PUT /api/files/<id>/`: Update a specific file.
-   `DELETE /api/files/<id>/`: Delete a specific file.

-   `POST /api/users/register/`: Register a new user.
-   `POST /api/users/login/`: Log in a user.

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the MIT License.
