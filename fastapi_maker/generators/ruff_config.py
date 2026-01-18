"""
Generador de configuración de Ruff para FastAPI Maker.
"""
from pathlib import Path
import typer

class RuffConfigGenerator:
    """Genera y maneja la configuración de Ruff."""
    
    @staticmethod
    def generate_ruff_config():
        """
        Genera una configuración básica de Ruff en pyproject.toml.
        """
        config_path = Path("pyproject.toml")
        
        # Configuración simple y funcional de Ruff
        config_content = '''[tool.ruff]
# Mismo que Black
line-length = 88
indent-width = 4

# Asumir Python 3.11 para FastAPI
target-version = "py311"

# Excluir directorios comunes
exclude = [
    ".git",
    "__pycache__",
    ".env",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    "migrations",
    "alembic",
    "tests/__pycache__",
]

[tool.ruff.lint]
# Reglas básicas de Ruff
select = ["E", "F", "I", "B", "UP"]

# Reglas a ignorar
ignore = [
    "E501",  # line too long - manejado por formatter
    "B008",  # do not perform function calls in argument defaults
]

# Ignorar imports no usados en __init__.py
per-file-ignores = { "__init__.py" = ["F401"] }

[tool.ruff.lint.isort]
# Configurar isort para FastAPI
known-first-party = ["app", "models", "schemas", "routers", "crud"]

[tool.ruff.format]
# Como Black
quote-style = "double"
indent-style = "space"
'''
        
        try:
            if config_path.exists():
                typer.echo("pyproject.toml ya existe. Actualizando configuracion de Ruff...")
                # Leer contenido existente
                with open(config_path, 'r', encoding='utf-8') as f:
                    existing = f.read()
                
                # Verificar si ya tiene configuración de ruff
                if "[tool.ruff]" in existing:
                    typer.echo("Configuracion de Ruff ya existe en pyproject.toml")
                    return
                
                # Agregar configuración al final
                with open(config_path, 'a', encoding='utf-8') as f:
                    f.write("\n\n" + config_content)
                typer.echo("Configuracion de Ruff agregada a pyproject.toml")
            else:
                # Crear nuevo archivo
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(config_content)
                typer.echo("Configuracion de Ruff creada en pyproject.toml")
            
            # Crear .ruff-ignore si no existe
            RuffConfigGenerator.create_ruff_ignore_file()
            
            typer.echo("\nConfiguracion aplicada:")
            typer.echo("- Line-length: 88")
            typer.echo("- Indent-width: 4")
            typer.echo("- Reglas: E, F, I, B, UP")
            typer.echo("- Formato: estilo Black")
            
        except Exception as e:
            typer.echo(f"Error: {e}")
    
    @staticmethod
    def create_ruff_ignore_file():
        """Crea el archivo .ruff-ignore."""
        ignore_path = Path(".ruff-ignore")
        if not ignore_path.exists():
            ignore_content = '''# Archivos a ignorar por Ruff
/alembic/versions/*
/migrations/versions/*
*.pyc
__pycache__/
'''
            with open(ignore_path, 'w', encoding='utf-8') as f:
                f.write(ignore_content)