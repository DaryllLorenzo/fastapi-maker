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
from fastapi_maker.utils.ruff_executor import RuffExecutor
from fastapi_maker.generators.audit_manager import AuditManager

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
        typer.echo(f" Error: {e}")
        typer.echo(" Asegúrate de instalar las dependencias: pip install questionary")
        raise typer.Exit(1)
    
@app.command()
def lint(
    check: bool = typer.Option(
        False, "--check", "-c", 
        help="Solo detecta problemas sin hacer cambios"
    ),
    fix: bool = typer.Option(
        False, "--fix", "-f", 
        help="Corrige automáticamente problemas de estilo (imports no usados, formato básico)"
    ),
    format: bool = typer.Option(
        False, "--format", "-F", 
        help="Aplica formato al código (indentación, comillas, longitud de línea)"
    ),
    all: bool = typer.Option(
        False, "--all", "-a", 
        help="Ejecuta todas las operaciones: detecta, corrige y formatea"
    )
):
    """
    Ejecuta Ruff linter/formatter en el proyecto.
    
    - Usa --check para solo ver problemas
    - Usa --fix para corregir automáticamente problemas simples
    - Usa --format para aplicar estilo de código
    - Sin opciones: verifica y formatea
    
    Nota: --fix solo corrige problemas superficiales de estilo,
    no modifica la lógica de tu código.
    """
    RuffExecutor.execute(
        check=check,
        fix=fix,
        format_cmd=format,
        all_ops=all
    )

@app.command()
def audit(
    fix: bool = typer.Option(
        False, "--fix", "-f", 
        help="Intenta actualizar dependencias vulnerables automáticamente"
    )
):
    """
    Audita dependencias del proyecto usando pip-audit.
    
    Por defecto solo verifica. Usa --fix para intentar correcciones.
    
    Ejemplos:
        fam audit          # Solo verifica
        fam audit --fix    # Verifica e intenta corregir
    """
    try:  
        auditor = AuditManager(fix_mode=fix)
        if auditor.run_audit():
            raise typer.Exit(code=1) 
    except Exception as e:
        typer.echo(f"Error al ejecutar comando {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
