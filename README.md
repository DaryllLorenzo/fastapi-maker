# fastapi-maker

> 🚀 **FastAPI project scaffolding CLI** – Generate production-ready CRUD modules in seconds with explicit field requirements, realistic examples, clean **offline Swagger documentation**, and database relationships.

A powerful command-line tool to bootstrap and scale FastAPI applications with a clean, maintainable architecture:

- Auto-generated **SQLAlchemy models** with `id`, `created_at`, `updated_at`, and custom fields
- **Pydantic v2 DTOs** (Create, Update, Response) with accurate type hints and validation
- **Repository + Service** pattern for separation of concerns
- **Routers** auto-registered in `main.py` with clean path parameters
- **Database relationships** with interactive setup for One-to-Many, Many-to-Many, and One-to-One
- **Alembic** pre-configured with models auto-imported
- **Offline API Documentation** with Swagger UI and ReDoc (no CDN required)
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
- `fam init` → Initialize a new FastAPI project with database, Alembic, CORS, logging, and **offline documentation**
- `fam create <entity> [fields...]` → Generate a full CRUD module with customizable fields
- `fam relation` → Create relationships between existing entities (One-to-Many, Many-to-Many, One-to-One)
- `fam migrate [-m "message"]` → Auto-generate and apply database migrations with Alembic
- `fam lint [--check|--fix|--format|--all]` → Lint and format code using Ruff (default: check + format)

### 🛡️ Offline API Documentation
- **Zero CDN dependencies** - All Swagger UI and ReDoc assets served locally
- **Privacy-focused** - No external network requests for documentation
- **Fast loading** - Documentation works without internet connection
- **Customizable** - Easy to configure themes and favicons
- **Powered by** [`fastapi-standalone-docs`](https://github.com/ioxiocom/fastapi-standalone-docs) - Visit for advanced configuration options

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

### Database Relationships
Create relationships between entities with an interactive wizard:
```bash
fam relation
```
**Supported relationship types:**
- **One-to-Many**: e.g., User has many Orders
- **Many-to-Many**: e.g., Products belong to multiple Categories
- **One-to-One**: e.g., User has one Profile

**Automatic updates include:**
- SQLAlchemy ForeignKey and relationship() fields
- DTOs with relation fields (`user_id` or `category_ids`)
- Service layer mapping logic
- Association tables for Many-to-Many relationships

### Production-Ready Swagger (OpenAPI) Docs
- **Clean route display**: `/users/{user_id}` instead of `/users/user_id`
- **Clear field requirements**: POST endpoint description lists **Required** and **Optional** fields
- **Realistic examples**: Type-specific values (`"user@example.com"`, `42`, `true`) instead of generic placeholders
- **Full visibility**: All fields appear in schema documentation, even optional ones
- **Accurate nullability**: Optional fields correctly marked as nullable in responses
- **Offline functionality**: Documentation works completely offline using local assets

### Database Support & Migrations
- **Multi-database support**: SQLite, PostgreSQL, and MySQL
- **Auto-database creation**: Automatically creates database if it doesn't exist
- **Smart migrations**: Alembic configured with environment-based settings
- **SQLite compatibility**: Proper handling of autoincrement primary keys

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
# Initialize a new project with offline documentation
fam init

# Create a User entity with required name and optional fields
fam create user *name:str email:str age:int is_active:bool

# Create an Order entity
fam create order *amount:float status:str

# Create a relationship between User and Order (One-to-Many)
fam relation
# Follow the interactive prompts to create a User -> Order relationship

# Run database migrations (auto-creates database if needed)
fam migrate -m "Add user and order tables with relationship"

# Start your FastAPI app with offline documentation
python3 -m app.main
```

Then visit `http://localhost:8000/docs` to see your auto-generated, fully-documented API - **completely offline!**

---

## 🔧 Advanced Configuration

### Offline Documentation Customization
The generated project uses [`fastapi-standalone-docs`](https://github.com/ioxiocom/fastapi-standalone-docs) for offline documentation. You can customize it in `app/main.py`:

```python
from fastapi_standalone_docs import StandaloneDocs

app = FastAPI()

# Basic configuration (included by default)
StandaloneDocs(app=app)

# Advanced configuration
StandaloneDocs(
    app=app,
    redoc_favicon_url="/custom-favicon.png",  # Custom favicon
    swagger_favicon_url="/custom-favicon.png",
    with_google_fonts=True,  # Enable Google Fonts (disabled by default)
)
```

### Database Configuration
Supported database URLs in your `.env` file:
```bash
# SQLite (default)
DATABASE_URL=sqlite:///./app.db

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/mydatabase

# MySQL
DATABASE_URL=mysql://user:password@localhost:3306/mydatabase
```

## 🎯 Use Cases

- **Rapid Prototyping**: Go from idea to working API in minutes
- **MVP Development**: Perfect for startups and hackathons
- **Team Consistency**: Enforce clean architecture across engineering teams
- **Learning FastAPI**: Excellent for understanding FastAPI best practices
- **Production APIs**: Solid foundation for scalable applications
- **Database Modeling**: Build complex data models with relationships easily

## 🤝 Contributing

We welcome contributions! Feel free to:
- Report bugs and suggest features
- Submit pull requests
- Improve documentation
- Share your use cases

## 📄 License

MIT License - feel free to use in commercial projects.

---

> 💡 **Pro Tip**: Use `*` prefix to mark fields as required — everything else is optional by default. Your API consumers will thank you for the clarity!

> 🌐 **Documentation Note**: Your API docs work completely offline thanks to `fastapi-standalone-docs`. Perfect for development in restricted environments or when privacy matters!

> 🔗 **Relationship Tip**: Use `fam relation` after creating your entities to build connected data models with proper foreign keys and DTOs.