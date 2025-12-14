# ---------------------------------------------------
# Proyecto: fastapi-maker (fam)
# Autor: Daryll Lorenzo Alfonso
# Año: 2025
# Licencia: MIT License
# ---------------------------------------------------

"""
Módulo que define las plantillas de código para generar una entidad CRUD.

Contiene funciones para generar:
- Modelo SQLAlchemy (con columnas obligatorias/opcionales)
- DTOs de Pydantic (Create, Update, Out) con tipos y ejemplos correctos
- Repositorio, Servicio y Router de FastAPI

Correcciones aplicadas:
1. Usa `Path(...)` en endpoints con `{id}` → evita "<built-in function id>" en Swagger.
2. Añade en la descripción del endpoint POST una lista de campos obligatorios/opcionales.
3. Mantiene ejemplos con valores reales sin modificar las claves.
"""

from typing import List, Dict
from fastapi_maker.utils.sqlalchemy_type_map import SQLALCHEMY_TYPE_MAP
from fastapi_maker.utils.pydantic_type_map import PYDANTIC_TYPE_MAP
from fastapi_maker.utils.pydantic_imports import PYDANTIC_IMPORTS
from fastapi_maker.utils.example_values import EXAMPLE_VALUES

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def _get_example_value(field_type: str) -> str:
    return EXAMPLE_VALUES.get(field_type, '"Example"')


def _generate_model_fields(fields: List[Dict[str, str]]) -> str:
    lines = []
    for field in fields:
        sa_type = SQLALCHEMY_TYPE_MAP[field["type"]]
        nullable = "nullable=False" if field["required"] else "nullable=True"
        doc = f'doc="Field {field["name"]}"'
        lines.append(f'    {field["name"]} = Column({sa_type}, {nullable}, {doc})')
    return "\n".join(lines)


def _generate_create_dto_fields(fields: List[Dict[str, str]]) -> str:
    lines = []
    for field in fields:
        py_type = PYDANTIC_TYPE_MAP[field["type"]]
        desc = f'description="Field {field["name"]}"'
        if field["required"]:
            lines.append(f'    {field["name"]}: {py_type} = Field(..., {desc})')
        else:
            lines.append(f'    {field["name"]}: {py_type} | None = Field(None, {desc})')
    return "\n".join(lines)


def _generate_update_dto_fields(fields: List[Dict[str, str]]) -> str:
    lines = []
    for field in fields:
        py_type = PYDANTIC_TYPE_MAP[field["type"]]
        desc = f'description="Field {field["name"]}"'
        lines.append(f'    {field["name"]}: {py_type} | None = Field(None, {desc})')
    return "\n".join(lines)


def _get_pydantic_imports(fields: List[Dict[str, str]]) -> str:
    imports = set()
    for field in fields:
        imp = PYDANTIC_IMPORTS.get(field["type"])
        if imp:
            imports.add(imp)
    return "\n".join(sorted(imports)) if imports else ""


def _build_example_dict(fields: List[Dict[str, str]]) -> str:
    items = [
        f'"{field["name"]}": {_get_example_value(field["type"])}'
        for field in fields
    ]
    if not items:
        return "{}"
    return ",\n".join(f'                {item}' for item in items)

def _generate_out_dto_fields(fields: List[Dict[str, str]]) -> str:
    """Genera campos para el DTO de salida, incluyendo ID y timestamps."""
    lines = ["    id: int = Field(..., description=\"Unique identifier\", example=1)"]
    for field in fields:
        py_type = PYDANTIC_TYPE_MAP[field["type"]]
        lines.append(f'    {field["name"]}: {py_type} | None = None')
    lines.append('    created_at: datetime = Field(..., description="Creation timestamp")')
    lines.append('    updated_at: datetime = Field(..., description="Last update timestamp")')
    
    # Espacio para relaciones que se agregarán después (como IDs)
    lines.append('\n    # Relationship IDs (will be added by relation manager)')
    return "\n".join(lines)


# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

# templates/entity_templates.py (versión completa y corregida)

def get_main_templates(entity_name: str, fields: List[Dict[str, str]]) -> dict:
    entity_class = entity_name.capitalize()
    model_fields = _generate_model_fields(fields)

    # Generar lista de campos obligatorios y opcionales para la descripción
    required_fields = [f["name"] for f in fields if f["required"]]
    optional_fields = [f["name"] for f in fields if not f["required"]]
    required_str = ", ".join(required_fields) if required_fields else "None"
    optional_str = ", ".join(optional_fields) if optional_fields else "None"

    create_description = f"""
**Required fields**: {required_str}
**Optional fields**: {optional_str}
    """.strip()

    return {
        f"{entity_name}_model.py": f'''# ORM Model for {entity_name}
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, Float, BigInteger
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.db.base_mixin import BaseMixin

class {entity_class}(Base, BaseMixin):
    """{entity_class} model representing a {entity_name} in the database"""
    
    __tablename__ = "{entity_name.lower()}s"
    
{model_fields}
    
    # Relationships will be added here by relation manager
''',

        f"{entity_name}_repository.py": f'''# Repository for {entity_name}
from typing import List, Optional
from sqlalchemy.orm import Session
from .{entity_name}_model import {entity_class}


class {entity_class}Repository:
    def __init__(self, db: Session):
        self.db = db
        self.model = {entity_class}

    def get_all(self) -> List[{entity_class}]:
        return self.db.query({entity_class}).all()
    
    def get_by_id(self, id: int) -> Optional[{entity_class}]:
        return self.db.query({entity_class}).filter({entity_class}.id == id).first()
    
    def create(self, {entity_name}_data: dict) -> {entity_class}:
        db_item = {entity_class}(**{entity_name}_data)
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item
    
    def update(self, id: int, update_data: dict) -> Optional[{entity_class}]:
        item = self.get_by_id(id)
        if item:
            for key, value in update_data.items():
                if value is not None:
                    setattr(item, key, value)
            self.db.commit()
            self.db.refresh(item)
        return item
    
    def delete(self, id: int) -> bool:
        item = self.get_by_id(id)
        if item:
            self.db.delete(item)
            self.db.commit()
            return True
        return False
''',

        f"{entity_name}_service.py": f'''# Service for {entity_name}
from typing import List, Optional
from sqlalchemy.orm import Session
from .{entity_name}_model import {entity_class}
from .{entity_name}_repository import {entity_class}Repository
from .dto.{entity_name}_in_dto import Create{entity_class}Dto
from .dto.{entity_name}_update_dto import Update{entity_class}Dto
from .dto.{entity_name}_out_dto import {entity_class}OutDto


class {entity_class}Service:
    def __init__(self, repository: {entity_class}Repository):
        self.repository = repository
    
    def model_to_dto(self, entity: {entity_class}) -> Optional[{entity_class}OutDto]:
        """Convierte un modelo a DTO, incluyendo campos básicos."""
        if not entity:
            return None
        
        # Convertir el modelo a diccionario usando to_dict si existe
        if hasattr(entity, 'to_dict'):
            dto_dict = entity.to_dict()
        else:
            # Alternativa: convertir atributos manualmente
            dto_dict = {{}}
            for column in entity.__table__.columns:
                dto_dict[column.name] = getattr(entity, column.name)
        
        # Nota: Las relaciones (IDs) se agregarán automáticamente
        # por el relation_manager cuando se cree una relación
        
        return {entity_class}OutDto(**dto_dict)
    
    def get_all_{entity_name}s(self) -> List[{entity_class}OutDto]:
        entities = self.repository.get_all()
        return [self.model_to_dto(entity) for entity in entities]
    
    def get_{entity_name}_by_id(self, id: int) -> Optional[{entity_class}OutDto]:
        entity = self.repository.get_by_id(id)
        return self.model_to_dto(entity)
    
    def create_{entity_name}(self, {entity_name}_data: Create{entity_class}Dto) -> {entity_class}OutDto:
        entity_data_dict = {entity_name}_data.model_dump()
        entity = self.repository.create(entity_data_dict)
        return self.model_to_dto(entity)
    
    def update_{entity_name}(self, id: int, update_data: Update{entity_class}Dto) -> Optional[{entity_class}OutDto]:
        update_dict = {{key: value for key, value in update_data.model_dump().items() if value is not None}}
        if not update_dict:
            return None
        entity = self.repository.update(id, update_dict)
        return self.model_to_dto(entity)
    
    def delete_{entity_name}(self, id: int) -> bool:
        return self.repository.delete(id)
''',

        f"{entity_name}_router.py": f'''# Router for {entity_name}
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.orm import Session
from app.db.database import get_db
from typing import List, Optional
from .{entity_name}_repository import {entity_class}Repository
from .{entity_name}_service import {entity_class}Service
from .dto.{entity_name}_in_dto import Create{entity_class}Dto
from .dto.{entity_name}_update_dto import Update{entity_class}Dto
from .dto.{entity_name}_out_dto import {entity_class}OutDto


router = APIRouter(
    prefix="/{entity_name}s",
    tags=["{entity_class}s"],
    responses={{
        404: {{"description": "{entity_class} not found"}},
        400: {{"description": "Bad request"}}
    }}
)


def get_service(db: Session = Depends(get_db)) -> {entity_class}Service:
    repository = {entity_class}Repository(db)
    return {entity_class}Service(repository)


@router.get("/", response_model=List[{entity_class}OutDto])
def get_all_{entity_name}s(service: {entity_class}Service = Depends(get_service)) -> List[{entity_class}OutDto]:
    return service.get_all_{entity_name}s()


@router.get("/{{{entity_name}_id}}", response_model={entity_class}OutDto)
def get_{entity_name}_by_id(
    {entity_name}_id: int = Path(..., description="ID of the {entity_name} to retrieve"),
    service: {entity_class}Service = Depends(get_service)
) -> {entity_class}OutDto:
    entity = service.get_{entity_name}_by_id({entity_name}_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{entity_class} not found")
    return entity


@router.post(
    "/",
    response_model={entity_class}OutDto,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new {entity_name}",
    description=\"\"\"{create_description}\"\"\"
)
def create_{entity_name}({entity_name}_data: Create{entity_class}Dto, service: {entity_class}Service = Depends(get_service)) -> {entity_class}OutDto:
    return service.create_{entity_name}({entity_name}_data)


@router.patch("/{{{entity_name}_id}}",
                response_model={entity_class}OutDto,
                summary="Update {entity_name}",
                description=\"\"\"{create_description}\"\"\"
)
def update_{entity_name}(
    {entity_name}_id: int = Path(..., description="ID of the {entity_name} to update"),
    update_data: Update{entity_class}Dto = Body(...),
    service: {entity_class}Service = Depends(get_service)
) -> {entity_class}OutDto:
    entity = service.update_{entity_name}({entity_name}_id, update_data)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{entity_class} not found")
    return entity


@router.delete("/{{{entity_name}_id}}", status_code=status.HTTP_204_NO_CONTENT)
def delete_{entity_name}(
    {entity_name}_id: int = Path(..., description="ID of the {entity_name} to delete"),
    service: {entity_class}Service = Depends(get_service)
):
    success = service.delete_{entity_name}({entity_name}_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{entity_class} not found")
'''
    }

def get_dto_templates(entity_name: str, fields: List[Dict[str, str]]) -> dict:
    entity_class = entity_name.capitalize()
    pydantic_imports = _get_pydantic_imports(fields)
    create_fields = _generate_create_dto_fields(fields)
    update_fields = _generate_update_dto_fields(fields)
    out_fields = _generate_out_dto_fields(fields)

    # Siempre necesitamos datetime por created_at/updated_at
    time_imports = "from datetime import datetime\n"
    if any(f["type"] == "date" for f in fields):
        time_imports += "from datetime import date\n"

    create_example = _build_example_dict(fields)
    update_example = _build_example_dict(fields)

    out_example_lines = ['"id": 1']
    for field in fields:
        out_example_lines.append(f'"{field["name"]}": {_get_example_value(field["type"])}')
    out_example_lines.extend([
        '"created_at": "2023-01-01T00:00:00"',
        '"updated_at": "2023-01-01T00:00:00"'
    ])
    out_example_str = ",\n".join(f'                {line}' for line in out_example_lines)

    return {
        f"{entity_name}_in_dto.py": f'''# Input DTO for {entity_name}
from pydantic import BaseModel, Field
{pydantic_imports}

class Create{entity_class}Dto(BaseModel):
{create_fields}

    model_config = {{
        "json_schema_extra": {{
            "example": {{
{create_example}
            }}
        }}
    }}
''',

        f"{entity_name}_update_dto.py": f'''# Update DTO for {entity_name}
from pydantic import BaseModel, Field
from typing import Optional
{pydantic_imports}

class Update{entity_class}Dto(BaseModel):
{update_fields}

    model_config = {{
        "json_schema_extra": {{
            "example": {{
{update_example}
            }}
        }}
    }}
''',

        f"{entity_name}_out_dto.py": f'''# Output DTO for {entity_name}
from pydantic import BaseModel, Field
from typing import Optional, List
{time_imports}
{pydantic_imports}

class {entity_class}OutDto(BaseModel):
{out_fields}

    model_config = {{
        "from_attributes": True,
        "json_schema_extra": {{
            "example": {{
{out_example_str}
            }}
        }}
    }}
'''
    }