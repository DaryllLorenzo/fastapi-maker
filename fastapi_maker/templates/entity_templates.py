# templates/entity_templates.py

def get_main_templates(entity_name: str) -> dict:
    """Plantillas para los archivos principales"""
    entity_class = entity_name.capitalize()

    return {
        f"{entity_name}_model.py": f'''# ORM Model for {entity_name}
from sqlalchemy import Column, String
from app.db.database import Base
from app.db.base_mixin import BaseMixin

class {entity_class}(Base, BaseMixin):
    """{entity_class} model representing a {entity_name} in the database"""
    
    __tablename__ = "{entity_name.lower()}s"
    
    name = Column(String(100), nullable=False, doc="Name of the {entity_name}")
''',

        f"{entity_name}_repository.py": f'''# Repository for {entity_name}
from typing import List, Optional
from sqlalchemy.orm import Session
from .{entity_name}_model import {entity_class}


class {entity_class}Repository:
    """Repository class for handling database operations for {entity_class} entities"""

    def __init__(self, db: Session):
        """Initialize repository with database session"""
        self.db = db

    def get_all(self) -> List[{entity_class}]:
        """
        Retrieve all {entity_name} entities from database
        
        Returns:
            List[{entity_class}]: List of all {entity_name} entities
        """
        return self.db.query({entity_class}).all()
    
    def get_by_id(self, id: int) -> Optional[{entity_class}]:
        """
        Retrieve a {entity_name} by its ID
        
        Args:
            id (int): The ID of the {entity_name} to retrieve
            
        Returns:
            Optional[{entity_class}]: The {entity_name} entity if found, None otherwise
        """
        return self.db.query({entity_class}).filter({entity_class}.id == id).first()
    
    def create(self, {entity_name}_data: dict) -> {entity_class}:
        """
        Create a new {entity_name} entity
        
        Args:
            {entity_name}_data (dict): Dictionary containing {entity_name} data
            
        Returns:
            {entity_class}: The created {entity_name} entity
        """
        db_item = {entity_class}(**{entity_name}_data)
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item
    
    def update(self, id: int, update_data: dict) -> Optional[{entity_class}]:
        """
        Update an existing {entity_name} entity
        
        Args:
            id (int): The ID of the {entity_name} to update
            update_data (dict): Dictionary containing fields to update
            
        Returns:
            Optional[{entity_class}]: The updated {entity_name} entity if found, None otherwise
        """
        item = self.get_by_id(id)
        if item:
            for key, value in update_data.items():
                if value is not None:  # Only update fields that are provided
                    setattr(item, key, value)
            self.db.commit()
            self.db.refresh(item)
        return item
    
    def delete(self, id: int) -> bool:
        """
        Delete a {entity_name} entity by ID
        
        Args:
            id (int): The ID of the {entity_name} to delete
            
        Returns:
            bool: True if deletion was successful, False if {entity_name} not found
        """
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
    """Service class for handling business logic for {entity_class} entities"""

    def __init__(self, repository: {entity_class}Repository):
        """Initialize service with repository"""
        self.repository = repository
    
    def get_all_{entity_name}s(self) -> List[{entity_class}OutDto]:
        """
        Get all {entity_name} entities
        
        Returns:
            List[{entity_class}OutDto]: List of all {entity_name} entities as DTOs
        """
        entities = self.repository.get_all()
        return [{entity_class}OutDto.model_validate(entity) for entity in entities]
    
    def get_{entity_name}_by_id(self, id: int) -> Optional[{entity_class}OutDto]:
        """
        Get a {entity_name} by ID
        
        Args:
            id (int): The ID of the {entity_name} to retrieve
            
        Returns:
            Optional[{entity_class}OutDto]: The {entity_name} as DTO if found, None otherwise
        """
        entity = self.repository.get_by_id(id)
        return {entity_class}OutDto.model_validate(entity) if entity else None
    
    def create_{entity_name}(self, {entity_name}_data: Create{entity_class}Dto) -> {entity_class}OutDto:
        """
        Create a new {entity_name}
        
        Args:
            {entity_name}_data (Create{entity_class}Dto): Data for creating the {entity_name}
            
        Returns:
            {entity_class}OutDto: The created {entity_name} as DTO
        """
        entity_data_dict = {entity_name}_data.model_dump()
        entity = self.repository.create(entity_data_dict)
        return {entity_class}OutDto.model_validate(entity)
    
    def update_{entity_name}(self, id: int, update_data: Update{entity_class}Dto) -> Optional[{entity_class}OutDto]:
        """
        Update an existing {entity_name}
        
        Args:
            id (int): The ID of the {entity_name} to update
            update_data (Update{entity_class}Dto): Data for updating the {entity_name}
            
        Returns:
            Optional[{entity_class}OutDto]: The updated {entity_name} as DTO if found, None otherwise
        """
        # Filter only non-None fields for update
        update_dict = {{key: value for key, value in update_data.model_dump().items() if value is not None}}
        
        if not update_dict:
            return None
            
        entity = self.repository.update(id, update_dict)
        return {entity_class}OutDto.model_validate(entity) if entity else None
    
    def delete_{entity_name}(self, id: int) -> bool:
        """
        Delete a {entity_name} by ID
        
        Args:
            id (int): The ID of the {entity_name} to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        return self.repository.delete(id)
''',

        f"{entity_name}_router.py": f'''# Router for {entity_name}
from fastapi import APIRouter, Depends, HTTPException, status
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
    """Dependency injection for {entity_class}Service"""
    repository = {entity_class}Repository(db)
    return {entity_class}Service(repository)


@router.get(
    "/",
    response_model=List[{entity_class}OutDto],
    summary="Get all {entity_name}s",
    description="Retrieve a list of all {entity_name} entities"
)
def get_all_{entity_name}s(
    service: {entity_class}Service = Depends(get_service)
) -> List[{entity_class}OutDto]:
    """
    Get all {entity_name}s
    
    Returns:
        List[{entity_class}OutDto]: List of all {entity_name} entities
    """
    return service.get_all_{entity_name}s()


@router.get(
    "/{{id}}",
    response_model={entity_class}OutDto,
    summary="Get {entity_name} by ID",
    description="Retrieve a specific {entity_name} by its ID"
)
def get_{entity_name}_by_id(
    id: int,
    service: {entity_class}Service = Depends(get_service)
) -> {entity_class}OutDto:
    """
    Get {entity_name} by ID
    
    Args:
        id (int): The ID of the {entity_name} to retrieve
        
    Returns:
        {entity_class}OutDto: The requested {entity_name}
        
    Raises:
        HTTPException: 404 if {entity_name} not found
    """
    entity = service.get_{entity_name}_by_id(id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{entity_class} not found"
        )
    return entity


@router.post(
    "/",
    response_model={entity_class}OutDto,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new {entity_name}",
    description="Create a new {entity_name} entity with the provided data"
)
def create_{entity_name}(
    {entity_name}_data: Create{entity_class}Dto,
    service: {entity_class}Service = Depends(get_service)
) -> {entity_class}OutDto:
    """
    Create a new {entity_name}
    
    Args:
        {entity_name}_data (Create{entity_class}Dto): Data for creating the {entity_name}
        
    Returns:
        {entity_class}OutDto: The created {entity_name}
    """
    return service.create_{entity_name}({entity_name}_data)


@router.patch(
    "/{{id}}",
    response_model={entity_class}OutDto,
    summary="Update a {entity_name}",
    description="Update an existing {entity_name} with the provided data (partial update)"
)
def update_{entity_name}(
    id: int,
    update_data: Update{entity_class}Dto,
    service: {entity_class}Service = Depends(get_service)
) -> {entity_class}OutDto:
    """
    Update a {entity_name}
    
    Args:
        id (int): The ID of the {entity_name} to update
        update_data (Update{entity_class}Dto): Data for updating the {entity_name}
        
    Returns:
        {entity_class}OutDto: The updated {entity_name}
        
    Raises:
        HTTPException: 404 if {entity_name} not found
        HTTPException: 400 if no data provided for update
    """
    # Check if there's any data to update
    update_dict = {{key: value for key, value in update_data.model_dump().items() if value is not None}}
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided for update"
        )
    
    entity = service.update_{entity_name}(id, update_data)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{entity_class} not found"
        )
    return entity


@router.delete(
    "/{{id}}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a {entity_name}",
    description="Delete a specific {entity_name} by its ID"
)
def delete_{entity_name}(
    id: int,
    service: {entity_class}Service = Depends(get_service)
):
    """
    Delete a {entity_name}
    
    Args:
        id (int): The ID of the {entity_name} to delete
        
    Raises:
        HTTPException: 404 if {entity_name} not found
    """
    success = service.delete_{entity_name}(id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{entity_class} not found"
        )
'''
    }


def get_dto_templates(entity_name: str) -> dict:
    """Plantillas para los archivos DTO (Pydantic v2)"""
    entity_class = entity_name.capitalize()

    return {
        f"{entity_name}_in_dto.py": f'''# Input DTO for {entity_name}
from pydantic import BaseModel, Field


class Create{entity_class}Dto(BaseModel):
    """
    Data Transfer Object for creating a {entity_name}
    
    Attributes:
        name (str): The name of the {entity_name}
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the {entity_name}",
        example="Example {entity_name} name"
    )

    model_config = {{
        "json_schema_extra": {{
            "example": {{
                "name": "Example {entity_name} name"
            }}
        }}
    }}
''',

        f"{entity_name}_update_dto.py": f'''# Update DTO for {entity_name}
from pydantic import BaseModel, Field
from typing import Optional


class Update{entity_class}Dto(BaseModel):
    """
    Data Transfer Object for updating a {entity_name}
    
    Attributes:
        name (Optional[str]): The name of the {entity_name} (optional for updates)
    """
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Name of the {entity_name}",
        example="Updated {entity_name} name"
    )

    model_config = {{
        "json_schema_extra": {{
            "example": {{
                "name": "Updated {entity_name} name"
            }}
        }}
    }}
''',

        f"{entity_name}_out_dto.py": f'''# Output DTO for {entity_name}
from pydantic import BaseModel, Field
from datetime import datetime


class {entity_class}OutDto(BaseModel):
    """
    Data Transfer Object for {entity_name} response
    
    Attributes:
        id (int): Unique identifier of the {entity_name}
        name (str): Name of the {entity_name}
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """
    id: int = Field(..., description="Unique identifier", example=1)
    name: str = Field(..., description="Name of the {entity_name}", example="Example {entity_name} name")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {{
        "from_attributes": True,
        "json_schema_extra": {{
            "example": {{
                "id": 1,
                "name": "Example {entity_name} name",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }}
        }}
    }}
'''
    }