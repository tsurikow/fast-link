# Fast-Link

Fast-Link is a modern URL shortener service that combines a robust FastAPI backend with a user-friendly Streamlit frontend. It provides features such as URL shortening, custom URL creation with expiration settings, user authentication, and URL management (update, delete, and statistics). The project uses PostgreSQL for persistent storage, Redis for caching, Alembic for migrations, and Docker Compose for container orchestration.

---

## Features

- **URL Shortening:** Automatically generate unique short codes for long URLs.
- **Custom Short URL Creation:** Authenticated users can create custom short URLs by specifying their own short codes and expiration times.
- **User Authentication:** Secure endpoints using FastAPI Users (JWT and OAuth2) with email and password.
- **URL Management:** Update, delete (move to expired history), and view statistics (creation date, hit count, last used timestamp) for your URLs.
- **Caching:** Utilize Redis caching for faster redirection and reduced database load.
- **Automatic Expiration Handling:** Background tasks move expired URLs to a separate history table.
- **Multipage Streamlit Frontend:** A sleek, organized web interface for managing URLs.
- **Dockerized Deployment:** Easy deployment and scaling with Docker Compose.

---

## Tech Stack

- **Backend:** FastAPI, Python 3.12, uv dependency manager, Alembic
- **Database:** PostgreSQL
- **Cache:** Redis
- **Authentication:** FastAPI Users (JWT, OAuth2)
- **Frontend:** Streamlit
- **Containerization:** Docker, Docker Compose

---

## Project Structure

```
.
├── LICENSE
├── README.md
├── alembic.ini
├── backend
│   ├── Dockerfile
│   ├── init.py
│   ├── app
│   │   ├── init.py
│   │   ├── api
│   │   │   ├── init.py
│   │   │   ├── routes
│   │   │   │   ├── init.py
│   │   │   │   ├── auth_users.py
│   │   │   │   └── url.py
│   │   │   └── schemas
│   │   │       ├── init.py
│   │   │       ├── url.py
│   │   │       └── user.py
│   │   ├── core
│   │   │   ├── init.py
│   │   │   ├── config.py
│   │   │   ├── logging_config.py
│   │   │   ├── manager.py
│   │   │   └── security.py
│   │   ├── db
│   │   │   ├── init.py
│   │   │   ├── base_class.py
│   │   │   ├── migrations
│   │   │   │   ├── README
│   │   │   │   ├── env.py
│   │   │   │   ├── script.py.mako
│   │   │   │   └── versions
│   │   │   │       └── f9073e260444_.py
│   │   │   └── session.py
│   │   ├── main.py
│   │   ├── models
│   │   │   ├── init.py
│   │   │   ├── url.py
│   │   │   └── user.py
│   │   └── services
│   │       ├── init.py
│   │       ├── cache.py
│   │       ├── expiration.py
│   │       ├── shortener.py
│   │       ├── url_dependencies.py
│   │       ├── url_helpers.py
│   │       └── url_utils.py
│   └── scripts
│       └── entrypoint.sh
├── docker-compose.yml
├── frontend
│   ├── Dockerfile
│   ├── init.py
│   ├── app.py
│   ├── config.py
│   ├── helpers.py
│   └── logging_config.py
├── project_structure.txt
├── pyproject.toml
├── scripts
│   └── deploy.sh
└── uv.lock
```

---

## Dependencies

The project is managed using [uv](https://github.com/astral-sh/uv) with a single `pyproject.toml`. Key dependencies include:

- **Core:** `loguru`, `pydantic`, `pydantic-settings`
- **Backend:** `alembic`, `asyncpg`, `fastapi`, `fastapi-users[sqlalchemy]`, `redis`, `sqlalchemy`, `uvicorn`
- **Frontend:** `requests`, `streamlit`

See the `[project.optional-dependencies]` section in `pyproject.toml` for more details.

---------------------------------------------------------------------------------------

## Installation and Local Development

### Prerequisites

- Docker & Docker Compose
- Git

### Setup

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/fast-link.git
   cd fast-link
   ```
2. Prepare Environment Variables:
   Create a .env file based on the provided .env.dist file:

   ```bash
   cp .env.dist .env
   ```
   Edit .env to set your own secrets and configuration (e.g. Redis, Postgres, FastAPI, Streamlit ports).
3. Build and Run Containers:

   ```bash
   docker-compose up --build
   ```
4.	Access the Applications:
-	FastAPI API: http://localhost:8000 (or the port defined by FASTAPI_PORT)
-	Streamlit Frontend: http://localhost:8501 (or the port defined by STREAMLIT_PORT)

---
## Deployment

For production, use the provided deploy script to automate setup. A common approach is to include a .env.dist file in your repository and then, during deployment, rename it to .env if no .env file exists. For example, your deploy script (scripts/deploy.sh) might contain:
```bash
#!/bin/bash
set -e

if [ ! -f .env ]; then
    echo "No .env file found. Copying .env.dist to .env..."
    cp .env.dist .env
fi

docker-compose up -d
```
Place this script in the root of your repository, mark it executable (chmod +x scripts/deploy.sh), and run it on your VPS after cloning the repository.

---

## Usage

### FastAPI API Endpoints
- **POST /url:** Create or update a shortened URL.
- **POST /shorten:** Create a custom short URL with a user-defined short code and expiration time (authenticated only).
- **GET /{short_code}:** Redirect to the original URL.
- **PUT /{short_code}:** Update a URL. Users can choose whether to regenerate the short code.
- **DELETE /{short_code}:** Move a URL to expired history.
- **GET /{short_code}/stats:** Retrieve URL usage statistics.
- **GET /my_urls?type=active|expired:** Get URLs created by the authenticated user, filtered by active or expired status.

### Streamlit Frontend

The multipage Streamlit frontend provides an intuitive interface for:
- Logging in and registering.
- Creating short URLs (auto-generated or custom).
- Searching for URLs.
- Full URL history for user.
- Updating or deleting URLs.
- Viewing URL statistics.
- Viewing current user information.

Pages are organized in separate files under the frontend directory (or a pages subdirectory) and accessible via sidebar navigation.

---
