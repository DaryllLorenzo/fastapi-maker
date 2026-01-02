"""
Generador de configuración de Ruff para FastAPI Maker.
"""
from pathlib import Path
import toml
import typer

class RuffConfigGenerator:
    """Genera y maneja la configuración de Ruff."""
    
    @staticmethod
    def generate_ruff_config():
        """
        Genera una configuración básica de Ruff en pyproject.toml.
        Si ya existe, actualiza la sección de ruff.
        """
        config_path = Path("pyproject.toml")
        
        # Configuración básica de Ruff
        ruff_config = {
            "tool": {
                "ruff": {
                    # Configuración de linting
                    "lint": {
                        "select": [
                            "E",   # pycodestyle errors
                            "W",   # pycodestyle warnings
                            "F",   # pyflakes
                            "I",   # isort (organización de imports)
                            "B",   # flake8-bugbear
                            "C4",  # flake8-comprehensions
                            "UP",  # pyupgrade
                            "N",   # pep8-naming
                            "PL",  # Pylint
                            "RUF", # Reglas específicas de Ruff
                        ],
                        "ignore": [
                            "E501",  # line too long (manejado por formatter)
                            "B008",  # do not perform function calls in argument defaults
                            "PLR0913",  # Too many arguments
                            "PLR0915",  # Too many statements
                            "PLR2004",  # Magic value used in comparison
                        ],
                        "exclude": [
                            ".git",
                            "__pycache__",
                            ".env",
                            ".venv",
                            "venv",
                            "env",
                            ".mypy_cache",
                            ".pytest_cache",
                            "migrations",
                            "alembic",
                            "tests/__pycache__",
                        ],
                        # Configuraciones específicas
                        "per-file-ignores": {
                            "__init__.py": ["F401"],  # unused import en __init__
                        },
                    },
                    # Configuración de formateo
                    "format": {
                        "indent-style": "space",
                        "indent-width": 4,
                        "line-length": 88,
                        "quote-style": "double",
                    },
                    # Configuración de isort (organización de imports)
                    "lint.isort": {
                        "known-first-party": ["app", "models", "schemas", "routers", "crud"],
                        "lines-after-imports": 2,
                    },
                    # Configuración específica para FastAPI
                    "lint.flake8-pytest-style": {
                        "fixture-parentheses": False,
                    },
                }
            }
        }
        
        try:
            if config_path.exists():
                # Leer configuración existente
                with open(config_path, 'r', encoding='utf-8') as f:
                    existing_config = toml.load(f)
                
                # Actualizar o agregar sección ruff
                if "tool" not in existing_config:
                    existing_config["tool"] = {}
                
                existing_config["tool"]["ruff"] = ruff_config["tool"]["ruff"]
                
                # Escribir configuración actualizada
                with open(config_path, 'w', encoding='utf-8') as f:
                    toml.dump(existing_config, f)
                
                typer.echo(f"✅ Configuración de Ruff actualizada en {config_path}")
            else:
                # Crear nuevo archivo con configuración
                with open(config_path, 'w', encoding='utf-8') as f:
                    toml.dump(ruff_config, f)
                
                typer.echo(f"✅ Configuración de Ruff creada en {config_path}")
            
            # Crear archivo .ruff-ignore si no existe
            ruff_ignore_path = Path(".ruff-ignore")
            if not ruff_ignore_path.exists():
                RuffConfigGenerator.create_ruff_ignore_file(ruff_ignore_path)
            
            RuffConfigGenerator.print_config_summary()
            
        except Exception as e:
            typer.echo(f"❌ Error generando configuración de Ruff: {e}")
            raise
    
    @staticmethod
    def create_ruff_ignore_file(filepath: Path):
        """Crea el archivo .ruff-ignore."""
        ignore_content = """# Archivos y directorios a ignorar por Ruff
/alembic/versions/*
/migrations/versions/*
**/__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ignore_content)
        typer.echo(f"✅ Archivo .ruff-ignore creado")
    
    @staticmethod
    def print_config_summary():
        """Muestra un resumen de la configuración aplicada."""
        typer.echo("\n📋 Configuración de Ruff aplicada:")
        typer.echo("   • Selección de reglas: E, W, F, I, B, C4, UP, N, PL, RUF")
        typer.echo("   • Longitud de línea: 88 caracteres")
        typer.echo("   • Indentación: 4 espacios")
        typer.echo("   • Comillas: dobles")
        typer.echo("   • Excluye: migraciones, entornos virtuales, caches")
    
    @staticmethod
    def validate_ruff_installed():
        """Verifica si ruff está instalado."""
        try:
            import ruff
            return True
        except ImportError:
            return False