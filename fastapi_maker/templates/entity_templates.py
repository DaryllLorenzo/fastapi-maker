# templates/entity_templates.py

def get_main_templates(entity_name: str) -> dict:
    """Plantillas para los archivos principales"""
    entity_class = entity_name.capitalize()  # User, Product, etc.

    return {
        f"{entity_name}_model.py": f'''# Modelo ORM de {entity_name}
from sqlalchemy import Column, String
from db.database import Base
from db.base_mixin import BaseMixin

class {entity_class}(Base, BaseMixin):
    __tablename__ = "{entity_name.lower()}"
    
    nombre = Column(String(100), nullable=False)
''',

        f"{entity_name}_repository.py": f'''# Repository de {entity_name}
from typing import List, Optional
from sqlalchemy.orm import Session
from .{entity_name}_model import {entity_class}

class {entity_class}Repository:
    def get_all(self, db: Session) -> List[{entity_class}]:
        return db.query({entity_class}).all()
    
    def get_by_id(self, db: Session, id: int) -> Optional[{entity_class}]:
        return db.query({entity_class}).filter({entity_class}.id == id).first()
    
    def create(self, db: Session, item: {entity_class}) -> {entity_class}:
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
''',

        f"{entity_name}_service.py": f'''# Service de {entity_name}
from typing import List, Optional
from sqlalchemy.orm import Session
from .{entity_name}_model import {entity_class}
from .{entity_name}_repository import {entity_class}Repository

class {entity_class}Service:
    def __init__(self):
        self.repository = {entity_class}Repository()
    
    def get_all_{entity_name}s(self, db: Session) -> List[{entity_class}]:
        return self.repository.get_all(db)
    
    def get_{entity_name}_by_id(self, db: Session, id: int) -> Optional[{entity_class}]:
        return self.repository.get_by_id(db, id)
    
    def create_{entity_name}(self, db: Session, item: {entity_class}) -> {entity_class}:
        return self.repository.create(db, item)
''',

        f"{entity_name}_router.py": f'''# Router de {entity_name}
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from .{entity_name}_service import {entity_class}Service
from .dto.{entity_name}_in_dto import Create{entity_class}Dto
from .dto.{entity_name}_out_dto import {entity_class}OutDto

router = APIRouter(prefix="/{entity_name}s", tags=["{entity_class}"])

service = {entity_class}Service()

@router.get("/", response_model=list[{entity_class}OutDto])
def get_all_{entity_name}s(db: Session = Depends(get_db)):
    return service.get_all_{entity_name}s(db)

@router.get("/{{id}}", response_model={entity_class}OutDto)
def get_{entity_name}_by_id(id: int, db: Session = Depends(get_db)):
    item = service.get_{entity_name}_by_id(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="{entity_class} no encontrado")
    return item

@router.post("/", response_model={entity_class}OutDto)
def create_{entity_name}(item: Create{entity_class}Dto, db: Session = Depends(get_db)):
    from .{entity_name}_model import {entity_class}
    db_item = {entity_class}(**item.model_dump())
    return service.create_{entity_name}(db, db_item)
'''
    }


def get_dto_templates(entity_name: str) -> dict:
    """Plantillas para los archivos DTO (Pydantic v2)"""
    entity_class = entity_name.capitalize()

    return {
        f"{entity_name}_in_dto.py": f'''# DTO de entrada para {entity_name}
from pydantic import BaseModel

class Create{entity_class}Dto(BaseModel):
    nombre: str

    model_config = {{"from_attributes": True}}
''',

        f"{entity_name}_out_dto.py": f'''# DTO de salida para {entity_name}
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class {entity_class}OutDto(BaseModel):
    id: int
    nombre: str
    created_at: datetime
    updated_at: datetime

    model_config = {{"from_attributes": True}}
'''
    }