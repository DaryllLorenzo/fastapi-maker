from pathlib import Path
import typer
import os
import subprocess
import sys

class ProjectInitializer:
    def __init__(self):
        self.base_dir = Path(".")

    def create_project_structure(self):
        """Crear la estructura completa del proyecto"""
        typer.echo("🚀 Inicializando proyecto FastAPI...")

        self._create_env_file()
        self._create_requirements()
        self._create_database_structure()
        self._create_main_app()
        self._create_alembic_structure()
        self._create_config_files()

        typer.echo("✅ Proyecto FastAPI inicializado exitosamente!")
        typer.echo("📝 Next steps:")
        typer.echo("   1. Configura tu DATABASE_URL en .env")
        typer.echo("   2. Ejecuta: pip install -r requirements.txt")
        typer.echo("   3. Ejecuta: alembic upgrade head")

    def _create_env_file(self):
        """Crear archivo .env"""
        env_content = '''# Database
DATABASE_URL=sqlite:///./app.db

# App Settings
DEBUG=true
SECRET_KEY=tu-clave-secreta-aqui-cambiar-en-produccion
API_V1_STR=/api/v1

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
'''
        env_file = self.base_dir / ".env"
        env_file.write_text(env_content)
        typer.echo("📄 Creando archivo: .env")

    def _create_requirements(self):
        """Crear requirements.txt"""
        requirements_content = '''fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
alembic>=1.12.0
python-dotenv>=1.0.0
python-multipart>=0.0.6
pydantic>=2.0.0
psycopg2-binary>=2.9.0  # Para PostgreSQL
# mysqlclient>=2.0.0    # Para MySQL
'''
        requirements_file = self.base_dir / "requirements.txt"
        requirements_file.write_text(requirements_content)
        typer.echo("📄 Creando archivo: requirements.txt")

    def _create_database_structure(self):
        """Crear estructura de base de datos"""
        db_dir = self.base_dir / "db"
        db_dir.mkdir(exist_ok=True)
        typer.echo("📁 Creando carpeta: db/")

        # database.py - Configuración principal de BD
        database_content = '''from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependencia para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''
        database_file = db_dir / "database.py"
        database_file.write_text(database_content)
        typer.echo("📄 Creando archivo: db/database.py")

        # base_mixin.py - Clase base para modelos
        base_mixin_content = '''from sqlalchemy import Column, BigInteger, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr

class BaseMixin:
    """Mixin base para todos los modelos con campos comunes"""

    @declared_attr
    def id(cls):
        return Column(BigInteger, primary_key=True, autoincrement=True)

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
'''
        base_mixin_file = db_dir / "base_mixin.py"
        base_mixin_file.write_text(base_mixin_content)
        typer.echo("📄 Creando archivo: db/base_mixin.py")

        # seeders/__init__.py
        seeders_dir = db_dir / "seeders"
        seeders_dir.mkdir(exist_ok=True)
        (seeders_dir / "__init__.py").touch()
        typer.echo("📁 Creando carpeta: db/seeders/")

        # seeders/base_seeder.py
        base_seeder_content = '''from sqlalchemy.orm import Session
from typing import List, Type, Any
import logging

logger = logging.getLogger(__name__)

class BaseSeeder:
    """Clase base para todos los seeders"""

    @property
    def model(self) -> Type:
        """Debe ser implementado por las subclases"""
        raise NotImplementedError("Debes implementar la propiedad 'model'")

    @property
    def data(self) -> List[Any]:
        """Debe ser implementado por las subclases"""
        raise NotImplementedError("Debes implementar la propiedad 'data'")

    def run(self, db: Session) -> None:
        """Ejecuta el seeder"""
        try:
            for item_data in self.data:
                # Verificar si el registro ya existe
                exists = db.query(self.model).filter_by(**item_data).first()
                if not exists:
                    db.add(self.model(**item_data))

            db.commit()
            logger.info(f"✅ Seeder para {self.model.__name__} ejecutado correctamente")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error en seeder para {self.model.__name__}: {e}")
            raise
'''
        base_seeder_file = seeders_dir / "base_seeder.py"
        base_seeder_file.write_text(base_seeder_content)
        typer.echo("📄 Creando archivo: db/seeders/base_seeder.py")

        # seeders/__init__.py con imports
        seeders_init_content = '''from .base_seeder import BaseSeeder

__all__ = ["BaseSeeder"]
'''
        seeders_init_file = seeders_dir / "__init__.py"
        seeders_init_file.write_text(seeders_init_content)

    def _create_main_app(self):
        """Crear archivo principal de FastAPI"""
        main_content = '''from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from db.database import get_db
from db.database import engine, Base

# Importar modelos aquí cuando los crees
# from app.usuarios.usuario_model import Usuario

# Crear tablas
Base.metadata.create_all(bind=engine)

load_dotenv()

app = FastAPI(
    title="FastAPI App",
    description="API generada con FastAPI Maker",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "¡Bienvenido a FastAPI!"}

@app.get("/health")
def health_check(db=Depends(get_db)):
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
'''
        main_file = self.base_dir / "main.py"
        main_file.write_text(main_content)
        typer.echo("📄 Creando archivo: main.py")

    def _find_venv_python(self) -> Path:
        """Busca el ejecutable de Python dentro del entorno virtual en el proyecto."""
        possible_names = [".venv", "venv", "env"]
        for name in possible_names:
            venv_path = self.base_dir / name
            if venv_path.exists():
                if sys.platform == "win32":
                    python_exe = venv_path / "Scripts" / "python.exe"
                else:
                    python_exe = venv_path / "bin" / "python"
                if python_exe.exists():
                    return python_exe
        # Si no se encuentra, usar el Python actual (asumiendo que ya está activado)
        return Path(sys.executable)

    def _create_alembic_structure(self):
        """Inicializa Alembic usando `alembic init` desde el entorno virtual."""
        typer.echo("⚙️  Inicializando Alembic con `alembic init`...")

        python_exe = self._find_venv_python()
        typer.echo(f"🐍 Usando Python: {python_exe}")

        # Verificar que Alembic esté instalado
        try:
            subprocess.run(
                [str(python_exe), "-c", "import alembic"],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            typer.echo("⚠️  Alembic no está instalado. Asegúrate de ejecutar `pip install -r requirements.txt` primero.")
            typer.echo("   Creando estructura manual como fallback...")
            self._create_alembic_structure_manual()
            return

        alembic_dir = self.base_dir / "alembic"
        if alembic_dir.exists():
            typer.echo("⚠️  La carpeta 'alembic/' ya existe. Saltando `alembic init`.")
        else:
            try:
                subprocess.run(
                    [str(python_exe), "-m", "alembic", "init", "alembic"],
                    cwd=self.base_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
                typer.echo("✅ `alembic init` ejecutado exitosamente.")
            except subprocess.CalledProcessError as e:
                typer.echo(f"❌ Error al ejecutar `alembic init`: {e.stderr}")
                typer.echo("   Creando estructura manual como fallback...")
                self._create_alembic_structure_manual()
                return

        # Personalizar los archivos clave
        self._customize_alembic_files()

    def _customize_alembic_files(self):
        """Sobrescribe alembic.ini y alembic/env.py con configuración personalizada."""
        # alembic.ini
        alembic_ini_content = '''[alembic]
script_location = alembic
sqlalchemy.url = ${DATABASE_URL}

[loggers]
keys = root

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'''
        (self.base_dir / "alembic.ini").write_text(alembic_ini_content)
        typer.echo("📄 Personalizando: alembic.ini")

        # alembic/env.py
        env_py_content = '''from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from dotenv import load_dotenv

# Añadir el directorio raíz al path de Python
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from db.database import Base
target_metadata = Base.metadata

def get_url():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL no está definida en las variables de entorno")
    return database_url

def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    url = get_url()
    connectable = engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
        (self.base_dir / "alembic" / "env.py").write_text(env_py_content)
        typer.echo("📄 Personalizando: alembic/env.py")

    def _create_alembic_structure_manual(self):
        """Versión manual (tu implementación original) por si falla `alembic init`."""
        alembic_ini_content = '''[alembic]
script_location = alembic
sqlalchemy.url = ${DATABASE_URL}

[loggers]
keys = root

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'''
        alembic_ini_file = self.base_dir / "alembic.ini"
        alembic_ini_file.write_text(alembic_ini_content)
        typer.echo("📄 Creando archivo: alembic.ini")

        alembic_dir = self.base_dir / "alembic"
        alembic_dir.mkdir(exist_ok=True)
        typer.echo("📁 Creando carpeta: alembic/")

        versions_dir = alembic_dir / "versions"
        versions_dir.mkdir(exist_ok=True)
        typer.echo("📁 Creando carpeta: alembic/versions/")

        env_py_content = '''from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from dotenv import load_dotenv

# Añadir el directorio raíz al path de Python
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from db.database import Base
# Importa tus modelos aquí para que Alembic los detecte
# from app.usuarios.usuario_model import Usuario

target_metadata = Base.metadata

def get_url():
    """Obtener URL de base de datos desde variable de entorno"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL no está definida en las variables de entorno")
    return database_url

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Obtener la URL de la base de datos
    url = get_url()

    # Configurar el engine
    connectable = engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
        env_py_file = alembic_dir / "env.py"
        env_py_file.write_text(env_py_content)
        typer.echo("📄 Creando archivo: alembic/env.py")

        script_mako_content = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''
        script_mako_file = alembic_dir / "script.py.mako"
        script_mako_file.write_text(script_mako_content)
        typer.echo("📄 Creando archivo: alembic/script.py.mako")

    def _create_config_files(self):
        """Crear archivos de configuración adicionales"""
        # .gitignore
        gitignore_content = '''# Environment
.env
.venv
env/

# Database
*.db
*.sqlite3

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Alembic
alembic/versions/*

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
'''
        gitignore_file = self.base_dir / ".gitignore"
        gitignore_file.write_text(gitignore_content)
        typer.echo("📄 Creando archivo: .gitignore")

        # README.md
        readme_content = '''# FastAPI Project

Proyecto generado con FastAPI Maker

## Configuración de Alembic

Asegúrate de que tu variable DATABASE_URL esté definida en el archivo .env:

```env
DATABASE_URL=sqlite:///./app.db```
'''