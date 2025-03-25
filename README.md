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

## FastAPI API Endpoints

### Urls Group

1. **POST /url**  
   **Description:**  
   - Creates a new shortened URL or updates an existing one.
   - **For authenticated users:**  
     - The endpoint checks if a URL with the same original URL already exists for that user. If found, it refreshes its expiration date.
     - If not found, it creates a new URL record and assigns the user’s ID to the `created_by` field.
   - **For anonymous users:**  
     - A new URL is always created (with `created_by` set to null).

2. **GET /my_urls**  
   **Description:**  
   - Retrieves a list of URLs created by the authenticated user.
   - Accepts a query parameter (`url_type`) with values `"active"` or `"expired"`:
     - **active:** Returns URLs from the active URLs table.
     - **expired:** Returns URLs from the expired URLs table.
   - The results are sorted by creation date in descending order.

3. **POST /shorten**  
   **Description:**  
   - Allows an authenticated user to create a custom short URL.
   - The user specifies a custom short code and an expiration time.
   - The endpoint validates that the expiration time is in the future and that the custom short code is unique.
   - On success, a new URL record is created with the provided details.

4. **GET /search**  
   **Description:**  
   - Searches for active URLs based on the provided original URL.
   - Returns a list of URL details that match the given original URL.
   - If no URLs are found, a 404 error is returned.

5. **GET /{short_code}**  
   **Description:**  
   - Redirects the client to the original URL associated with the provided short code.
   - First checks Redis for a cached mapping; on a cache miss, it queries the database.
   - Validates that the URL exists and is not expired.
   - Also schedules a background task to update the URL’s hit counter and expiration (if not fixed).

6. **DELETE /{short_code}**  
   **Description:**  
   - Moves a URL from the active table to the expired history.
   - Only the user who created the URL (as indicated by the `created_by` field) can delete (i.e. move) the URL.
   - Upon success, the URL is removed from the active table, inserted into the expired URLs table (preserving all usage data), and its cache entry in Redis is deleted.

7. **PUT /{short_code}**  
   **Description:**  
   - Updates the original URL of an existing record.
   - Authenticated users can choose whether to generate a new short code:
     - **If regenerating:** A new short code is generated (using a salt to ensure uniqueness), the old short code is removed from Redis, and the new mapping is stored.
     - **If not regenerating:** Only the original URL is updated, and the cache is updated with the new original URL while retaining the current short code.
   - Ownership is enforced: only the creator (as per `created_by`) may update the URL.

8. **GET /{short_code}/stats**  
   **Description:**  
   - Retrieves usage statistics for the given short code.
   - Returns details such as the original URL, creation date, hit count, and last used timestamp.
   - This endpoint is accessible even for anonymous users (unless further restricted).

### Auth Group

1. **POST /auth/jwt/login**  
   **Description:**  
   - Authenticates a user using email and password.
   - On success, returns a JWT access token for subsequent authenticated requests.
   - If the credentials are invalid, it returns a 401 error.

2. **POST /auth/register**  
   **Description:**  
   - Registers a new user with an email and password.
   - Validates that the email is in a correct format and not already in use.
   - Returns a 201 status on success.

### Users Group

1. **GET /users/me**  
   **Description:**  
   - Returns detailed information about the current authenticated user.
   - Requires a valid JWT token and typically includes email and other profile details.


---

## Streamlit Frontend

The multipage Streamlit frontend provides an intuitive interface for:
- Logging in and registering.
- Creating short URLs (auto-generated or custom).
- Searching for URLs.
- Full URL history for user.
- Updating or deleting URLs.
- Viewing URL statistics.
- Viewing current user information.

Pages are organized and accessible via sidebar navigation.

---

## Database Structure

The Fast-Link service uses a async PostgreSQL database with a schema that includes tables for active URLs, expired URLs, and users. Below is a description of the key tables and their columns:

### Table: urls

This table stores active (non-expired) URL records.

| Column         | Data Type                        | Constraints & Defaults                                    | Description                                                  |
|----------------|----------------------------------|-----------------------------------------------------------|--------------------------------------------------------------|
| **id**         | UUID (native, PG_UUID(as_uuid=True))  | Primary key; default: `uuid.uuid4()`                    | Unique identifier for each URL record.                       |
| **short_code** | String                           | Unique, not null, indexed                                 | The unique short code generated for the URL.                 |
| **original_url** | String                         | Not null                                                  | The original, long URL provided by the user.                 |
| **created_at** | DateTime (with timezone)         | Not null; server default: `func.now()`                    | Timestamp when the URL was created.                          |
| **expires_at** | DateTime (with timezone)         | Nullable                                                  | The expiration timestamp of the URL (if applicable).         |
| **hit_count**  | Integer                          | Not null; default: `0`                                      | The number of times the short URL has been accessed.         |
| **created_by** | UUID (native, PG_UUID(as_uuid=True))  | Nullable; foreign key referencing `user.id`             | The ID of the user who created the URL (null for anonymous).   |
| **last_used_at** | DateTime (with timezone)       | Nullable                                                  | Timestamp of the most recent access of the URL.              |
| **fixed_expiration** | Boolean                    | Not null; default: `false` (using SQL text "false")       | Flag indicating if the expiration should remain fixed on access.|

---

### Table: expired_urls

This table stores URL records that have expired or have been “deleted” (moved to history). Unlike active URLs, the `short_code` in this table is not required to be unique, allowing reuse of short codes in active URLs.

| Column         | Data Type                        | Constraints & Defaults                                    | Description                                                  |
|----------------|----------------------------------|-----------------------------------------------------------|--------------------------------------------------------------|
| **id**         | UUID (native, PG_UUID(as_uuid=True))  | Primary key; default: `uuid.uuid4()`                    | Unique identifier for each expired URL record.               |
| **short_code** | String                           | Not null, indexed (uniqueness not enforced)               | The short code originally assigned to the URL.               |
| **original_url** | String                         | Not null                                                  | The original URL provided by the user.                       |
| **created_at** | DateTime (with timezone)         | Not null; server default: `func.now()`                    | Timestamp when the URL was created.                          |
| **expires_at** | DateTime (with timezone)         | Nullable                                                  | The expiration timestamp when the URL was valid.             |
| **hit_count**  | Integer                          | Not null; default: `0`                                      | The number of times the URL was accessed before expiring.      |
| **moved_at**   | DateTime (with timezone)         | Not null; server default: `func.now()`                    | Timestamp when the URL was moved to the expired history.       |
| **created_by** | UUID (native, PG_UUID(as_uuid=True))  | Nullable; foreign key referencing `user.id`             | The ID of the user who created the URL (null for anonymous).   |
| **last_used_at** | DateTime (with timezone)       | Nullable                                                  | Timestamp of the most recent access of the URL.              |
| **fixed_expiration** | Boolean                    | Not null; default: `false` (using SQL text "false")       | Flag indicating if the expiration was fixed on access.         |

---

### Table: user

The user table is managed by FastAPI Users and typically includes:

| Column  | Data Type                        | Description                                            |
|---------|----------------------------------|--------------------------------------------------------|
| **id**  | UUID (native, PG_UUID(as_uuid=True))  | Unique identifier for the user.                         |
| **email** | String (with Email validation) | The user’s email address (unique).                     |
| **hashed_password** | String           | Hashed and salted password.                           |
| **registered_at** | DateTime (with timezone) | Timestamp when the user registered.                  |
| _Other fields may be present depending on your FastAPI Users configuration._ |

---

This database design ensures:
- Active URLs have unique short codes.
- Expired URLs maintain a history of URL usage without enforcing uniqueness on short codes, allowing reuse.
- User relationships are maintained via a direct foreign key in the URL tables.
- Essential usage statistics and timestamps (creation, last used, expiration, and moved) are recorded.
