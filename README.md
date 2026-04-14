# TaskFlow — Backend Engineering Assignment

TaskFlow is a minimal but powerful task management system backend built with Python and FastAPI. It supports user registration, project ownership, task assignment, and project statistics.

## Overview

### Tech Stack
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Database**: PostgreSQL
- **Migrations**: Alembic
- **Authentication**: JWT with `python-jose` and `bcrypt` hashing
- **Deployment**: Docker & Docker Compose

### Key Features
- **Project Ownership**: Users can create projects and become owners.
- **Task Management**: Projects contain tasks with status (`todo`, `in_progress`, `done`) and priority (`low`, `medium`, `high`).
- **Authorization**: Strict access control (owners vs. participants vs. creators).
- **Graceful Shutdown**: Handles `SIGTERM` and `SIGINT` for clean service exit.
- **Structured Logging**: JSON-ready structured logs for production observability.

## Architecture Decisions

1. **FastAPI over Go**: Chosen for superior developer experience, automatic OpenAPI documentation, and robust type validation with Pydantic.
2. **Explicit Migrations (Alembic)**: Avoided SQLAlchemy's `auto-migrate` to ensure schema changes are trackable, reversible, and predictable in production environments.
3. **Multi-stage Docker Build**: Separates building dependencies from the runtime image, resulting in a significantly smaller and more secure production container.
4. **Relational Constraints**: Used PostgreSQL's foreign keys with `ON DELETE CASCADE` and `SET NULL` to maintain data integrity automatically.

## Running Locally

### Prerequisites
- Docker & Docker Compose

### Fast Start
1. Clone the repository and navigate to the root:
   ```bash
   git clone <repo-url>
   cd taskflow
   ```
2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
3. Start the services:
   ```bash
   docker compose up 
   ```

The API will be available at **http://localhost:5001**.
Interactive API documentation (Swagger) is at **http://localhost:5001/docs**.

## Running Migrations
Migrations run automatically on container startup via the Docker entrypoint (`alembic upgrade head`).
To run them manually inside the container:
```bash
docker exec -it taskflow_api alembic upgrade head
```

## Seed Script
To populate the database with test data (1 user, 1 project, 3 tasks):
```bash
docker exec -it taskflow_api python scripts/seed.py
```

## Test Credentials
- **Email**: `test@example.com`
- **Password**: `password123`

## API Reference

A full Postman collection for testing all endpoints is available in the repository: [Docs/taskflow_collection.json](./Docs/taskflow_collection.json)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT |
| GET | `/api/v1/projects` | List accessible projects |
| POST | `/api/v1/projects` | Create a project |
| GET | `/api/v1/projects/{id}` | Get project details + tasks |
| PATCH | `/api/v1/projects/{id}` | Update project (Owner only) |
| DELETE| `/api/v1/projects/{id}` | Delete project (Owner only) |
| GET | `/api/v1/projects/{id}/tasks`| List tasks in project |
| POST | `/api/v1/projects/{id}/tasks`| Create task in project |
| GET | `/api/v1/projects/{id}/stats`| Project task statistics |
| PATCH | `/api/v1/tasks/{id}` | Update task |
| DELETE| `/api/v1/tasks/{id}` | Delete task (Owner/Creator only) |

## What I'd Do With More Time
1. **Real-time Notifications**: Implement WebSockets or SSE for instant task updates across users.
2. **Global Search**: Add full-text search capabilities using PostgreSQL's `tsvector`.
3. **Advanced Filtering**: Support complex multi-field filtering and sorting on all list endpoints.
4. **Unit Tests**: Implement a comprehensive suite of unit tests with a dedicated test database container.
