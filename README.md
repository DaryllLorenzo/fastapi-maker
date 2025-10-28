# fastapi-maker

> 🚀 **FastAPI project scaffolding CLI** – Generate production-ready modules in seconds.

A command-line tool to bootstrap and scale FastAPI applications with clean architecture:
- Auto-generated **SQLAlchemy models** (with timestamps, ID, etc.)
- **Pydantic v2 DTOs** (Create, Update, Response)
- **Repository + Service** pattern
- **Routers** auto-registered in `main.py`
- **Alembic** pre-configured and models auto-imported
- Environment management via `.env`

Perfect for rapid prototyping or enforcing consistent structure across teams.

## ✨ Features

- `fam init` → Initialize a new FastAPI project with database, Alembic, CORS, and more.
- `fam create <entity>` → Generate a full module (e.g., `User`) with: