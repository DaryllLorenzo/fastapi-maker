# ---------------------------------------------------
# Project: fastapi-maker (fam)
# Author: Daryll Lorenzo Alfonso
# Year: 2025
# License: MIT License
# ---------------------------------------------------
"""
Templates para relaciones entre entidades en FastAPI-Maker.
"""

from typing import Optional, List


def get_foreign_key_template(foreign_entity: str, unique: bool = False) -> str:
    """Genera código para columna de foreign key."""
    unique_str = ", unique=True" if unique else ""
    return f'{foreign_entity}_id = Column(Integer, ForeignKey("{foreign_entity}s.id"){unique_str})\n'


def get_relationship_template(
    relationship_name: str,
    related_class: str,
    is_list: bool = True,
    secondary: Optional[str] = None,
    back_populates: Optional[str] = None,
    uselist: Optional[bool] = None
) -> str:
    """Genera código para relación SQLAlchemy."""
    params = [f'"{related_class}"']
    if secondary:
        params.append(f'secondary="{secondary}"')
    if back_populates:
        params.append(f'back_populates="{back_populates}"')
    if uselist is not None:
        params.append(f'uselist={str(uselist)}')
    elif not is_list:
        params.append('uselist=False')
    return f'{relationship_name} = relationship({", ".join(params)})\n'


def get_association_table_template(entity1: str, entity2: str) -> str:
    """Genera código para tabla de asociación many-to-many."""
    table_name = f"{entity1}_{entity2}"
    return (
        f'# Association table for many-to-many relationship between {entity1} and {entity2}\n'
        'from sqlalchemy import Table, Column, Integer, ForeignKey\n'
        'from app.db.database import Base\n\n'
        f'{table_name} = Table(\n'
        f'    "{table_name}",\n'
        '    Base.metadata,\n'
        f'    Column("{entity1}_id", Integer, ForeignKey("{entity1}s.id"), primary_key=True),\n'
        f'    Column("{entity2}_id", Integer, ForeignKey("{entity2}s.id"), primary_key=True)\n'
        ')\n'
    )


def get_out_dto_relation_field(related_entity: str, is_list: bool) -> str:
    """Genera campo de relación para DTOs de salida."""
    if is_list:
        return (
            f'{related_entity}_ids: Optional[List[int]] = Field('
            f'None, description="Lista de IDs de {related_entity.capitalize()}s relacionados")'
        )
    else:
        return f'{related_entity}_id: Optional[int] = Field(None, description="ID del {related_entity.capitalize()} relacionado")'


def get_in_dto_relation_field(related_entity: str, is_list: bool) -> str:
    """Genera campo de relación para DTOs de entrada."""
    if is_list:
        return (
            f'{related_entity}_ids: Optional[List[int]] = Field('
            f'None, description="Lista de IDs de {related_entity.capitalize()}s relacionados")'
        )
    else:
        return f'{related_entity}_id: Optional[int] = Field(None, description="ID del {related_entity.capitalize()} relacionado")'


def get_model_to_dto_logic(related_entity: str, is_list: bool) -> str:
    """Genera lógica para incluir IDs en model_to_dto."""
    if is_list:
        return (
            f'        # Incluir IDs de {related_entity}s\n'
            f'        if hasattr(entity, "{related_entity}s") and entity.{related_entity}s:\n'
            f'            {related_entity}_ids = [item.id for item in entity.{related_entity}s]\n'
            f'            dto_dict["{related_entity}_ids"] = {related_entity}_ids\n'
            f'        else:\n'
            f'            dto_dict["{related_entity}_ids"] = []\n'
        )
    else:
        return (
            f'        # Incluir ID de {related_entity}\n'
            f'        if hasattr(entity, "{related_entity}") and entity.{related_entity}:\n'
            f'            dto_dict["{related_entity}_id"] = entity.{related_entity}.id\n'
            f'        else:\n'
            f'            dto_dict["{related_entity}_id"] = None\n'
        )


def get_model_to_dto_method(entity_name: str, related_entity: str, is_list: bool) -> str:
    """Genera método completo model_to_dto."""
    logic = get_model_to_dto_logic(related_entity, is_list)
    return (
        '    def model_to_dto(self, entity):\n'
        '        """Convierte un modelo a DTO, incluyendo campos básicos y relaciones."""\n'
        '        if not entity:\n'
        '            return None\n'
        '        dto_dict = {}\n'
        '        for column in entity.__table__.columns:\n'
        '            dto_dict[column.name] = getattr(entity, column.name)\n'
        f'{logic}'
        f'        from .dto.{entity_name}_out_dto import {entity_name.capitalize()}OutDto\n'
        f'        return {entity_name.capitalize()}OutDto(**dto_dict)\n'
    )


def get_repository_method(entity_name: str, related_entity: str) -> str:
    """Genera método para repositorio."""
    return (
        f'    def get_by_{related_entity}_id(self, {related_entity}_id: int):\n'
        f'        """Obtiene todos los {entity_name}s por {related_entity}_id"""\n'
        f'        return self.db.query(self.model).filter(\n'
        f'            self.model.{related_entity}_id == {related_entity}_id\n'
        f'        ).all()\n'
    )


def get_get_by_ids_method(related_entity: str) -> str:
    """Genera método get_by_ids para repositorio."""
    return (
        '    def get_by_ids(self, ids: List[int]):\n'
        f'        """Obtiene múltiples {related_entity}s por lista de IDs."""\n'
        f'        return self.db.query(self.model).filter(self.model.id.in_(ids)).all()\n'
    )


def get_create_method_with_relation_filter(entity_name: str) -> str:
    """Genera un método create_* que filtra listas (_ids) pero mantiene FKs (_id)."""
    return (
        f'    def create_{entity_name}(self, {entity_name}_in_dto: Create{entity_name.capitalize()}Dto) -> {entity_name.capitalize()}OutDto:\n'
        f'        """Crea una nueva {entity_name}. Filtra automáticamente listas de relaciones."""\n'
        f'        data = {entity_name}_in_dto.model_dump()\n'
        f'        # Filtrar listas de relaciones (_ids) pero MANTENER foreign keys (_id)\n'
        f'        base_data = {{k: v for k, v in data.items() if not k.endswith("_ids")}}\n'
        f'        entity = self.repository.create(base_data)\n'
        f'        return self.model_to_dto(entity)\n'
    )


def get_create_method_with_many_to_many_relations(entity_name: str, related_entity: str) -> str:
    """Genera un método create_* que maneja relaciones m-n."""
    return (
        f'    def create_{entity_name}(self, {entity_name}_in_dto: Create{entity_name.capitalize()}Dto) -> {entity_name.capitalize()}OutDto:\n'
        f'        """Crea una nueva {entity_name} con manejo de relaciones many-to-many."""\n'
        f'        data = {entity_name}_in_dto.model_dump()\n\n'
        f'        # Separar datos base de relaciones (listas)\n'
        f'        base_data = {{k: v for k, v in data.items() if not k.endswith("_ids")}}\n'
        f'        relation_ids = {{k: v for k, v in data.items() if k.endswith("_ids")}}\n\n'
        f'        # Crear entidad base\n'
        f'        entity = self.repository.create(base_data)\n\n'
        f'        # Manejar relaciones many-to-many si existen\n'
        f'        if relation_ids:\n'
        f'            for rel_field, ids in relation_ids.items():\n'
        f'                if ids is not None:\n'
        f'                    rel_name = rel_field[:-4]  # quitar "_ids"\n'
        f'                    for rel_id in ids:\n'
        f'                        add_method = getattr(self, f"add_{{rel_name}}_to_{entity_name}", None)\n'
        f'                        if add_method:\n'
        f'                            try:\n'
        f'                                add_method(entity.id, rel_id)\n'
        f'                            except Exception:\n'
        f'                                pass\n\n'
        f'        return self.model_to_dto(entity)\n'
    )


def get_many_to_many_service_methods(entity_name: str, related_entity: str) -> str:
    """Genera métodos para servicios many-to-many."""
    return (
        f'def add_{related_entity}_to_{entity_name}(self, {entity_name}_id: int, {related_entity}_id: int) -> bool:\n'
        f'    """Agrega una relación many-to-many entre {entity_name} y {related_entity}"""\n'
        f'    {entity_name}_obj = self.repository.get_by_id({entity_name}_id)\n'
        f'    {related_entity}_repo = {related_entity.capitalize()}Repository(self.repository.db)\n'
        f'    {related_entity}_obj = {related_entity}_repo.get_by_id({related_entity}_id)\n'
        f'    if {entity_name}_obj and {related_entity}_obj:\n'
        f'        if {related_entity}_obj not in {entity_name}_obj.{related_entity}s:\n'
        f'            {entity_name}_obj.{related_entity}s.append({related_entity}_obj)\n'
        f'            self.repository.db.commit()\n'
        f'            return True\n'
        f'    return False\n\n'
        f'def remove_{related_entity}_from_{entity_name}(self, {entity_name}_id: int, {related_entity}_id: int) -> bool:\n'
        f'    """Elimina una relación many-to-many entre {entity_name} y {related_entity}"""\n'
        f'    {entity_name}_obj = self.repository.get_by_id({entity_name}_id)\n'
        f'    if {entity_name}_obj:\n'
        f'        {entity_name}_obj.{related_entity}s = [r for r in {entity_name}_obj.{related_entity}s if r.id != {related_entity}_id]\n'
        f'        self.repository.db.commit()\n'
        f'        return True\n'
        f'    return False\n'
    )

def get_update_method_with_many_to_many_relations(entity_name: str, related_entity: str) -> str:
    """Genera un método update_* que maneja relaciones m-n."""
    return (
        f'    def update_{entity_name}(self, {entity_name}_id: int, {entity_name}_update_dto: Update{entity_name.capitalize()}Dto) -> {entity_name.capitalize()}OutDto:\n'
        f'        """Actualiza una {entity_name} existente con manejo de relaciones many-to-many."""\n'
        f'        # Obtener la entidad actual\n'
        f'        entity = self.repository.get_by_id({entity_name}_id)\n'
        f'        if not entity:\n'
        f'            raise ValueError("{entity_name.capitalize()} no encontrada")\n\n'
        f'        data = {entity_name}_update_dto.model_dump(exclude_unset=True)\n\n'
        f'        # Separar datos base de relaciones (listas)\n'
        f'        base_data = {{k: v for k, v in data.items() if not k.endswith("_ids")}}\n'
        f'        relation_ids = {{k: v for k, v in data.items() if k.endswith("_ids")}}\n\n'
        f'        # Actualizar campos base\n'
        f'        if base_data:\n'
        f'            entity = self.repository.update({entity_name}_id, base_data)\n\n'
        f'        # Manejar relaciones many-to-many si se proporcionan\n'
        f'        for rel_field, new_ids in relation_ids.items():\n'
        f'            if new_ids is not None:\n'
        f'                rel_name = rel_field[:-4]  # quitar "_ids"\n'
        f'                \n'
        f'                # Obtener IDs actuales\n'
        f'                current_ids = [obj.id for obj in getattr(entity, f"{{rel_name}}s", [])]\n'
        f'                \n'
        f'                # Encontrar IDs a agregar y eliminar\n'
        f'                ids_to_add = [id for id in new_ids if id not in current_ids]\n'
        f'                ids_to_remove = [id for id in current_ids if id not in new_ids]\n'
        f'                \n'
        f'                # Agregar nuevas relaciones\n'
        f'                for rel_id in ids_to_add:\n'
        f'                    add_method = getattr(self, f"add_{{rel_name}}_to_{entity_name}", None)\n'
        f'                    if add_method:\n'
        f'                        try:\n'
        f'                            add_method({entity_name}_id, rel_id)\n'
        f'                        except Exception as e:\n'
        f'                            self.logger.warning(f"No se pudo agregar relación {{rel_name}} {{rel_id}}: {{e}}")\n'
        f'                \n'
        f'                # Eliminar relaciones antiguas\n'
        f'                for rel_id in ids_to_remove:\n'
        f'                    remove_method = getattr(self, f"remove_{{rel_name}}_from_{entity_name}", None)\n'
        f'                    if remove_method:\n'
        f'                        try:\n'
        f'                            remove_method({entity_name}_id, rel_id)\n'
        f'                        except Exception as e:\n'
        f'                            self.logger.warning(f"No se pudo eliminar relación {{rel_name}} {{rel_id}}: {{e}}")\n'
        f'        \n'
        f'        # Refrescar y retornar\n'
        f'        self.repository.db.refresh(entity)\n'
        f'        return self.model_to_dto(entity)\n'
    )


def get_update_method_with_foreign_key(entity_name: str, related_entity: str) -> str:
    """Genera un método update_* que maneja foreign keys."""
    return (
        f'    def update_{entity_name}(self, {entity_name}_id: int, {entity_name}_update_dto: Update{entity_name.capitalize()}Dto) -> {entity_name.capitalize()}OutDto:\n'
        f'        """Actualiza una {entity_name} existente con manejo de foreign keys."""\n'
        f'        data = {entity_name}_update_dto.model_dump(exclude_unset=True)\n'
        f'        # Mantener foreign key (_id) pero filtrar listas (_ids)\n'
        f'        update_data = {{k: v for k, v in data.items() if not k.endswith("_ids")}}\n'
        f'        entity = self.repository.update({entity_name}_id, update_data)\n'
        f'        return self.model_to_dto(entity)\n'
    )