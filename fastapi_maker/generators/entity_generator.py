# generators/entity_generator.py

# ---------------------------------------------------
# Proyecto: fastapi-maker (fam)
# Autor: Daryll Lorenzo Alfonso
# Año: 2025
# Licencia: MIT License
# ---------------------------------------------------

"""
Clase principal que orquesta la generación de una entidad CRUD completa.

Responsabilidades:
- Parsear la especificación de campos (obligatorios vs opcionales).
- Crear la estructura de carpetas y archivos.
- Inyectar el modelo en alembic/env.py.
- Registrar el router en app/main.py.

Flujo típico:
    EntityGenerator("user", ["*name:str", "email:str"]) 
    → genera app/api/user/ con todos los archivos necesarios.
"""

from pathlib import Path
import typer
import re
from typing import List, Dict
from fastapi_maker.templates.entity_templates import get_main_templates, get_dto_templates
from fastapi_maker.utils.sqlalchemy_type_map import SQLALCHEMY_TYPE_MAP


class EntityGenerator:
    def __init__(self, entity_name: str, field_specs: List[str]):
        """
        Inicializa el generador con el nombre de la entidad y la lista de campos.
        
        Args:
            entity_name: Nombre de la entidad (ej: "User")
            field_specs: Lista de strings en formato "*nombre:tipo" u "nombre:tipo"
        """
        self.entity_name = entity_name.lower()
        self.entity_class = entity_name.capitalize()
        self.folder_name = self.entity_name
        self.fields = self._parse_fields(field_specs)

    def _parse_fields(self, field_specs: List[str]) -> List[Dict[str, str]]:
        """
        Convierte la lista de strings de campos en una lista de diccionarios estructurados.
        
        Ejemplo de entrada: ["*name:str", "email:str"]
        Ejemplo de salida: [
            {"name": "name", "type": "str", "required": True},
            {"name": "email", "type": "str", "required": False}
        ]
        """
        fields = []
        valid_types = set(SQLALCHEMY_TYPE_MAP.keys())
        for spec in field_specs:
            # Detectar si el campo es obligatorio (*)
            required = spec.startswith("*")
            name = spec[1:] if required else spec
            
            # Validar formato "nombre:tipo"
            if ":" not in name:
                raise ValueError(f"Formato inválido: '{spec}'. Usa '*nombre:tipo' o 'nombre:tipo'.")
            field_name, dtype = name.split(":", 1)
            
            # Validar nombre de campo (identificador válido en Python)
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", field_name):
                raise ValueError(f"Nombre de campo inválido: '{field_name}'")
            
            # Validar tipo soportado
            if dtype not in valid_types:
                raise ValueError(f"Tipo no soportado: '{dtype}'. Tipos válidos: {sorted(valid_types)}")
            
            fields.append({
                "name": field_name,
                "type": dtype,
                "required": required
            })
        return fields

    def create_structure(self):
        """Orquesta la creación completa de la entidad."""
        main_folder = Path("app") / "api" / Path(self.folder_name)
        main_folder.mkdir(exist_ok=True)
        typer.echo(f" ➤ Creando carpeta: {self.folder_name}")

        self._create_main_files(main_folder)
        self._create_dto_files(main_folder)
        self._add_model_to_alembic_env()
        self._add_router_to_main()

        typer.echo(f" ✅ Entidad '{self.entity_class}' generada e integrada correctamente.")

    def _create_main_files(self, folder: Path):
        """Genera los archivos principales: modelo, repositorio, servicio y router."""
        templates = get_main_templates(self.entity_name, self.fields)
        for filename, content in templates.items():
            (folder / filename).write_text(content, encoding="utf-8")
            typer.echo(f"   ➤ Creando archivo: {filename}")

    def _create_dto_files(self, folder: Path):
        """Genera los archivos DTO (Pydantic) dentro de una subcarpeta 'dto'."""
        dto_folder = folder / "dto"
        dto_folder.mkdir(exist_ok=True)
        typer.echo(f"   ➤ Creando subcarpeta: dto/")

        templates = get_dto_templates(self.entity_name, self.fields)
        for filename, content in templates.items():
            (dto_folder / filename).write_text(content, encoding="utf-8")
            typer.echo(f"   ➤ Creando archivo: dto/{filename}")

    def _add_model_to_alembic_env(self):
        """Añade la importación del modelo a alembic/env.py para que Alembic lo detecte."""
        env_path = Path("alembic") / "env.py"
        if not env_path.exists():
            typer.echo("   ⚠️  alembic/env.py no encontrado. Saltando integración con Alembic.")
            return

        import_line = f"from app.api.{self.folder_name}.{self.entity_name}_model import {self.entity_class}\n"
        content = env_path.read_text(encoding="utf-8")

        # Evitar importaciones duplicadas
        if import_line.strip() in content:
            typer.echo("   ➤ Modelo ya presente en alembic/env.py")
            return

        lines = content.splitlines(keepends=True)
        new_lines = []
        inserted = False

        for line in lines:
            new_lines.append(line)
            if line.strip() == "from app.db.database import Base":
                new_lines.append(import_line)
                inserted = True

        if inserted:
            env_path.write_text("".join(new_lines), encoding="utf-8")
            typer.echo("   ➤ Modelo agregado a alembic/env.py")
        else:
            typer.echo("   ⚠️  No se encontró 'from app.db.database import Base' en alembic/env.py. No se agregó la importación.")

    def _add_router_to_main(self):
        """Registra el router de la entidad en app/main.py."""
        main_path = Path("app") / "main.py"
        if not main_path.exists():
            typer.echo("   ⚠️  app/main.py no encontrado. Saltando registro del router.")
            return

        content = main_path.read_text(encoding="utf-8")

        import_line = f"from app.api.{self.folder_name}.{self.entity_name}_router import router as {self.entity_name}_router\n"
        include_line = f"app.include_router({self.entity_name}_router)\n"

        # Añadir importación si no existe
        if import_line.strip() not in content:
            app_line = "app = FastAPI("
            if app_line in content:
                lines = content.splitlines(keepends=True)
                # Insertar justo antes de la línea `app = FastAPI(...)`
                idx = next(i for i, line in enumerate(lines) if app_line in line)
                lines.insert(idx, import_line)
                content = "".join(lines)
                typer.echo("   ➤ Router importado en app/main.py")

        # Añadir include si no existe
        if include_line.strip() not in content:
            if "if __name__ == \"__main__\":" in content:
                content = content.replace(
                    "if __name__ == \"__main__\":",
                    f"{include_line}\nif __name__ == \"__main__\":"
                )
            else:
                content += f"\n{include_line}"
            main_path.write_text(content, encoding="utf-8")
            typer.echo("   ➤ Router incluido en la aplicación FastAPI")