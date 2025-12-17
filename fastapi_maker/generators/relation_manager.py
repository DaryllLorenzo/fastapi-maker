# ---------------------------------------------------
# Proyecto: fastapi-maker (fam)
# Autor: Daryll Lorenzo Alfonso
# Año: 2025
# Licencia: MIT License
# ---------------------------------------------------

import typer
from pathlib import Path
import questionary
from typing import List, Optional
from enum import Enum
from dataclasses import dataclass
from fastapi_maker.utils.code_editor import CodeEditor
from fastapi_maker.templates.relation_templates import (
    get_foreign_key_template,
    get_relationship_template,
    get_association_table_template,
    get_out_dto_relation_field,
    get_in_dto_relation_field,
    get_model_to_dto_method,
    get_repository_method,
    get_many_to_many_service_methods
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
            return RelationshipConfig(origin, target, relation_type, foreign_key_in_target=True, is_list_in_origin=True)
        elif relation_type == RelationType.MANY_TO_MANY:
            return RelationshipConfig(origin, target, relation_type, foreign_key_in_target=False, is_list_in_origin=True, is_list_in_target=True)
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
            return RelationshipConfig(origin, target, relation_type, foreign_key_in_target=foreign_key_in_target)

    def _confirm_relationship(self, config: RelationshipConfig):
        typer.echo("\n  Resumen de la relación:")
        typer.echo("=" * 40)
        typer.echo(f"  Entidad origen: {config.origin_entity}")
        typer.echo(f"  Entidad destino: {config.target_entity}")
        typer.echo(f"  Tipo de relación: {config.relation_type.value}")

        if config.relation_type in [RelationType.ONE_TO_MANY, RelationType.ONE_TO_ONE]:
            fk_entity = config.target_entity if config.foreign_key_in_target else config.origin_entity
            fk_field = f"{config.origin_entity}_id" if config.foreign_key_in_target else f"{config.target_entity}_id"
            typer.echo(f"  Foreign key en: {fk_entity}_model.py")
            typer.echo(f"  Campo: {fk_field}")

        typer.echo(f"  {config.origin_entity}_out_dto tendrá: {self._get_dto_field_desc(config.target_entity, config.is_list_in_origin)}")
        typer.echo(f"  {config.target_entity}_out_dto tendrá: {self._get_dto_field_desc(config.origin_entity, config.is_list_in_target)}")
        typer.echo("=" * 40)
        if not questionary.confirm("¿Generar la relación con estas configuraciones?", default=True).ask():
            typer.echo("\n  Operación cancelada.")
            raise typer.Exit(0)

    def _get_dto_field_desc(self, related_entity: str, is_list: bool) -> str:
        return f"{related_entity}_ids: List[int]" if is_list else f"{related_entity}_id: Optional[int]"

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
        typer.echo("   3. Los DTOs ahora incluyen campos de ID para las relaciones y sus examples")
        typer.echo("   4. Actualizar manualmente los DTOs de entrada si es necesario")

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
        typer.echo(f"    Imports de SQLAlchemy actualizados en {entity_name}_model.py")

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
                lines.insert(i + 1, "from sqlalchemy.orm import relationship")
                return lines
        return self.editor.ensure_import(lines, "from sqlalchemy.orm import relationship")

    def _generate_one_to_many(self, config: RelationshipConfig):
        self._add_foreign_key(config.target_entity, config.origin_entity)
        self._add_relationship(config.origin_entity, config.target_entity, f"{config.target_entity}s", config.target_entity.capitalize(), is_list=True, back_populates=config.origin_entity)
        self._add_relationship(config.target_entity, config.origin_entity, config.origin_entity, config.origin_entity.capitalize(), is_list=False, back_populates=f"{config.target_entity}s")

    def _generate_many_to_many(self, config: RelationshipConfig):
        table_name = f"{config.origin_entity}_{config.target_entity}"
        self._create_association_table(config.origin_entity, config.target_entity)
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
        typer.echo(f"    Foreign key agregada a {entity_name}_model.py: {foreign_entity}_id")

    def _add_relationship(self, entity_name: str, related_entity: str, relationship_name: str, related_class: str, is_list: bool = False, secondary: str = None, back_populates: str = None, uselist: bool = None):
        model_path = self.base_path / entity_name / f"{entity_name}_model.py"
        if not model_path.exists():
            raise FileNotFoundError(f"Archivo de modelo no encontrado para {entity_name}")
        lines = self.editor.read_lines(model_path)
        if self.editor.ensure_content(lines, f"{relationship_name} = relationship"):
            typer.echo(f"   La relación {relationship_name} ya existe en {entity_name}_model.py")
            return
        rel_line = get_relationship_template(relationship_name, related_class, is_list, secondary, back_populates, uselist)
        position, indent = self.editor.find_insert_position_in_class(model_path, entity_name.capitalize())
        lines = self.editor.insert_line(lines, rel_line, position, indent)
        self.editor.write_lines(model_path, lines)
        typer.echo(f"    Relación agregada a {entity_name}_model.py: {relationship_name}")

    def _create_association_table(self, entity1: str, entity2: str):
        table_name = f"{entity1}_{entity2}"
        shared_dir = self.base_path / "shared"
        models_dir = shared_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        (models_dir / "__init__.py").touch(exist_ok=True)
        table_path = models_dir / f"{table_name}.py"
        table_code = get_association_table_template(entity1, entity2)
        table_path.write_text(table_code, encoding='utf-8')
        typer.echo(f"    Tabla de asociación creada: shared/models/{table_name}.py")

    def _update_dtos_for_relationship(self, config: RelationshipConfig):
        # --- Salida: según is_list_*
        if config.is_list_in_origin:
            self._update_out_dto(config.origin_entity, config.target_entity, is_list=True)
        elif config.relation_type == RelationType.ONE_TO_ONE and not config.foreign_key_in_target:
            self._update_out_dto(config.origin_entity, config.target_entity, is_list=False)

        if config.is_list_in_target:
            self._update_out_dto(config.target_entity, config.origin_entity, is_list=True)
        elif config.relation_type == RelationType.ONE_TO_ONE and config.foreign_key_in_target:
            self._update_out_dto(config.target_entity, config.origin_entity, is_list=False)

        # --- Entrada y actualización: SIEMPRE campo individual (is_list=False)
        def update_in_and_update(entity: str, related: str):
            self._update_in_dto(entity, related, is_list=False)
            self._update_update_dto(entity, related, is_list=False)

        if config.relation_type == RelationType.ONE_TO_MANY:
            update_in_and_update(config.target_entity, config.origin_entity)
        elif config.relation_type == RelationType.ONE_TO_ONE:
            if config.foreign_key_in_target:
                update_in_and_update(config.target_entity, config.origin_entity)
            else:
                update_in_and_update(config.origin_entity, config.target_entity)
        # MANY_TO_MANY: no se añade nada a in/update DTOs

    def _update_out_dto(self, entity_name: str, related_entity: str, is_list: bool):
        self._update_dto(entity_name, related_entity, is_list, dto_suffix="_out_dto")

    def _update_in_dto(self, entity_name: str, related_entity: str, is_list: bool):
        self._update_dto(entity_name, related_entity, is_list, dto_suffix="_in_dto")

    def _update_update_dto(self, entity_name: str, related_entity: str, is_list: bool):
        self._update_dto(entity_name, related_entity, is_list, dto_suffix="_update_dto")

    def _update_dto(self, entity_name: str, related_entity: str, is_list: bool, dto_suffix: str):
        """Método genérico para actualizar cualquier tipo de DTO."""
        if dto_suffix in ("_in_dto", "_update_dto"):
            is_list = False  # asegurar coherencia: nunca List en in/update

        dto_filename = f"{entity_name}{dto_suffix}.py"
        dto_path = self.base_path / entity_name / "dto" / dto_filename
        if not dto_path.exists():
            return

        field_name = f"{related_entity}_ids" if is_list else f"{related_entity}_id"
        lines = self.editor.read_lines(dto_path)

        if self.editor.ensure_content(lines, f"    {field_name}:"):
            typer.echo(f"   El campo {field_name} ya existe en {dto_filename}")
            return

        if dto_suffix == "_out_dto":
            field_line = get_out_dto_relation_field(related_entity, is_list)
        else:
            field_line = get_in_dto_relation_field(related_entity, is_list)  # siempre is_list=False para estos

        lines = self.editor.insert_before(
            lines,
            field_line,
            "model_config",
            maintain_indent=True,
            ensure_blank_line=True
        )

        # Imports
        if is_list:
            lines = self.editor.ensure_import(lines, "from typing import List, Optional")
        else:
            lines = self.editor.ensure_import(lines, "from typing import Optional")

        # Examples
        lines = self._update_dto_examples(lines, entity_name, related_entity, is_list, dto_type=dto_suffix.strip("_"))

        self.editor.write_lines(dto_path, lines)
        typer.echo(f"    DTO {dto_suffix} actualizado para {entity_name}: {field_line.strip()}")

    def _update_dto_examples(self, lines: List[str], entity_name: str, related_entity: str, is_list: bool, dto_type: str) -> List[str]:
        """Actualiza el ejemplo en model_config (asume formato dict literal con json_schema_extra)."""
        model_config_idx = -1
        for i, line in enumerate(lines):
            if "model_config = {" in line:
                model_config_idx = i
                break
        if model_config_idx == -1:
            return lines

        json_extra_start = -1
        for i in range(model_config_idx, len(lines)):
            if '"json_schema_extra"' in lines[i]:
                json_extra_start = i
                break
        if json_extra_start == -1:
            return lines

        example_start = -1
        for i in range(json_extra_start, len(lines)):
            if '"example"' in lines[i]:
                example_start = i
                break
        if example_start == -1:
            return lines

        # Encontrar dict de example
        example_dict_start = -1
        for i in range(example_start, len(lines)):
            if "{" in lines[i]:
                if lines[i].strip().endswith("{"):
                    example_dict_start = i + 1
                else:
                    for j in range(i+1, min(i+5, len(lines))):
                        if lines[j].strip() == "{":
                            example_dict_start = j + 1
                            break
                    if example_dict_start == -1:
                        example_dict_start = i + 1
                break
        if example_dict_start == -1:
            example_dict_start = example_start + 1

        # Cierre
        brace_count = 0
        example_end = -1
        for i in range(example_dict_start - 1, len(lines)):
            brace_count += lines[i].count('{') - lines[i].count('}')
            if brace_count <= 0 and i >= example_dict_start:
                example_end = i
                break
        if example_end == -1:
            example_end = example_dict_start + 10

        field_name = f"{related_entity}_ids" if is_list else f"{related_entity}_id"
        if any(f'"{field_name}"' in line or f"'{field_name}'" in line for line in lines[example_dict_start:example_end]):
            return lines

        current_indent = 8  # fallback (4 para class + 4 para ejemplo)
        if example_dict_start < len(lines):
            first_field = lines[example_dict_start]
            if first_field.strip():
                current_indent = len(first_field) - len(first_field.lstrip())

        value = "[1, 2, 3]" if is_list else "1"
        new_line = f'{" " * current_indent}"{field_name}": {value},'
        lines.insert(example_end, new_line)

        # Asegurar coma en línea anterior
        if example_end > example_dict_start:
            prev = lines[example_end - 1].rstrip()
            if prev and not prev.endswith(',') and not prev.endswith('{'):
                lines[example_end - 1] = prev + ','

        return lines

    def _update_services_for_relationship(self, config: RelationshipConfig):
        if config.relation_type in [RelationType.ONE_TO_MANY]:
            self._update_service_for_foreign_key_relationship(config)
        elif config.relation_type == RelationType.MANY_TO_MANY:
            self._update_service_for_many_to_many(config)
        elif config.relation_type == RelationType.ONE_TO_ONE:
            self._update_service_for_one_to_one(config)

    def _update_service_for_foreign_key_relationship(self, config: RelationshipConfig):
        if config.is_list_in_origin:
            self._update_service_with_relation_ids(config.origin_entity, config)
        if config.is_list_in_target:
            self._update_service_with_relation_ids(config.target_entity, config)

        if config.relation_type == RelationType.ONE_TO_MANY:
            self._update_repository_for_fk(config.target_entity, config.origin_entity)

    def _update_repository_for_fk(self, entity_name: str, related_entity: str):
        repo_path = self.base_path / entity_name / f"{entity_name}_repository.py"
        if not repo_path.exists():
            return

        method_name = f"get_by_{related_entity}_id"
        lines = self.editor.read_lines(repo_path)
        if self.editor.ensure_content(lines, f"def {method_name}"):
            typer.echo(f"   El método {method_name} ya existe en {entity_name}_repository.py")
            return

        method_code = get_repository_method(entity_name, related_entity)
        lines = self.editor.insert_before(lines, method_code, "def get_by_id", maintain_indent=False)
        self.editor.write_lines(repo_path, lines)
        typer.echo(f"    Repositorio actualizado para {entity_name} (método {method_name})")

    def _update_service_with_relation_ids(self, entity_name: str, config: RelationshipConfig):
        service_path = self.base_path / entity_name / f"{entity_name}_service.py"
        if not service_path.exists():
            return

        related_entity = config.target_entity if entity_name == config.origin_entity else config.origin_entity
        is_list = config.is_list_in_origin if entity_name == config.origin_entity else config.is_list_in_target

        lines = self.editor.read_lines(service_path)
        model_to_dto_line = self.editor.find_line(service_path, "def model_to_dto")

        if model_to_dto_line:
            line_num, _ = model_to_dto_line
            for i in range(line_num, len(lines)):
                if "dto_dict =" in lines[i]:
                    current_indent = len(lines[i]) - len(lines[i].lstrip())
                    logic_lines = self._build_dto_logic_lines(related_entity, is_list, current_indent)
                    for j, logic in enumerate(logic_lines):
                        lines.insert(i + 1 + j, logic)
                    break
        else:
            method_code = get_model_to_dto_method(entity_name, related_entity, is_list)
            position, indent = self.editor.find_insert_position_in_class(service_path, f"{entity_name.capitalize()}Service")
            lines = self.editor.insert_line(lines, method_code.strip(), position, indent)

        self.editor.write_lines(service_path, lines)
        typer.echo(f"    Servicio actualizado para {entity_name} (incluye IDs de {related_entity})")

    def _build_dto_logic_lines(self, related_entity: str, is_list: bool, base_indent: int) -> List[str]:
        i4 = " " * (base_indent + 4)
        i0 = " " * base_indent
        if is_list:
            return [
                f'{i0}# Incluir IDs de {related_entity}s',
                f'{i0}if hasattr(entity, "{related_entity}s") and entity.{related_entity}s:',
                f'{i4}{related_entity}_ids = [item.id for item in entity.{related_entity}s]',
                f'{i4}dto_dict["{related_entity}_ids"] = {related_entity}_ids',
                f'{i0}else:',
                f'{i4}dto_dict["{related_entity}_ids"] = []',
            ]
        else:
            return [
                f'{i0}# Incluir ID de {related_entity}',
                f'{i0}if hasattr(entity, "{related_entity}") and entity.{related_entity}:',
                f'{i4}dto_dict["{related_entity}_id"] = entity.{related_entity}.id',
                f'{i0}else:',
                f'{i4}dto_dict["{related_entity}_id"] = None',
            ]

    def _update_service_for_many_to_many(self, config: RelationshipConfig):
        for entity_name in [config.origin_entity, config.target_entity]:
            service_path = self.base_path / entity_name / f"{entity_name}_service.py"
            if not service_path.exists():
                continue

            related_entity = config.target_entity if entity_name == config.origin_entity else config.origin_entity
            self._update_service_with_relation_ids(entity_name, config)

            lines = self.editor.read_lines(service_path)
            if self.editor.ensure_content(lines, f"def add_{related_entity}_to_{entity_name}"):
                continue

            lines = self.editor.ensure_import(lines, f"from app.api.{related_entity}.{related_entity}_repository import {related_entity.capitalize()}Repository")
            methods_code = get_many_to_many_service_methods(entity_name, related_entity)
            position, indent = self.editor.find_insert_position_in_class(service_path, f"{entity_name.capitalize()}Service")
            lines = self.editor.insert_line(lines, methods_code.strip(), position, indent)
            self.editor.write_lines(service_path, lines)
            typer.echo(f"    Servicio actualizado con métodos many-to-many para {entity_name}")

    def _update_service_for_one_to_one(self, config: RelationshipConfig):
        for entity_name in [config.origin_entity, config.target_entity]:
            service_path = self.base_path / entity_name / f"{entity_name}_service.py"
            if not service_path.exists():
                continue
            self._update_service_with_relation_ids(entity_name, config)
            typer.echo(f"    Servicio actualizado para {entity_name} (one-to-one)")


def main():
    manager = RelationManager()
    manager.create_relation()


if __name__ == "__main__":
    main()