# fastapi-maker

> 🚀 **FastAPI project scaffolding CLI** – Generate production-ready CRUD modules in seconds with explicit field requirements, realistic examples, and clean Swagger documentation.

A powerful command-line tool to bootstrap and scale FastAPI applications with a clean, maintainable architecture:

- Auto-generated **SQLAlchemy models** with `id`, `created_at`, `updated_at`, and custom fields
- **Pydantic v2 DTOs** (Create, Update, Response) with accurate type hints and validation
- **Repository + Service** pattern for separation of concerns
- **Routers** auto-registered in `main.py` with clean path parameters
- **Alembic** pre-configured with models auto-imported
- Environment management via `.env` for example:
```python
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
```
- **Self-documenting OpenAPI specs** with clear required/optional field indicators

Perfect for rapid prototyping, MVP development, or enforcing consistent structure across engineering teams.

---

## ✨ Features

### Core Commands
- `fam init` → Initialize a new FastAPI project with database, Alembic, CORS, logging, and more.
- `fam create <entity> [fields...]` → Generate a full CRUD module with customizable fields
- `fam migrate [-m "message"]` → Auto-generate and apply database migrations with Alembic

### Smart Field Definition Syntax
Define **required** vs **optional** fields using intuitive syntax:
```bash
fam create user *name:str email:str age:int is_active:bool
```
- `*name:str` → **required** field (`name` must be provided)
- `email:str` → **optional** field (`email` can be omitted)

### Supported Field Types
| Type      | SQL Type       | Pydantic Type | Example Value              |
|-----------|----------------|---------------|----------------------------|
| `str`     | `String(255)`  | `str`         | `"John Doe"`               |
| `text`    | `Text`         | `str`         | `"A detailed description…"`|
| `int`     | `Integer`      | `int`         | `42`                       |
| `bigint`  | `BigInteger`   | `int`         | `9007199254740991`         |
| `float`   | `Float`        | `float`       | `3.14`                     |
| `bool`    | `Boolean`      | `bool`       | `true`                     |
| `date`    | `Date`         | `date`        | `"2023-10-05"`             |
| `datetime`| `DateTime`     | `datetime`    | `"2023-10-05T14:30:00"`   |
| `email`   | `String(255)`  | `str`         | `"user@example.com"`       |
| `url`     | `String(255)`  | `str`         | `"https://example.com"`    |

### Auto-Generated Module Structure
```bash
app/api/user/
├── user_model.py        # SQLAlchemy ORM model with nullable rules
├── user_repository.py   # CRUD database operations
├── user_service.py      # Business logic and DTO mapping
├── user_router.py       # FastAPI routes (auto-registered in main.py)
└── dto/
    ├── user_in_dto.py   # Input validation (Create)
    ├── user_update_dto.py # Partial updates (Patch)
    └── user_out_dto.py  # API responses (with id, created_at, updated_at)
```

### Production-Ready Swagger (OpenAPI) Docs
- **Clean route display**: `/users/{user_id}` instead of `/users/user_id`
- **Clear field requirements**: POST endpoint description lists **Required** and **Optional** fields
- **Realistic examples**: Type-specific values (`"user@example.com"`, `42`, `true`) instead of generic placeholders
- **Full visibility**: All fields appear in schema documentation, even optional ones
- **Accurate nullability**: Optional fields correctly marked as nullable in responses

### Safe Data Handling
- **OutDTOs accept `None`** for optional fields → prevents validation errors when DB returns `NULL`
- **Always includes `datetime` import** in OutDTOs for `created_at`/`updated_at`
- **Parameter name consistency** → no more `NameError: name 'xxx_data' is not defined`

---

## 📦 Installation

```bash
pip install fastapi-maker
```

## 🚀 Quick Start

```bash
# Initialize a new project
fam init

# Create a User entity with required name and optional fields
fam create user *name:str email:str age:int is_active:bool

# Create an Animal entity with only a required name
fam create animal *name:str

# Run database migrations
fam migrate -m "Add user and animal tables"

# Start your FastAPI app
python3 -m app.main
```

Then visit `http://localhost:8000/docs` to see your auto-generated, fully-documented API!

---

> 💡 **Pro Tip**: Use `*` prefix to mark fields as required — everything else is optional by default. Your API consumers will thank you for the clarity!