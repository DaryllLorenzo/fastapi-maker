# ---------------------------------------------------
# Project: fastapi-maker (fam)
# Author: Daryll Lorenzo Alfonso
# Year: 2025
# License: MIT License
# ---------------------------------------------------

import typer
from pathlib import Path
import questionary
from typing import List
from enum import Enum
from dataclasses import dataclass

from fastapi_maker.utils.code_editor import CodeEditor
from fastapi_maker.templates.relation_templates import (
    get_foreign_key_template,
    get_relationship_template,
    get_association_table_template,
    get_out_dto_relation_field,
    get_in_dto_relation_field,
    get_model_to_dto_logic,
    get_repository_method,
    get_many_to_many_service_methods,
    get_get_by_ids_method,
    get_create_method_with_relation_filter,
    get_create_method_with_many_to_many_relations
)


class RelationType(Enum):
    ONE_TO_MANY = "one-to-many"
    MANY_TO_MANY = "many-to-many"
    ONE_TO_ONE = "one-to-one"


@dataclass
class RelationshipConfig:
    origin_entity: str
    target_entity: str
    relation_type: RelationType
    foreign_key_in_target: bool = True
    is_list_in_origin: bool = False
    is_list_in_target: bool = False


class RelationManager:
    def __init__(self):
        self.base_path = Path("app/api")
        if not self.base_path.exists():
            typer.echo("  No se encontró la carpeta app/api. ¿Has inicializado el proyecto?")
            raise typer.Exit(1)
        self.editor = CodeEditor()
        self.entities = self._get_existing_entities()

    def _get_existing_entities(self) -> List[str]:
        return [
            d.name for d in self.base_path.iterdir()
            if d.is_dir() and (d / f"{d.name}_model.py").exists()
        ]

    def create_relation(self):
        if len(self.entities) < 2:
            typer.echo("  Necesitas al menos dos entidades para crear una relación.")
            return

        typer.echo("\n  Creando relación entre entidades")
        typer.echo("=" * 40)

        origin = self._select_entity("Selecciona la entidad de ORIGEN:", self.entities)
        relation_type = self._select_relation_type()
        available_targets = [e for e in self.entities if e != origin]
        target = self._select_entity("Selecciona la entidad de DESTINO:", available_targets)

        config = self._configure_relationship(origin, target, relation_type)
        self._confirm_relationship(config)
        self._generate_relationship(config)

    def _select_entity(self, message: str, choices: List[str]) -> str:
        choice = questionary.select(message=message, choices=choices, use_shortcuts=True, qmark="➤", pointer="→").ask()
        if choice is None:
            typer.echo("\n  Operación cancelada por el usuario.")
            raise typer.Exit(0)
        return choice

    def _select_relation_type(self) -> RelationType:
        choices = [
            {"name": "Uno a Muchos (One-to-Many)", "value": RelationType.ONE_TO_MANY},
            {"name": "Muchos a Muchos (Many-to-Many)", "value": RelationType.MANY_TO_MANY},
            {"name": "Uno a Uno (One-to-One)", "value": RelationType.ONE_TO_ONE},
        ]
        choice = questionary.select(
            message="Selecciona el tipo de relación:",
            choices=[c["name"] for c in choices],
            use_shortcuts=True,
            qmark="➤",
            pointer="→"
        ).ask()
        if choice is None:
            typer.echo("\n  Operación cancelada.")
            raise typer.Exit(0)
        return next(c["value"] for c in choices if c["name"] == choice)

    def _configure_relationship(self, origin: str, target: str, relation_type: RelationType) -> RelationshipConfig:
        if relation_type == RelationType.ONE_TO_MANY:
            return RelationshipConfig(origin, target, relation_type,
                                      foreign_key_in_target=True,
                                      is_list_in_origin=True)
        elif relation_type == RelationType.MANY_TO_MANY:
            list_choice = questionary.select(
                message=f"¿Qué entidad debe tener la lista de IDs en su DTO?",
                choices=[
                    f"{origin.capitalize()} (origen) - tendrá {target}_ids en su DTO",
                    f"{target.capitalize()} (destino) - tendrá {origin}_ids en su DTO"
                ],
                default=f"{origin.capitalize()} (origen) - tendrá {target}_ids en su DTO",
                qmark="➤",
                pointer="→"
            ).ask()
            if list_choice is None:
                typer.echo("\n  Operación cancelada.")
                raise typer.Exit(0)
            if "origen" in list_choice.lower():
                return RelationshipConfig(origin, target, relation_type,
                                          foreign_key_in_target=False,
                                          is_list_in_origin=True,
                                          is_list_in_target=False)
            else:
                return RelationshipConfig(origin, target, relation_type,
                                          foreign_key_in_target=False,
                                          is_list_in_origin=False,
                                          is_list_in_target=True)
        elif relation_type == RelationType.ONE_TO_ONE:
            side = questionary.select(
                message="¿Qué entidad debe tener la foreign key?",
                choices=[f"{origin.capitalize()} (origen)", f"{target.capitalize()} (destino)"],
                default=f"{origin.capitalize()} (origen)",
                qmark="➤",
                pointer="→"
            ).ask()
            if side is None:
                typer.echo("\n  Operación cancelada.")
                raise typer.Exit(0)
            foreign_key_in_target = "destino" in side.lower()
            return RelationshipConfig(origin, target, relation_type,
                                      foreign_key_in_target=foreign_key_in_target)

    def _confirm_relationship(self, config: RelationshipConfig):
        typer.echo("\n  Resumen de la relación:")
        typer.echo("=" * 40)
        typer.echo(f"  Entidad origen: {config.origin_entity}")
        typer.echo(f"  Entidad destino: {config.target_entity}")
        typer.echo(f"  Tipo de relación: {config.relation_type.value}")

        if config.relation_type == RelationType.MANY_TO_MANY:
            typer.echo(f"  Tabla de asociación: {config.origin_entity}_{config.target_entity}")
            if config.is_list_in_origin:
                typer.echo(f"  Solo {config.origin_entity} tendrá {config.target_entity}_ids en su DTO")
            else:
                typer.echo(f"  Solo {config.target_entity} tendrá {config.origin_entity}_ids en su DTO")
        elif config.relation_type in [RelationType.ONE_TO_MANY, RelationType.ONE_TO_ONE]:
            fk_entity = config.target_entity if config.foreign_key_in_target else config.origin_entity
            fk_field = f"{config.origin_entity}_id" if config.foreign_key_in_target else f"{config.target_entity}_id"
            typer.echo(f"  Foreign key en: {fk_entity}_model.py")
            typer.echo(f"  Campo: {fk_field}")
        
        if config.is_list_in_origin:
            typer.echo(f"  {config.origin_entity}_out_dto tendrá: {config.target_entity}_ids: List[int]")
        if config.is_list_in_target:
            typer.echo(f"  {config.target_entity}_out_dto tendrá: {config.origin_entity}_ids: List[int]")

        typer.echo("=" * 40)
        if not questionary.confirm("¿Generar la relación con estas configuraciones?", default=True).ask():
            typer.echo("\n  Operación cancelada.")
            raise typer.Exit(0)

    def _generate_relationship(self, config: RelationshipConfig):
        typer.echo(f"\n  Generando relación {config.relation_type.value}...")
        try:
            self._ensure_sqlalchemy_imports(config.origin_entity)
            self._ensure_sqlalchemy_imports(config.target_entity)

            if config.relation_type == RelationType.ONE_TO_MANY:
                self._generate_one_to_many(config)
            elif config.relation_type == RelationType.MANY_TO_MANY:
                self._generate_many_to_many(config)
            elif config.relation_type == RelationType.ONE_TO_ONE:
                self._generate_one_to_one(config)

            self._update_dtos_for_relationship(config)
            self._update_services_for_relationship(config)

            typer.echo(f"\n  Relación {config.relation_type.value} generada exitosamente!")
            typer.echo(f"   Entre: {config.origin_entity} ↔ {config.target_entity}")
            self._show_next_steps(config)
        except Exception as e:
            typer.echo(f"\n  Error generando relación: {str(e)}")
            import traceback
            traceback.print_exc()
            raise typer.Exit(1)

    def _show_next_steps(self, config: RelationshipConfig):
        typer.echo("\n  Próximos pasos:")
        typer.echo(f"   1. Ejecutar: fam migrate -m 'Agregar relación entre {config.origin_entity} y {config.target_entity}'")
        typer.echo("   2. Revisar el código generado en las carpetas de entidades")

    # --- Métodos auxiliares de edición ---
    def _ensure_sqlalchemy_imports(self, entity_name: str):
        model_path = self.base_path / entity_name / f"{entity_name}_model.py"
        if not model_path.exists():
            raise FileNotFoundError(f"Archivo de modelo no encontrado para {entity_name}")
        lines = self.editor.read_lines(model_path)
        content = "\n".join(lines)
        if "ForeignKey" not in content:
            lines = self._add_foreign_key_import(lines)
        if "relationship" not in content:
            lines = self._add_relationship_import(lines)
        self.editor.write_lines(model_path, lines)

    def _add_foreign_key_import(self, lines: List[str]) -> List[str]:
        for i, line in enumerate(lines):
            if "from sqlalchemy import" in line and "ForeignKey" not in line:
                lines[i] = line.replace("from sqlalchemy import", "from sqlalchemy import ForeignKey,")
                return lines
        return self.editor.ensure_import(lines, "from sqlalchemy import ForeignKey")

    def _add_relationship_import(self, lines: List[str]) -> List[str]:
        for i, line in enumerate(lines):
            if "from sqlalchemy.orm import" in line and "relationship" not in line:
                lines[i] = line.replace("from sqlalchemy.orm import", "from sqlalchemy.orm import relationship,")
                return lines
        for i, line in enumerate(lines):
            if "from sqlalchemy import" in line:
                lines.insert(i + 1, "from sqlalchemy.orm import relationship\n")
                return lines
        return self.editor.ensure_import(lines, "from sqlalchemy.orm import relationship")

    def _generate_one_to_many(self, config: RelationshipConfig):
        self._add_foreign_key(config.target_entity, config.origin_entity)
        self._add_relationship(config.origin_entity, config.target_entity, f"{config.target_entity}s", config.target_entity.capitalize(), is_list=True, back_populates=config.origin_entity)
        self._add_relationship(config.target_entity, config.origin_entity, config.origin_entity, config.origin_entity.capitalize(), is_list=False, back_populates=f"{config.target_entity}s")

    def _generate_many_to_many(self, config: RelationshipConfig):
        table_name = f"{config.origin_entity}_{config.target_entity}"
        self._create_association_table(config.origin_entity, config.target_entity)
        self._add_association_import_to_models(config.origin_entity, table_name)
        self._add_association_import_to_models(config.target_entity, table_name)
        self._add_relationship(config.origin_entity, config.target_entity, f"{config.target_entity}s", config.target_entity.capitalize(), is_list=True, secondary=table_name, back_populates=f"{config.origin_entity}s")
        self._add_relationship(config.target_entity, config.origin_entity, f"{config.origin_entity}s", config.origin_entity.capitalize(), is_list=True, secondary=table_name, back_populates=f"{config.target_entity}s")

    def _generate_one_to_one(self, config: RelationshipConfig):
        unique = True
        if config.foreign_key_in_target:
            self._add_foreign_key(config.target_entity, config.origin_entity, unique=unique)
        else:
            self._add_foreign_key(config.origin_entity, config.target_entity, unique=unique)
        self._add_relationship(config.origin_entity, config.target_entity, config.target_entity, config.target_entity.capitalize(), is_list=False, uselist=False, back_populates=config.origin_entity)
        self._add_relationship(config.target_entity, config.origin_entity, config.origin_entity, config.origin_entity.capitalize(), is_list=False, uselist=False, back_populates=config.target_entity)

    def _add_foreign_key(self, entity_name: str, foreign_entity: str, unique: bool = False):
        model_path = self.base_path / entity_name / f"{entity_name}_model.py"
        if not model_path.exists():
            raise FileNotFoundError(f"Archivo de modelo no encontrado para {entity_name}")
        fk_line = get_foreign_key_template(foreign_entity, unique)
        position, indent = self.editor.find_insert_position_in_class(model_path, entity_name.capitalize())
        lines = self.editor.read_lines(model_path)
        lines = self.editor.insert_line(lines, fk_line, position, indent)
        self.editor.write_lines(model_path, lines)

    def _add_relationship(self, entity_name: str, related_entity: str, relationship_name: str, related_class: str, is_list: bool = False, secondary: str = None, back_populates: str = None, uselist: bool = None):
        model_path = self.base_path / entity_name / f"{entity_name}_model.py"
        if not model_path.exists():
            raise FileNotFoundError(f"Archivo de modelo no encontrado para {entity_name}")
        lines = self.editor.read_lines(model_path)
        if self.editor.ensure_content(lines, f"{relationship_name} = relationship"):
            return
        rel_line = get_relationship_template(relationship_name, related_class, is_list, secondary, back_populates, uselist)
        position, indent = self.editor.find_insert_position_in_class(model_path, entity_name.capitalize())
        lines = self.editor.insert_line(lines, rel_line, position, indent)
        self.editor.write_lines(model_path, lines)

    def _create_association_table(self, entity1: str, entity2: str):
        table_name = f"{entity1}_{entity2}"
        association_dir = self.base_path / "association_models"
        association_dir.mkdir(parents=True, exist_ok=True)
        (association_dir / "__init__.py").touch(exist_ok=True)
        table_path = association_dir / f"{table_name}.py"
        table_code = get_association_table_template(entity1, entity2)
        table_path.write_text(table_code, encoding='utf-8')
        self._add_association_table_to_alembic_env(table_name)

    def _add_association_table_to_alembic_env(self, table_name: str):
        env_path = Path("alembic") / "env.py"
        if not env_path.exists():
            return
        import_line = f"from app.api.association_models.{table_name} import {table_name}\n"
        content = env_path.read_text(encoding="utf-8")
        if import_line.strip() in content:
            return
        lines = content.splitlines(keepends=True)
        new_lines = []
        inserted = False
        for i, line in enumerate(lines):
            new_lines.append(line)
            if line.strip().startswith("from app.api.") and "import" in line:
                for j in range(i+1, len(lines)):
                    if not lines[j].strip().startswith("from app.api."):
                        new_lines.insert(j, import_line)
                        inserted = True
                        break
                if inserted:
                    new_lines.extend(lines[i+1:])
                    break
        if not inserted:
            for i, line in enumerate(lines):
                new_lines.append(line)
                if line.strip() == "from app.db.database import Base":
                    new_lines.append(import_line)
                    inserted = True
                    new_lines.extend(lines[i+1:])
                    break
        if not inserted:
            new_lines.insert(0, import_line)
        env_path.write_text("".join(new_lines), encoding='utf-8')

    def _add_association_import_to_models(self, entity_name: str, table_name: str):
        model_path = self.base_path / entity_name / f"{entity_name}_model.py"
        if not model_path.exists():
            return
        lines = self.editor.read_lines(model_path)
        import_line = f"from app.api.association_models.{table_name} import {table_name}\n"
        if any(f"from app.api.association_models.{table_name}" in line for line in lines):
            return
        inserted = False
        for i, line in enumerate(lines):
            if "from sqlalchemy" in line:
                for j in range(i+1, len(lines)):
                    if not (lines[j].startswith(("from ", "import ")) or not lines[j].strip()):
                        lines.insert(j, import_line)
                        inserted = True
                        break
                if inserted:
                    break
        if not inserted:
            lines.insert(0, import_line)
        self.editor.write_lines(model_path, lines)

    # --- DTOs ---
    def _update_dtos_for_relationship(self, config: RelationshipConfig):
        if config.is_list_in_origin:
            self._update_out_dto(config.origin_entity, config.target_entity, is_list=True)
        if config.is_list_in_target:
            self._update_out_dto(config.target_entity, config.origin_entity, is_list=True)

        if config.relation_type == RelationType.MANY_TO_MANY:
            if config.is_list_in_origin:
                self._update_in_dto(config.origin_entity, config.target_entity, is_list=True)
                self._update_update_dto(config.origin_entity, config.target_entity, is_list=True)
            if config.is_list_in_target:
                self._update_in_dto(config.target_entity, config.origin_entity, is_list=True)
                self._update_update_dto(config.target_entity, config.origin_entity, is_list=True)
        elif config.relation_type == RelationType.ONE_TO_MANY:
            self._update_in_dto(config.target_entity, config.origin_entity, is_list=False)
            self._update_update_dto(config.target_entity, config.origin_entity, is_list=False)
        elif config.relation_type == RelationType.ONE_TO_ONE:
            if config.foreign_key_in_target:
                self._update_in_dto(config.target_entity, config.origin_entity, is_list=False)
                self._update_update_dto(config.target_entity, config.origin_entity, is_list=False)
            else:
                self._update_in_dto(config.origin_entity, config.target_entity, is_list=False)
                self._update_update_dto(config.origin_entity, config.target_entity, is_list=False)

    def _update_out_dto(self, entity_name: str, related_entity: str, is_list: bool):
        self._update_dto(entity_name, related_entity, is_list, dto_suffix="_out_dto")

    def _update_in_dto(self, entity_name: str, related_entity: str, is_list: bool):
        self._update_dto(entity_name, related_entity, is_list, dto_suffix="_in_dto")

    def _update_update_dto(self, entity_name: str, related_entity: str, is_list: bool):
        self._update_dto(entity_name, related_entity, is_list, dto_suffix="_update_dto")

    def _update_dto(self, entity_name: str, related_entity: str, is_list: bool, dto_suffix: str):
        dto_filename = f"{entity_name}{dto_suffix}.py"
        dto_path = self.base_path / entity_name / "dto" / dto_filename
        if not dto_path.exists():
            return
        field_name = f"{related_entity}_ids" if is_list else f"{related_entity}_id"
        lines = self.editor.read_lines(dto_path)
        if self.editor.ensure_content(lines, f"    {field_name}:"):
            return
        field_line = get_out_dto_relation_field(related_entity, is_list) if dto_suffix == "_out_dto" else get_in_dto_relation_field(related_entity, is_list)
        model_config_idx = next((i for i, line in enumerate(lines) if "model_config" in line and "=" in line), -1)
        if model_config_idx == -1:
            lines.append("    " + field_line)
        else:
            indent = next((line[:len(line)-len(line.lstrip())] for line in lines[model_config_idx-1::-1] if line.strip() and ":" in line and "class" not in line), "    ")
            lines.insert(model_config_idx, indent + field_line)
            if model_config_idx + 1 < len(lines) and lines[model_config_idx + 1].strip() != "":
                lines.insert(model_config_idx + 1, "")
        if is_list:
            lines = self.editor.ensure_import(lines, "from typing import List, Optional")
        else:
            lines = self.editor.ensure_import(lines, "from typing import Optional")
        lines = self.editor.ensure_import(lines, "from pydantic import Field")
        lines = self._update_dto_examples(lines, entity_name, related_entity, is_list, dto_type=dto_suffix.strip("_"))
        self.editor.write_lines(dto_path, lines)

    def _update_dto_examples(self, lines: List[str], entity_name: str, related_entity: str, is_list: bool, dto_type: str) -> List[str]:
        model_config_idx = next((i for i, line in enumerate(lines) if "model_config = {" in line), -1)
        if model_config_idx == -1:
            return lines
        json_extra_start = next((i for i in range(model_config_idx, len(lines)) if '"json_schema_extra"' in lines[i]), -1)
        if json_extra_start == -1:
            return lines
        example_start = next((i for i in range(json_extra_start, len(lines)) if '"example"' in lines[i]), -1)
        if example_start == -1:
            return lines
        example_dict_start = next((i+1 for i in range(example_start, min(example_start+5, len(lines))) if "{" in lines[i]), example_start+1)
        brace_count = 0
        example_end = example_dict_start
        for i in range(example_dict_start-1, len(lines)):
            brace_count += lines[i].count('{') - lines[i].count('}')
            if brace_count <= 0 and i >= example_dict_start:
                example_end = i
                break
        field_name = f"{related_entity}_ids" if is_list else f"{related_entity}_id"
        if any(f'"{field_name}"' in line or f"'{field_name}'" in line for line in lines[example_dict_start:example_end]):
            return lines
        current_indent = 8
        if example_dict_start < len(lines) and lines[example_dict_start].strip():
            current_indent = len(lines[example_dict_start]) - len(lines[example_dict_start].lstrip())
        value = "[1, 2, 3]" if is_list else "1"
        lines.insert(example_end, f'{" " * current_indent}"{field_name}": {value},')
        if example_end > example_dict_start and not lines[example_end - 1].rstrip().endswith((',', '{')):
            lines[example_end - 1] += ","
        return lines

    # --- Servicios y Repositorios ---
    def _update_services_for_relationship(self, config: RelationshipConfig):
        if config.relation_type == RelationType.ONE_TO_MANY:
            self._update_service_for_foreign_key_relationship(config)
            # Inject mapping logic for the "One" side (list of IDs)
            if config.is_list_in_origin:
                 self._update_service_model_to_dto(config.origin_entity, config.target_entity, is_list=True)
            
        elif config.relation_type == RelationType.MANY_TO_MANY:
            self._update_service_for_many_to_many(config)
            # Inject mapping logic for both sides (list of IDs)
            self._update_service_model_to_dto(config.origin_entity, config.target_entity, is_list=True)
            self._update_service_model_to_dto(config.target_entity, config.origin_entity, is_list=True)
            
        elif config.relation_type == RelationType.ONE_TO_ONE:
            self._update_service_for_one_to_one(config)
            # Inject mapping logic only for the inverse side (the one that DOES NOT have the FK)
            if config.foreign_key_in_target:
                 # Origin is inverse, needs scalar logic
                 self._update_service_model_to_dto(config.origin_entity, config.target_entity, is_list=False)
            else:
                 # Target is inverse, needs scalar logic
                 self._update_service_model_to_dto(config.target_entity, config.origin_entity, is_list=False)

    def _update_service_model_to_dto(self, entity_name: str, related_entity: str, is_list: bool):
        """Inyecta la lógica de mapeo en el método model_to_dto del servicio."""
        service_path = self.base_path / entity_name / f"{entity_name}_service.py"
        if not service_path.exists():
            return
        
        lines = self.editor.read_lines(service_path)
        
        # Verificar si la lógica ya existe para no duplicar
        check_str = f'dto_dict["{related_entity}_ids"]' if is_list else f'dto_dict["{related_entity}_id"]'
        if any(check_str in line for line in lines):
            return

        # Buscar el método model_to_dto
        start_idx = -1
        for i, line in enumerate(lines):
            if "def model_to_dto" in line:
                start_idx = i
                break
        
        if start_idx == -1:
            return

        # Buscar el punto de inserción (antes del return OutDto)
        insert_idx = -1
        for i in range(start_idx + 1, len(lines)):
            if "return " in lines[i] and "OutDto" in lines[i]:
                 insert_idx = i
                 break
        
        if insert_idx == -1:
            # Fallback: insertar al final del método si no encontramos el return esperado
            # (difícil saber indentación sin return, asumimos el final del bloque)
            return

        # Generar e insertar lógica
        logic_code = get_model_to_dto_logic(related_entity, is_list)
        # La lógica ya viene indentada con 8 espacios en el template, ajustamos si es necesario.
        # Asumimos que el código usa 4 espacios de indentación estándar.
        
        new_lines_logic = logic_code.split('\n')
        # Filtramos líneas vacías extra si el template las tiene
        lines[insert_idx:insert_idx] = [l for l in new_lines_logic if l.strip() != ""]
        
        self.editor.write_lines(service_path, lines)

    def _update_service_for_foreign_key_relationship(self, config: RelationshipConfig):
        if config.is_list_in_origin:
            self._update_service_create_method(config.origin_entity, config)
        if config.is_list_in_target:
            self._update_service_create_method(config.target_entity, config)
        if config.relation_type == RelationType.ONE_TO_MANY:
            self._update_repository_for_fk(config.target_entity, config.origin_entity)

    def _update_service_for_many_to_many(self, config: RelationshipConfig):
        for entity_name in [config.origin_entity, config.target_entity]:
            self._update_service_create_method(entity_name, config)

            service_path = self.base_path / entity_name / f"{entity_name}_service.py"
            if not service_path.exists():
                continue

            related_entity = config.target_entity if entity_name == config.origin_entity else config.origin_entity
            lines = self.editor.read_lines(service_path)
            add_method_name = f"add_{related_entity}_to_{entity_name}"
            if not self.editor.ensure_content(lines, f"def {add_method_name}"):
                lines = self.editor.ensure_import(lines, f"from app.api.{related_entity}.{related_entity}_repository import {related_entity.capitalize()}Repository")
                methods_code = get_many_to_many_service_methods(entity_name, related_entity)
                lines.append("")
                lines.extend("    " + line for line in methods_code.split('\n') if line.strip())
                self.editor.write_lines(service_path, lines)

    def _update_service_for_one_to_one(self, config: RelationshipConfig):
        for entity_name in [config.origin_entity, config.target_entity]:
            self._update_service_create_method(entity_name, config)

    def _update_service_create_method(self, entity_name: str, config: RelationshipConfig = None):
        """
        Inserta o reemplaza el método create_{entity_name} en el servicio.
        """
        service_path = self.base_path / entity_name / f"{entity_name}_service.py"
        if not service_path.exists():
            return

        is_many_to_many = config is not None and config.relation_type == RelationType.MANY_TO_MANY
        has_list = False
        related_entity = None
        if is_many_to_many:
            if entity_name == config.origin_entity and config.is_list_in_origin:
                has_list = True
                related_entity = config.target_entity
            elif entity_name == config.target_entity and config.is_list_in_target:
                has_list = True
                related_entity = config.origin_entity

        lines = self.editor.read_lines(service_path)

        create_method_name = f"create_{entity_name}"
        method_start = -1
        for i, line in enumerate(lines):
            if line.lstrip().startswith(f"def {create_method_name}") or line.lstrip().startswith(f"async def {create_method_name}"):
                method_start = i
                break

        if has_list and related_entity:
            new_method = get_create_method_with_many_to_many_relations(entity_name, related_entity)
        else:
            new_method = get_create_method_with_relation_filter(entity_name)

        if method_start == -1:
            class_pos, _ = self.editor.find_insert_position_in_class(service_path, f"{entity_name.capitalize()}Service")
            lines = self.editor.insert_line(lines, new_method.strip(), class_pos, 4)
        else:
            method_indent = len(lines[method_start]) - len(lines[method_start].lstrip())
            method_end = len(lines) - 1
            for j in range(method_start + 1, len(lines)):
                stripped = lines[j].lstrip()
                current_indent = len(lines[j]) - len(stripped)
                if (stripped.startswith("def ") or stripped.startswith("async def ")) and current_indent <= method_indent:
                    method_end = j - 1
                    break
            new_lines_raw = new_method.strip().split("\n")
            indented_new_lines = []
            for nl in new_lines_raw:
                if nl.strip():
                    indented_new_lines.append(" " * method_indent + nl)
                else:
                    indented_new_lines.append("")
            lines[method_start:method_end + 1] = indented_new_lines

        self.editor.write_lines(service_path, lines)

    def _update_repository_for_fk(self, entity_name: str, related_entity: str):
        repo_path = self.base_path / entity_name / f"{entity_name}_repository.py"
        if not repo_path.exists():
            return
        lines = self.editor.read_lines(repo_path)
        if not self.editor.ensure_content(lines, "def get_by_ids"):
            get_by_ids_code = get_get_by_ids_method(related_entity)
            lines = self.editor.insert_before(lines, get_by_ids_code, "def get_by_id", maintain_indent=False)
            self.editor.write_lines(repo_path, lines)


def main():
    manager = RelationManager()
    manager.create_relation()


if __name__ == "__main__":
    main()