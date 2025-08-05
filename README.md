# RESTful API for Process Optimization

## 1. Project Overview
This project is a RESTful API server designed to determine the necessity of re-evaluating certain items in a given process. By identifying items with a high probability of recurrence, it aims to enhance productivity by skipping redundant checks and making immediate decisions.

## 2. Key Features
- **Real-time Decision Making**: Receives item data and determines whether re-evaluation is needed based on pre-calculated probability data from a machine learning or statistical batch system.
- **Single and Bulk Processing**: Supports both single-item and multi-item (bulk) processing through dedicated APIs to enhance network efficiency.
- **Data I/O**:
    - **Output (Check)**: An endpoint (`/check`) for querying the evaluation status of an item.
    - **Input (Record)**: An endpoint (`/record`) for a batch system to store and update the calculated probability data in Redis.

## 3. Technology Stack
- **Web Framework**: FastAPI (Asynchronous processing, high performance, automatic API documentation)
- **Database**: Redis (Ensures fast responses with an in-memory database)
- **Logging**: Loguru (Concise logging configuration)
- **Configuration Management**: Pydantic-Settings (Secure configuration management via environment variables and .env files)
- **Server**: Uvicorn (ASGI server)

## 4. Project Structure
```
.
├── logs/                     # Log file storage directory
├── .env.example              # Example environment variable file
├── pyproject.toml            # Project settings and dependency management file
├── config.py                 # Environment variable management using Pydantic-Settings
├── main.py                   # Main entry point for the FastAPI application (includes lifespan, router)
├── models
│   └── defect_model.py       # API request/response and data schema (Pydantic, Redis-OM)
├── db
│   └── redis_config.py       # Redis connection and key generation helper functions
├── routers
│   ├── single_item_router.py # Single item processing API router
│   └── bulk_items_router.py  # Bulk item processing API router
└── utils
    └── logging_config.py     # Loguru logging configuration
```

## 5. Installation and Setup

### 1. Prerequisites
- Python 3.10+
- A running Redis server

### 2. Dependency Installation
This project uses `uv` to manage dependencies. `uv` is an extremely fast Python package installer.

#### Install uv
If you don't have `uv` installed, run one of the following commands in your terminal. For more details, see the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/).
```
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
irm https://astral.sh/uv/install.ps1 | iex
```

#### Sync Dependencies
Run the following command in the project's root directory. It will read the `pyproject.toml` file and install all the required libraries into the virtual environment.
```
uv sync
```

### 3. Environment Variable Setup
Copy the `.env.example` file to create a `.env` file, and update the Redis connection details to match your local environment.
```
# .env file
REDIS_HOST=localhost
REDIS_PORT=6379
```
### 4. Run the API Server
You can run the server in two ways:

1.  **Directly with Uvicorn (Recommended for Development):**
    This method is recommended for development because it gives you direct control over server settings, such as enabling auto-reload with the `--reload` flag. This flag automatically restarts the server whenever you make changes to the code.

    ```bash
    uvicorn retest_optimizer.main:app --host 0.0.0.0 --port 8000 --reload
    ```

2.  **As a Python Module:**
    You can also run the project as a Python module. This is a cleaner command but offers less flexibility, as server settings like the port or reload-mode are configured within the `retest_optimizer/__main__.py` file.

    ```bash
    python -m retest_optimizer
    ```
### 5. API Documentation and Testing
Once the server is running, you can access the automatically generated API documentation in your web browser to explore and test the endpoints.
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
