# Fastapi Boilerplate

A FastAPI-based backend service for the **Fastapi Boilerplate** platform. This application provides RESTful APIs for managing estates, maintenance activities, bills, and resident records.

---

## 🚀 Tech Stack

- **Framework:** FastAPI
- **Language:** Python 3.8+
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Migration Tool:** Alembic
- **Testing:** unittest
- **Authentication:** JWT (JSON Web Tokens)

---

## 📦 Getting Started

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12+
- pip (Python package manager)

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/Smash-Tech-Group/fastapi-boilerplate.git
cd fastapi-boilerplate
```

**2. Create and activate virtual environment**

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Create a `.env` file by copying the sample:

```bash
cp .env.sample .env
```

Update the `.env` file with your configuration:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/em_fast_api
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**5. Set up PostgreSQL database**

```bash
# Access PostgreSQL as root
sudo -u postgres psql
```

```sql
-- Create database user
CREATE USER user WITH PASSWORD 'your_password';

-- Create database
CREATE DATABASE db_fast_api;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE db_fast_api TO user;

-- Exit PostgreSQL
\q
```

**6. Run database migrations**

```bash
# Apply existing migrations
alembic upgrade head
```

```bash
# Apply existing migrations
alembic revision --autogenerate -m "message"
```

```bash
# Apply existing migrations
alembic upgrade head
```

**7. Seed the database (optional)**

```bash
python3 seed.py DB - Sheet1.csv
```

**8. Start the server**

```bash
python main.py
```

The API will be available at `http://localhost:8000`

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🛠️ Available Commands

| Command | Description |
|---------|-------------|
| `python main.py` | Start the FastAPI development server |
| `alembic revision --autogenerate -m "message"` | Generate new migration |
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Rollback last migration |
| `python3 seed.py` | Populate database with dummy data |
| `python -m unittest tests/v1/test_*.py` | Run specific test file |

---

## 🗄️ Database Management

### Creating Migrations

When you add new models or modify existing ones:

**1. Ensure your model is imported**

Import your model in `api/v1/models/__init__.py`:

```python
from .your_model import YourModel
```

**2. Generate migration**

```bash
alembic revision --autogenerate -m "add your_table"
```

**3. Apply migration**

```bash
alembic upgrade head
```

### Migration Troubleshooting

If you encounter this error:
```
ERROR [alembic.util.messaging] Target database is not up to date.
```

**Solution:**
```bash
# First, update the database
alembic upgrade head

# Then generate your migration
alembic revision --autogenerate -m "your migration message"
```

---

## 🧪 Testing

This project uses Python's `unittest` framework.

**Run specific tests:**

```bash
# Test login endpoint
python -m unittest tests/v1/test_login.py

# Test signup endpoint
python -m unittest tests/v1/test_signup.py
```

**Important:** Always test your endpoints and models before pushing code.
s
---

## 📁 Project Structure

```
fastapi-boilerplate/
├── alembic/                     # Database migrations
│   ├── versions/                # Migration version files
│   └── env.py                   # Alembic environment configuration
├── api/
│   ├── core/                    # Core application components
│   │   ├── base/                # Base classes and models
│   │   ├── dependencies/        # Dependency injection
│   │   └── responses.py         # Standard API responses
│   ├── db/                      # Database configuration
│   │   └── database.py          # Database connection and session
│   ├── loggers/                 # Logging configuration
│   ├── utils/                   # Utility functions and helpers
│   │   ├── config.py            # Application configuration
│   │   ├── constants.py         # Application constants
│   │   ├── db_validators.py    # Database validation utilities
│   │   ├── files.py             # File handling utilities
│   │   ├── helpers.py           # General helper functions
│   │   ├── json_validator.py   # JSON validation
│   │   ├── log_streamer.py     # Log streaming utilities
│   │   ├── mime_types.py        # MIME type definitions
│   │   ├── minio_service.py    # MinIO object storage service
│   │   ├── pagination.py        # Pagination utilities
│   │   ├── rate_limiter.py     # Rate limiting middleware
│   │   ├── settings.py          # Application settings
│   │   ├── success_response.py # Success response formatters
│   │   ├── tweet_service.py    # Tweet/social media service
│   │   └── urllib_request.py   # HTTP request utilities
│   └── v1/                      # API version 1
│       ├── models/              # SQLAlchemy ORM models
│       │   └── __init__.py      # Import all models here
│       ├── routes/              # API route handlers
│       │   └── __init__.py      # Router configuration
│       ├── schemas/             # Pydantic request/response schemas
│       └── services/            # Business logic layer
├── logs/                        # Application logs
├── media/                       # Media files
│   └── uploads/                 # User uploaded files
├── node_modules/                # Node.js dependencies (if any)
├── qa_tests/                    # QA test suite
├── tests/                       # Unit and integration tests
│   ├── v1/                      # Version 1 API tests
│   │   ├── test_login.py
│   │   └── test_signup.py
│   ├── conftest.py              # Pytest configuration and fixtures
│   ├── database.py              # Test database setup
│   └── run_all_test.py          # Test runner script
├── tmp/                         # Temporary files
├── venv/                        # Virtual environment (git-ignored)
├── .env                         # Environment variables (git-ignored)
├── .env.sample                  # Environment variables template
├── alembic.ini                  # Alembic configuration
├── CountryPricingTable.py       # Country pricing utilities
├── LICENSE                      # Apache 2.0 License
├── main.py                      # Application entry point
├── package.json                 # Node.js package configuration
├── package-lock.json            # Node.js dependency lock
├── README.md                    # Project documentation
├── release.config.cjs           # Release configuration
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup configuration
└── update_api_status.py         # API status update script
```

---

## 🔀 Adding New Features

### Adding New Models

**1. Create your model file** in `api/v1/models/your_model.py`

**2. Import it** in `api/v1/models/__init__.py`:
```python
from .your_model import YourModel
```

**3. Generate and apply migration:**
```bash
alembic revision --autogenerate -m "add your_model"
alembic upgrade head
```

### Adding New Routes

**1. Check existing route files** in `api/v1/routes/`

If a related file exists, add your route there. Otherwise, create a new file.

**2. Create route file** (e.g., `api/v1/routes/yourRoute.py`):

```python
from fastapi import APIRouter

router = APIRouter(
    prefix="/estates",  # Don't include /api/v1
    tags=["yourRoute"]
)

@router.get("/")
async def get_estates():
    return {"message": "List of estates"}
```

**3. Register the router** in `api/v1/routes/__init__.py`:

```python
from .estates import router as estates_router

api_version_one.include_router(estates_router)
```

> **Note:** Don't include the base prefix `/api/v1` in your router, as it's already included in the `api_version_one` router.

---

## 👥 Contributing

We follow the **Git Flow** workflow for branch management and collaboration.

### Branch Structure

- **`main`** - Production-ready code
- **`develop`** - Integration branch for features
- **`feature/*`** - New features
- **`hotfix/*`** - Urgent production fixes
- **`release/*`** - Release preparation

### Git Flow Workflow

**1. Start a new feature**
```bash
# Create and switch to a new feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

**2. Work on your feature**
- Write clean, maintainable code
- Add tests for new functionality
- Test endpoints before committing
- Follow the coding guidelines below

**3. Run tests**
```bash
python -m unittest discover tests/
```

**4. Commit your changes**
```bash
# Use conventional commit messages
git add .
git commit -m "feat: add Fastapi Boilerplate endpoints"
```

**Commit message conventions:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

**5. Push migrations and create Pull Request**
```bash
# Push your feature branch (including migrations)
git push origin feature/your-feature-name
```

Then create a Pull Request from `feature/your-feature-name` → `develop`

**6. After PR approval and merge**
```bash
# Delete the local feature branch
git checkout develop
git pull origin develop
git branch -d feature/your-feature-name
```

### Hotfix Workflow

For urgent production fixes:

```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/fix-critical-bug

# Make your fix and test thoroughly
python -m unittest discover tests/

# Commit and push
git commit -m "fix: resolve critical authentication bug"
git push origin hotfix/fix-critical-bug
```

Create PR to **both** `main` and `develop`

### Release Workflow

When preparing a release:

```bash
# Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0

# Update version numbers, changelog, etc.
# Test thoroughly

# Merge to main
git checkout main
git merge release/v1.2.0
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin main --tags

# Merge back to develop
git checkout develop
git merge release/v1.2.0
git push origin develop

# Delete release branch
git branch -d release/v1.2.0
```

---

## ✅ Coding Guidelines

### General Principles
- Follow PEP 8 style guide for Python code
- Write descriptive variable and function names
- Add docstrings to all functions and classes
- Keep functions small and focused
- Write tests for all new endpoints and services

### Best Practices
- Always test endpoints before pushing
- Include Alembic migrations in your commits
- Use Pydantic schemas for request/response validation
- Implement proper error handling with appropriate HTTP status codes
- Use dependency injection for database sessions
- Keep business logic in service layer, not in routes

### Code Structure
- **Models:** SQLAlchemy ORM models (`api/v1/models/`)
- **Schemas:** Pydantic models for validation (`api/v1/schemas/`)
- **Routes:** API endpoints (`api/v1/routes/`)
- **Services:** Business logic (`api/v1/services/`)
- **Tests:** Unit tests (`tests/v1/`)

---

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `main.py` | Application entry point and FastAPI configuration |
| `alembic.ini` | Alembic migration configuration |
| `requirements.txt` | Python package dependencies |
| `.env` | Environment variables (git-ignored) |
| `.env.sample` | Template for required environment variables |
| `seed.py` | Database seeding script |

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Important Reminders

- ✅ Always test your endpoints before pushing
- ✅ Include Alembic migrations in your commits
- ✅ Update `.env.sample` when adding new environment variables
- ✅ Import new models in `api/v1/models/__init__.py`
- ✅ Follow the Git Flow workflow for all contributions
- ✅ Run `alembic upgrade head` before generating new migrations
