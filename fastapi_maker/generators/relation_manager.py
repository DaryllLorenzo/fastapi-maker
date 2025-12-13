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
    get_model_to_dto_method,
    get_repository_method,
    get_many_to_many_service_methods
)

class RelationType(Enum):
    ONE_TO_MANY = "one-to-many"
    MANY_TO_ONE = "many-to-one"
    MANY_TO_MANY = "many-to-many"
    ONE_TO_ONE = "one-to-one"


@dataclass
class RelationshipConfig:
    """Configuración para una relación entre dos entidades."""
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
            typer.echo("❌ No se encontró la carpeta app/api. ¿Has inicializado el proyecto?")
            raise typer.Exit(1)
        self.editor = CodeEditor()
        self.entities = self._get_existing_entities()

    def _get_existing_entities(self) -> List[str]:
        """Obtiene la lista de entidades existentes (carpetas en app/api)."""
        return [
            d.name for d in self.base_path.iterdir() 
            if d.is_dir() and (d / f"{d.name}_model.py").exists()
        ]

    def create_relation(self):
        """Flujo principal para crear una relación."""
        if len(self.entities) < 2:
            typer.echo("❌ Necesitas al menos dos entidades para crear una relación.")
            return
        
        typer.echo("\n🔗 Creando relación entre entidades")
        typer.echo("=" * 40)

        origin = self._select_entity("Selecciona la entidad de ORIGEN:", self.entities)
        relation_type = self._select_relation_type()
        available_targets = [e for e in self.entities if e != origin]
        target = self._select_entity("Selecciona la entidad de DESTINO:", available_targets)

        config = self._configure_relationship(origin, target, relation_type)
        self._confirm_relationship(config)
        self._generate_relationship(config)

    def _select_entity(self, message: str, choices: List[str]) -> str:
        choice = questionary.select(
            message=message, 
            choices=choices, 
            use_shortcuts=True, 
            qmark="➤", 
            pointer="→"
        ).ask()
        
        if choice is None:
            typer.echo("\n❌ Operación cancelada por el usuario.")
            raise typer.Exit(0)
        
        return choice

    def _select_relation_type(self) -> RelationType:
        choices = [
            {"name": "Uno a Muchos (One-to-Many)", "value": RelationType.ONE_TO_MANY},
            {"name": "Muchos a Uno (Many-to-One)", "value": RelationType.MANY_TO_ONE},
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
            typer.echo("\n❌ Operación cancelada por el usuario.")
            raise typer.Exit(0)
        
        return next(c["value"] for c in choices if c["name"] == choice)

    def _configure_relationship(self, origin: str, target: str, relation_type: RelationType) -> RelationshipConfig:
        if relation_type == RelationType.ONE_TO_MANY:
            return RelationshipConfig(origin, target, relation_type, 
                                     foreign_key_in_target=True, is_list_in_origin=True)
        
        elif relation_type == RelationType.MANY_TO_ONE:
            return RelationshipConfig(origin, target, relation_type, 
                                     foreign_key_in_target=False, is_list_in_target=True)
        
        elif relation_type == RelationType.MANY_TO_MANY:
            return RelationshipConfig(origin, target, relation_type, 
                                     foreign_key_in_target=False, 
                                     is_list_in_origin=True, is_list_in_target=True)
        
        elif relation_type == RelationType.ONE_TO_ONE:
            side = questionary.select(
                message="¿Qué entidad debe tener la foreign key?",
                choices=[f"{origin.capitalize()} (origen)", f"{target.capitalize()} (destino)"],
                default=f"{origin.capitalize()} (origen)",
                qmark="➤",
                pointer="→"
            ).ask()
            
            if side is None:
                typer.echo("\n❌ Operación cancelada.")
                raise typer.Exit(0)
            
            foreign_key_in_target = "destino" in side.lower()
            return RelationshipConfig(origin, target, relation_type, 
                                     foreign_key_in_target=foreign_key_in_target)

    def _confirm_relationship(self, config: RelationshipConfig):
        typer.echo("\n📋 Resumen de la relación:")
        typer.echo("=" * 40)
        typer.echo(f"🔸 Entidad origen: {config.origin_entity}")
        typer.echo(f"🔸 Entidad destino: {config.target_entity}")
        typer.echo(f"🔸 Tipo de relación: {config.relation_type.value}")

        if config.relation_type in [RelationType.ONE_TO_MANY, RelationType.MANY_TO_ONE, RelationType.ONE_TO_ONE]:
            fk_entity = config.target_entity if config.foreign_key_in_target else config.origin_entity
            fk_field = f"{config.origin_entity}_id" if config.foreign_key_in_target else f"{config.target_entity}_id"
            typer.echo(f"🔸 Foreign key en: {fk_entity}_model.py")
            typer.echo(f"🔸 Campo: {fk_field}")

        typer.echo(f"🔸 {config.origin_entity}_out_dto tendrá: {self._get_dto_field_desc(config.target_entity, config.is_list_in_origin)}")
        typer.echo(f"🔸 {config.target_entity}_out_dto tendrá: {self._get_dto_field_desc(config.origin_entity, config.is_list_in_target)}")

        typer.echo("=" * 40)
        if not questionary.confirm("¿Generar la relación con estas configuraciones?", default=True).ask():
            typer.echo("\n❌ Operación cancelada.")
            raise typer.Exit(0)

    def _get_dto_field_desc(self, related_entity: str, is_list: bool) -> str:
        """Obtiene descripción del campo DTO."""
        return f"{related_entity}_ids: List[int]" if is_list else f"{related_entity}_id: Optional[int]"

    def _generate_relationship(self, config: RelationshipConfig):
        typer.echo(f"\n🚀 Generando relación {config.relation_type.value}...")
        
        try:
            self._ensure_sqlalchemy_imports(config.origin_entity)
            self._ensure_sqlalchemy_imports(config.target_entity)

            if config.relation_type == RelationType.ONE_TO_MANY:
                self._generate_one_to_many(config)
            elif config.relation_type == RelationType.MANY_TO_ONE:
                self._generate_many_to_one(config)
            elif config.relation_type == RelationType.MANY_TO_MANY:
                self._generate_many_to_many(config)
            elif config.relation_type == RelationType.ONE_TO_ONE:
                self._generate_one_to_one(config)

            self._update_dtos_for_relationship(config)
            self._update_services_for_relationship(config)

            typer.echo(f"\n✅ Relación {config.relation_type.value} generada exitosamente!")
            typer.echo(f"   Entre: {config.origin_entity} ↔ {config.target_entity}")
            self._show_next_steps(config)
        
        except Exception as e:
            typer.echo(f"\n❌ Error generando relación: {str(e)}")
            import traceback
            traceback.print_exc()
            raise typer.Exit(1)

    def _show_next_steps(self, config: RelationshipConfig):
        """Muestra los próximos pasos."""
        typer.echo("\n📝 Próximos pasos:")
        typer.echo(f"   1. Ejecutar: fam migrate -m 'Agregar relación entre {config.origin_entity} y {config.target_entity}'")
        typer.echo("   2. Revisar el código generado en las carpetas de entidades")
        typer.echo("   3. Los DTOs ahora incluyen campos de ID para las relaciones")
        typer.echo("   4. Actualizar manualmente los DTOs de entrada si es necesario")

    def _ensure_sqlalchemy_imports(self, entity_name: str):
        """Asegura imports de SQLAlchemy."""
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
        typer.echo(f"  ✅ Imports de SQLAlchemy actualizados en {entity_name}_model.py")

    def _add_foreign_key_import(self, lines: List[str]) -> List[str]:
        """Agrega import de ForeignKey."""
        for i, line in enumerate(lines):
            if "from sqlalchemy import" in line and "ForeignKey" not in line:
                lines[i] = line.replace("from sqlalchemy import", "from sqlalchemy import ForeignKey,")
                return lines
        
        return self.editor.ensure_import(lines, "from sqlalchemy import ForeignKey")

    def _add_relationship_import(self, lines: List[str]) -> List[str]:
        """Agrega import de relationship."""
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
        self._add_relationship(config.origin_entity, config.target_entity, 
                              f"{config.target_entity}s", config.target_entity.capitalize(), 
                              is_list=True, back_populates=config.origin_entity)
        self._add_relationship(config.target_entity, config.origin_entity, 
                              config.origin_entity, config.origin_entity.capitalize(), 
                              is_list=False, back_populates=f"{config.target_entity}s")

    def _generate_many_to_one(self, config: RelationshipConfig):
        self._add_foreign_key(config.origin_entity, config.target_entity)
        self._add_relationship(config.origin_entity, config.target_entity, 
                              config.target_entity, config.target_entity.capitalize(), 
                              is_list=False, back_populates=f"{config.origin_entity}s")
        self._add_relationship(config.target_entity, config.origin_entity, 
                              f"{config.origin_entity}s", config.origin_entity.capitalize(), 
                              is_list=True, back_populates=config.target_entity)

    def _generate_many_to_many(self, config: RelationshipConfig):
        table_name = f"{config.origin_entity}_{config.target_entity}"
        self._create_association_table(config.origin_entity, config.target_entity)
        self._add_relationship(config.origin_entity, config.target_entity, 
                              f"{config.target_entity}s", config.target_entity.capitalize(), 
                              is_list=True, secondary=table_name, back_populates=f"{config.origin_entity}s")
        self._add_relationship(config.target_entity, config.origin_entity, 
                              f"{config.origin_entity}s", config.origin_entity.capitalize(), 
                              is_list=True, secondary=table_name, back_populates=f"{config.target_entity}s")

    def _generate_one_to_one(self, config: RelationshipConfig):
        unique = True
        if config.foreign_key_in_target:
            self._add_foreign_key(config.target_entity, config.origin_entity, unique=unique)
        else:
            self._add_foreign_key(config.origin_entity, config.target_entity, unique=unique)
        
        self._add_relationship(config.origin_entity, config.target_entity, 
                              config.target_entity, config.target_entity.capitalize(), 
                              is_list=False, uselist=False, back_populates=config.origin_entity)
        self._add_relationship(config.target_entity, config.origin_entity, 
                              config.origin_entity, config.origin_entity.capitalize(), 
                              is_list=False, uselist=False, back_populates=config.target_entity)

    def _add_foreign_key(self, entity_name: str, foreign_entity: str, unique: bool = False):
        """Agrega foreign key usando template."""
        model_path = self.base_path / entity_name / f"{entity_name}_model.py"
        if not model_path.exists():
            raise FileNotFoundError(f"Archivo de modelo no encontrado para {entity_name}")
        
        # Usar template (ya incluye la indentación básica)
        fk_line = get_foreign_key_template(foreign_entity, unique)
        
        # Encontrar dónde insertar (retorna indentación correcta)
        position, indent = self.editor.find_insert_position_in_class(model_path, entity_name.capitalize())
        
        # Insertar con la indentación calculada
        lines = self.editor.read_lines(model_path)
        lines = self.editor.insert_line(lines, fk_line, position, indent)
        self.editor.write_lines(model_path, lines)
        
        typer.echo(f"  ✅ Foreign key agregada a {entity_name}_model.py: {foreign_entity}_id")

    def _add_relationship(self, entity_name: str, related_entity: str,
                         relationship_name: str, related_class: str,
                         is_list: bool = False, secondary: str = None,
                         back_populates: str = None, uselist: bool = None):
        """Agrega relación usando template."""
        model_path = self.base_path / entity_name / f"{entity_name}_model.py"
        if not model_path.exists():
            raise FileNotFoundError(f"Archivo de modelo no encontrado para {entity_name}")
        
        lines = self.editor.read_lines(model_path)
        
        # Verificar si ya existe
        if self.editor.ensure_content(lines, f"{relationship_name} = relationship"):
            typer.echo(f"⚠️  La relación {relationship_name} ya existe en {entity_name}_model.py")
            return
        
        # Usar template (ya incluye la indentación básica)
        rel_line = get_relationship_template(
            relationship_name, related_class, is_list, secondary, back_populates, uselist
        )
        
        # Encontrar posición e indentación correcta
        position, indent = self.editor.find_insert_position_in_class(model_path, entity_name.capitalize())
        
        # Insertar con indentación correcta
        lines = self.editor.insert_line(lines, rel_line, position, indent)
        self.editor.write_lines(model_path, lines)
        
        typer.echo(f"  ✅ Relación agregada a {entity_name}_model.py: {relationship_name}")


    def _create_association_table(self, entity1: str, entity2: str):
        """Crea tabla de asociación usando template."""
        table_name = f"{entity1}_{entity2}"
        shared_dir = self.base_path / "shared"
        models_dir = shared_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        (models_dir / "__init__.py").touch(exist_ok=True)

        table_path = models_dir / f"{table_name}.py"
        table_code = get_association_table_template(entity1, entity2)
        
        table_path.write_text(table_code, encoding='utf-8')
        typer.echo(f"  ✅ Tabla de asociación creada: shared/models/{table_name}.py")

    def _update_dtos_for_relationship(self, config: RelationshipConfig):
        """Actualiza DTOs de salida y entrada."""
        entities = [
            (config.origin_entity, config.target_entity, config.is_list_in_origin),
            (config.target_entity, config.origin_entity, config.is_list_in_target)
        ]
        
        for entity_name, related_entity, is_list in entities:
            self._update_out_dto(entity_name, related_entity, is_list)
            self._update_in_dto(entity_name, related_entity, is_list)
            self._update_update_dto(entity_name, related_entity, is_list)

    def _update_out_dto(self, entity_name: str, related_entity: str, is_list: bool):
        """Actualiza DTO de salida."""
        dto_path = self.base_path / entity_name / "dto" / f"{entity_name}_out_dto.py"
        if not dto_path.exists():
            return
        
        field_name = f"{related_entity}_ids" if is_list else f"{related_entity}_id"
        lines = self.editor.read_lines(dto_path)
        
        # Verificar si ya existe
        if self.editor.ensure_content(lines, f"    {field_name}:"):
            typer.echo(f"⚠️  El campo de relación {field_name} ya existe en {entity_name}_out_dto.py")
            return
        
        # Usar template (sin indentación - lo manejaremos con LineLocator)
        field_line = get_out_dto_relation_field(related_entity, is_list)
        
        # Usar LineLocator para encontrar model_config
        result = self.editor.find_line(dto_path, "model_config")
        
        # Encontramos model_config, insertar antes con la misma indentación
        line_num, indent = result
        # Insertar en la línea anterior a model_config
        insert_position = line_num - 1  # Convertir a 0-based
        field_line_indented = f'{" " * indent}{field_line}'
        lines.insert(insert_position, field_line_indented)
        
        # Asegurar imports
        import_line = "from typing import List" if is_list else "from typing import Optional"
        lines = self.editor.ensure_import(lines, import_line)
        
        self.editor.write_lines(dto_path, lines)
        typer.echo(f"  ✅ DTO de salida actualizado para {entity_name}: {field_line.strip()}")

    def _update_in_dto(self, entity_name: str, related_entity: str, is_list: bool):
        """Actualiza DTO de entrada (solo si existe)."""
        dto_path = self.base_path / entity_name / "dto" / f"{entity_name}_in_dto.py"
        if not dto_path.exists():
            return
        
        field_name = f"{related_entity}_ids" if is_list else f"{related_entity}_id"
        lines = self.editor.read_lines(dto_path)
        
        # Verificar si ya existe
        if self.editor.ensure_content(lines, f"    {field_name}:"):
            return
        
        # Usar template (sin indentación - lo manejaremos con LineLocator)
        field_line = get_in_dto_relation_field(related_entity, is_list)
        
        # Usar LineLocator para encontrar model_config
        result = self.editor.find_line(dto_path, "model_config")
        
        # Encontramos model_config, insertar antes con la misma indentación
        line_num, indent = result
        # Insertar en la línea anterior a model_config
        insert_position = line_num - 1  # Convertir a 0-based
        field_line_indented = f'{" " * indent}{field_line}'
        lines.insert(insert_position, field_line_indented)
        
        # Asegurar imports
        import_line = "from typing import List" if is_list else "from typing import Optional"
        lines = self.editor.ensure_import(lines, import_line)
        
        self.editor.write_lines(dto_path, lines)
        typer.echo(f"  ✅ DTO de entrada actualizado para {entity_name}: {field_line.strip()}")

    def _update_update_dto(self, entity_name: str, related_entity: str, is_list: bool):
        """Actualiza DTO de actualización (solo si existe)."""
        dto_path = self.base_path / entity_name / "dto" / f"{entity_name}_update_dto.py"
        if not dto_path.exists():
            return
        
        field_name = f"{related_entity}_ids" if is_list else f"{related_entity}_id"
        lines = self.editor.read_lines(dto_path)
        
        # Verificar si ya existe
        if self.editor.ensure_content(lines, f"    {field_name}:"):
            return
        
        # Usar template (sin indentación - lo manejaremos con LineLocator)
        field_line = get_in_dto_relation_field(related_entity, is_list)
        
        # Usar LineLocator para encontrar model_config
        result = self.editor.find_line(dto_path, "model_config")
        
        # Encontramos model_config, insertar antes con la misma indentación
        line_num, indent = result
        # Insertar en la línea anterior a model_config
        insert_position = line_num - 1  # Convertir a 0-based
        field_line_indented = f'{" " * indent}{field_line}'
        lines.insert(insert_position, field_line_indented)
        
        # Asegurar imports - en update_dto ambos campos son Optional
        lines = self.editor.ensure_import(lines, "from typing import Optional")
        if is_list:
            lines = self.editor.ensure_import(lines, "from typing import List")
        
        self.editor.write_lines(dto_path, lines)
        typer.echo(f"  ✅ DTO de actualización actualizado para {entity_name}: {field_line.strip()}")

    def _update_services_for_relationship(self, config: RelationshipConfig):
        """Actualiza servicios según tipo de relación."""
        if config.relation_type in [RelationType.ONE_TO_MANY, RelationType.MANY_TO_ONE]:
            self._update_service_for_foreign_key_relationship(config)
        elif config.relation_type == RelationType.MANY_TO_MANY:
            self._update_service_for_many_to_many(config)
        elif config.relation_type == RelationType.ONE_TO_ONE:
            self._update_service_for_one_to_one(config)

    def _update_service_for_foreign_key_relationship(self, config: RelationshipConfig):
        for entity in [config.origin_entity, config.target_entity]:
            self._update_service_with_relation_ids(entity, config)

        fk_entity = config.target_entity if config.relation_type == RelationType.ONE_TO_MANY else config.origin_entity
        self._update_repository_for_fk(fk_entity, config)

    def _update_repository_for_fk(self, entity_name: str, config: RelationshipConfig):
        """Actualiza repositorio."""
        repo_path = self.base_path / entity_name / f"{entity_name}_repository.py"
        if not repo_path.exists():
            return

        related_entity = config.target_entity if entity_name == config.origin_entity else config.origin_entity
        method_name = f"get_by_{related_entity}_id"
        
        lines = self.editor.read_lines(repo_path)
        
        # Verificar si ya existe
        if self.editor.ensure_content(lines, f"def {method_name}"):
            typer.echo(f"⚠️  El método {method_name} ya existe en {entity_name}_repository.py")
            return
        
        # Usar template (ya incluye indentación correcta)
        method_code = get_repository_method(entity_name, related_entity)
        
        # Insertar antes de get_by_id SIN mantener indentación (el template ya la tiene)
        lines = self.editor.insert_before(lines, method_code, "def get_by_id", maintain_indent=False)
        self.editor.write_lines(repo_path, lines)
        
        typer.echo(f"  ✅ Repositorio actualizado para {entity_name} (método {method_name})")

    def _update_service_with_relation_ids(self, entity_name: str, config: RelationshipConfig):
        """Actualiza servicio."""
        service_path = self.base_path / entity_name / f"{entity_name}_service.py"
        if not service_path.exists():
            return
        
        related_entity = config.target_entity if entity_name == config.origin_entity else config.origin_entity
        is_list = config.is_list_in_origin if entity_name == config.origin_entity else config.is_list_in_target
        
        lines = self.editor.read_lines(service_path)
        
        # Buscar model_to_dto existente
        model_to_dto_line = self.editor.find_line(service_path, "def model_to_dto")
        
        if model_to_dto_line:
            # Actualizar método existente
            line_num, _ = model_to_dto_line
            dto_idx = line_num - 1
            
            # Buscar dto_dict = dentro del método
            for i in range(dto_idx + 1, len(lines)):
                if "dto_dict =" in lines[i]:
                    current_indent = len(lines[i]) - len(lines[i].lstrip())
                    
                    # Determinar lógica a insertar
                    logic_lines = [
                        f'{" " * current_indent}# Incluir IDs de {related_entity}s' if is_list else f'{" " * current_indent}# Incluir ID de {related_entity}',
                        f'{" " * current_indent}if hasattr(entity, "{related_entity}s") and entity.{related_entity}s:' if is_list else f'{" " * current_indent}if hasattr(entity, "{related_entity}") and entity.{related_entity}:',
                        f'{" " * (current_indent + 4)}{related_entity}_ids = [item.id for item in entity.{related_entity}s]' if is_list else f'{" " * (current_indent + 4)}dto_dict["{related_entity}_id"] = entity.{related_entity}.id',
                        f'{" " * (current_indent + 4)}dto_dict["{related_entity}_ids"] = {related_entity}_ids' if is_list else '',
                        f'{" " * current_indent}else:',
                        f'{" " * (current_indent + 4)}dto_dict["{related_entity}_ids"] = []' if is_list else f'{" " * (current_indent + 4)}dto_dict["{related_entity}_id"] = None'
                    ]
                    
                    # Filtrar líneas vacías
                    logic_lines = [line for line in logic_lines if line.strip()]
                    
                    # Insertar después de dto_dict =
                    insert_pos = i + 1
                    for j, line in enumerate(logic_lines):
                        lines.insert(insert_pos + j, line)
                    
                    break
        else:
            # Crear nuevo método usando template
            method_code = get_model_to_dto_method(entity_name, related_entity, is_list)
            
            # Insertar al final de la clase
            position, indent = self.editor.find_insert_position_in_class(service_path, f"{entity_name.capitalize()}Service")
            lines = self.editor.insert_line(lines, method_code.strip(), position, indent)
        
        self.editor.write_lines(service_path, lines)
        typer.echo(f"  ✅ Servicio actualizado para {entity_name} (incluye IDs de {related_entity})")

    def _update_service_for_many_to_many(self, config: RelationshipConfig):
        for entity_name in [config.origin_entity, config.target_entity]:
            service_path = self.base_path / entity_name / f"{entity_name}_service.py"
            if not service_path.exists():
                continue

            related_entity = config.target_entity if entity_name == config.origin_entity else config.origin_entity
            
            # Primero actualizar model_to_dto
            self._update_service_with_relation_ids(entity_name, config)
            
            lines = self.editor.read_lines(service_path)
            add_method = f"add_{related_entity}_to_{entity_name}"
            
            if self.editor.ensure_content(lines, f"def {add_method}"):
                continue

            # Asegurar import
            import_line = f"from app.api.{related_entity}.{related_entity}_repository import {related_entity.capitalize()}Repository"
            lines = self.editor.ensure_import(lines, import_line)

            # Usar template para métodos
            methods_code = get_many_to_many_service_methods(entity_name, related_entity)
            
            # Insertar al final de la clase
            position, indent = self.editor.find_insert_position_in_class(service_path, f"{entity_name.capitalize()}Service")
            lines = self.editor.insert_line(lines, methods_code.strip(), position, indent)
            self.editor.write_lines(service_path, lines)
            
            typer.echo(f"  ✅ Servicio actualizado con métodos many-to-many para {entity_name}")

    def _update_service_for_one_to_one(self, config: RelationshipConfig):
        for entity_name in [config.origin_entity, config.target_entity]:
            service_path = self.base_path / entity_name / f"{entity_name}_service.py"
            if not service_path.exists():
                continue
            
            self._update_service_with_relation_ids(entity_name, config)
            typer.echo(f"  ✅ Servicio actualizado para {entity_name} (one-to-one)")


def main():
    manager = RelationManager()
    manager.create_relation()


if __name__ == "__main__":
    main()