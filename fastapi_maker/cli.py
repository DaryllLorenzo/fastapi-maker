from fastapi_maker.generators.entity_generator import EntityGenerator
import typer
import os
from pathlib import Path
from fastapi_maker.generators.project_initializer import ProjectInitializer

app = typer.Typer(
    name="fam",
    help="FastAPI Maker: Scaffold FastAPI projects (work in progress)."
)

@app.command()
def init():
    """Inicializar la estructura base del proyecto FastAPI"""
    initializer = ProjectInitializer()
    initializer.create_project_structure()


@app.command()
def hello():
    """Just a placeholder to reserve the CLI name."""
    typer.echo("✅ fastapi-maker is reserved! Full version coming soon.")

@app.command()
def create(nombre: str):
    """Crear estructura de carpeta y archivos para una entidad"""
    generator = EntityGenerator(nombre)
    generator.create_structure()


if __name__ == "__main__":
    app()
