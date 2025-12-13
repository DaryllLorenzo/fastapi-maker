# templates/relation_templates.py

# ---------------------------------------------------
# Project: fastapi-maker (fam)
# Author: Daryll Lorenzo Alfonso
# Year: 2025
# License: MIT License
# ---------------------------------------------------
"""
Templates para relaciones entre entidades en FastAPI-Maker.
"""

from typing import Optional


def get_foreign_key_template(foreign_entity: str, unique: bool = False) -> str:
    """Genera código para columna de foreign key."""
    unique_str = ", unique=True" if unique else ""
    return f'{foreign_entity}_id = Column(Integer, ForeignKey("{foreign_entity}s.id"){unique_str})'


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
        params.append(f'uselist={str(uselist).lower()}')
    elif not is_list:
        params.append('uselist=False')
    
    return f'{relationship_name} = relationship({", ".join(params)})'


def get_association_table_template(entity1: str, entity2: str) -> str:
    """Genera código para tabla de asociación many-to-many."""
    table_name = f"{entity1}_{entity2}"
    
    return f'''# Association table for many-to-many relationship between {entity1} and {entity2}
from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db.database import Base

{table_name} = Table(
    "{table_name}",
    Base.metadata,
    Column("{entity1}_id", Integer, ForeignKey("{entity1}s.id"), primary_key=True),
    Column("{entity2}_id", Integer, ForeignKey("{entity2}s.id"), primary_key=True)
)'''


def get_out_dto_relation_field(related_entity: str, is_list: bool) -> str:
    """Genera campo de relación para DTOs de salida."""
    if is_list:
        return f'{related_entity}_ids: List[int] = []'
    else:
        return f'{related_entity}_id: Optional[int] = None'


def get_in_dto_relation_field(related_entity: str, is_list: bool) -> str:
    """Genera campo de relación para DTOs de entrada."""
    if is_list:
        return f'{related_entity}_ids: List[int] = []'
    else:
        return f'{related_entity}_id: Optional[int] = None'


def get_model_to_dto_logic(related_entity: str, is_list: bool) -> str:
    """Genera lógica para incluir IDs en model_to_dto."""
    if is_list:
        return f'''        # Incluir IDs de {related_entity}s
        if hasattr(entity, "{related_entity}s") and entity.{related_entity}s:
            {related_entity}_ids = [item.id for item in entity.{related_entity}s]
            dto_dict["{related_entity}_ids"] = {related_entity}_ids
        else:
            dto_dict["{related_entity}_ids"] = []'''
    else:
        return f'''        # Incluir ID de {related_entity}
        if hasattr(entity, "{related_entity}") and entity.{related_entity}:
            dto_dict["{related_entity}_id"] = entity.{related_entity}.id
        else:
            dto_dict["{related_entity}_id"] = None'''


def get_model_to_dto_method(entity_name: str, related_entity: str, is_list: bool) -> str:
    """Genera método completo model_to_dto."""
    logic = get_model_to_dto_logic(related_entity, is_list)
    
    return f'''    def model_to_dto(self, entity):
        """Convierte un modelo a DTO, incluyendo campos básicos y relaciones."""
        if not entity:
            return None
        dto_dict = {{}}
        for column in entity.__table__.columns:
            dto_dict[column.name] = getattr(entity, column.name)
{logic}
        from .dto.{entity_name}_out_dto import {entity_name.capitalize()}OutDto
        return {entity_name.capitalize()}OutDto(**dto_dict)'''


def get_repository_method(entity_name: str, related_entity: str) -> str:
    """Genera método para repositorio."""
    return f'''    def get_by_{related_entity}_id(self, {related_entity}_id: int):
        """Obtiene todos los {entity_name}s por {related_entity}_id"""
        return self.db.query(self.model).filter(
            self.model.{related_entity}_id == {related_entity}_id
        ).all()'''


def get_many_to_many_service_methods(entity_name: str, related_entity: str) -> str:
    """Genera métodos para servicios many-to-many."""
    return f'''    def add_{related_entity}_to_{entity_name}(self, {entity_name}_id: int, {related_entity}_id: int) -> bool:
        """Agrega una relación many-to-many entre {entity_name} y {related_entity}"""
        {entity_name}_obj = self.repository.get_by_id({entity_name}_id)
        {related_entity}_repo = {related_entity.capitalize()}Repository(self.repository.db)
        {related_entity}_obj = {related_entity}_repo.get_by_id({related_entity}_id)
        if {entity_name}_obj and {related_entity}_obj:
            if {related_entity}_obj not in {entity_name}_obj.{related_entity}s:
                {entity_name}_obj.{related_entity}s.append({related_entity}_obj)
                self.repository.db.commit()
                return True
        return False

    def remove_{related_entity}_from_{entity_name}(self, {entity_name}_id: int, {related_entity}_id: int) -> bool:
        """Elimina una relación many-to-many entre {entity_name} y {related_entity}"""
        {entity_name}_obj = self.repository.get_by_id({entity_name}_id)
        if {entity_name}_obj:
            {entity_name}_obj.{related_entity}s = [r for r in {entity_name}_obj.{related_entity}s if r.id != {related_entity}_id]
            self.repository.db.commit()
            return True
        return False'''