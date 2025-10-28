# generators/entity_generator.py

from pathlib import Path
import typer
import re
from fastapi_maker.templates.entity_templates import get_main_templates, get_dto_templates

class EntityGenerator:
    def __init__(self, entity_name: str):
        self.entity_name = entity_name.lower()
        self.entity_class = entity_name.capitalize()
        self.folder_name = self.entity_class  # Ej: "User"

    def create_structure(self):
        """Crear la estructura completa de la entidad e integrarla en el proyecto"""
        main_folder = Path(self.folder_name)
        main_folder.mkdir(exist_ok=True)
        typer.echo(f"📁 Creando carpeta: {self.folder_name}")

        # 1. Archivos principales (modelo, repo, service, router)
        self._create_main_files(main_folder)

        # 2. DTOs
        self._create_dto_files(main_folder)

        # 3. Integrar modelo en Alembic
        self._add_model_to_alembic_env()

        # 4. Integrar router en main.py
        self._add_router_to_main()

        typer.echo(f"✅ Entidad '{self.entity_class}' generada e integrada.")

    def _create_main_files(self, folder: Path):
        templates = get_main_templates(self.entity_name)
        for filename, content in templates.items():
            (folder / filename).write_text(content, encoding="utf-8")
            typer.echo(f"📄 Creando archivo: {filename}")

    def _create_dto_files(self, folder: Path):
        dto_folder = folder / "dto"
        dto_folder.mkdir(exist_ok=True)
        typer.echo(f"📁 Creando subcarpeta: dto/")

        templates = get_dto_templates(self.entity_name)
        for filename, content in templates.items():
            (dto_folder / filename).write_text(content, encoding="utf-8")
            typer.echo(f"📄 Creando archivo: dto/{filename}")

    def _add_model_to_alembic_env(self):
        env_path = Path("alembic") / "env.py"
        if not env_path.exists():
            typer.echo("⚠️  alembic/env.py no encontrado. Saltando.")
            return
    
        import_line = f"from {self.folder_name}.{self.entity_name}_model import {self.entity_class}\n"
        content = env_path.read_text(encoding="utf-8")
    
        if import_line.strip() in content:
            typer.echo("✅ Modelo ya presente en alembic/env.py")
            return
    
        # Buscar la línea "from db.database import Base"
        # e insertar justo después de ella (antes de target_metadata)
        lines = content.splitlines(keepends=True)
        new_lines = []
        inserted = False
    
        for i, line in enumerate(lines):
            new_lines.append(line)
            if line.strip() == "from db.database import Base":
                # Insertar la importación del modelo en la siguiente línea
                new_lines.append(import_line)
                inserted = True
    
        if inserted:
            env_path.write_text("".join(new_lines), encoding="utf-8")
            typer.echo("🔧 Modelo agregado a alembic/env.py")
        else:
            typer.echo("⚠️  No se encontró 'from db.database import Base' en alembic/env.py. No se agregó la importación.")

    def _add_router_to_main(self):
        main_path = Path("main.py")
        if not main_path.exists():
            typer.echo("⚠️  main.py no encontrado. Saltando.")
            return

        content = main_path.read_text(encoding="utf-8")

        import_line = f"from {self.folder_name}.{self.entity_name}_router import router as {self.entity_name}_router\n"
        include_line = f"app.include_router({self.entity_name}_router)\n"

        # Añadir importación si no existe
        if import_line.strip() not in content:
            app_line = "app = FastAPI("
            if app_line in content:
                lines = content.splitlines(keepends=True)
                idx = next(i for i, line in enumerate(lines) if app_line in line)
                lines.insert(idx, import_line)
                content = "".join(lines)
                typer.echo("🔧 Router importado en main.py")

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
            typer.echo("🔌 Router incluido en la aplicación FastAPI")