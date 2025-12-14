# ---------------------------------------------------
# Proyecto: fastapi-maker (fam)
# Autor: Daryll Lorenzo Alfonso
# Año: 2025
# Licencia: MIT License
# ---------------------------------------------------

"""
Punto de entrada de la CLI de FastAPI Maker (`fam`).

Comandos disponibles:
- `fam init`: Inicializa la estructura base del proyecto FastAPI.
- `fam create <nombre> [campos...]`: Crea una nueva entidad CRUD con campos personalizados.
- `fam migrate`: Ejecuta migraciones de Alembic.

Ejemplo de uso:
    fam create user *name:str email:str age:int is_active:bool
        → Crea entidad 'User' con 'name' obligatorio y el resto opcionales.
"""

from fastapi_maker.generators.entity_generator import EntityGenerator
import typer
import os
from pathlib import Path
from fastapi_maker.generators.migration_manager import MigrationManager
from fastapi_maker.generators.project_initializer import ProjectInitializer
from fastapi_maker.generators.relation_manager import RelationManager
from fastapi_maker.generators.router_update import RouterUpdater

app = typer.Typer(
    name="fam",
    help="FastAPI Maker: Scaffold FastAPI projects (work in progress)."
)

@app.command()
def init():
    """Inicializa la estructura base del proyecto FastAPI (carpetas, archivos base, etc.)."""
    initializer = ProjectInitializer()
    initializer.create_project_structure()

@app.command()
def create(nombre: str, campos: list[str] = typer.Argument(None, help="Lista de campos en formato: *nombre:tipo (obligatorio) o nombre:tipo (opcional)")):
    """
    Crea una nueva entidad CRUD con campos personalizados.

    - Usa * delante del nombre para marcarlo como obligatorio.
    - Si no se especifican campos, se usa por defecto: *name:str

    Ejemplos:
        fam create user *name:str email:str
        fam create post *title:str content:text published:bool
    """
    # Si no se pasan campos, usamos el valor por defecto
    if campos is None:
        campos = ["*name:str"]
    generator = EntityGenerator(nombre, campos)
    generator.create_structure()

@app.command()
def migrate(message: str = typer.Option(None, "-m", "--message", help="Mensaje descriptivo para la migración de Alembic.")):
    """
    Ejecuta las migraciones pendientes de Alembic en la base de datos.
    Opcionalmente, permite especificar un mensaje para la nueva migración.
    """
    MigrationManager.run_migrations(message=message)

@app.command()
def relation():
    """Genera una relación entre dos entidades existentes."""
    try:
        manager = RelationManager()
        manager.create_relation()
        updater = RouterUpdater()
        updater.update_all_routers_descriptions()
    except ImportError as e:
        typer.echo(f"❌ Error: {e}")
        typer.echo("💡 Asegúrate de instalar las dependencias: pip install questionary")
        raise typer.Exit(1)
    

if __name__ == "__main__":
    app()
