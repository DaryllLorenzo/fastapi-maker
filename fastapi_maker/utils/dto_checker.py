"""
Módulo para analizar y extraer información de campos DTO de Pydantic.
"""

import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class DTOFieldChecker:
    """
    Clase para analizar archivos DTO de Pydantic y extraer información de campos.
    """
    
    @staticmethod
    def parse_dto_file(file_path: Path) -> Dict[str, Dict]:
        """
        Analiza un archivo DTO y extrae información de campos.
        """
        if not file_path.exists():
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return DTOFieldChecker.parse_dto_content(content)
    

    @staticmethod
    def parse_dto_content(content: str) -> Dict[str, Dict]:
        fields = {}
        inside_class = False
        lines = content.split('\n')

        for line in lines:
            line_stripped = line.strip()

            if line_stripped.startswith('class '):
                inside_class = True
                continue
            
            if inside_class and ('model_config' in line_stripped or 'Config:' in line_stripped or line_stripped == ""):
                continue
            
            if inside_class and line_stripped:
                # Nueva regex que captura campos con/sin asignación
                match = re.match(r'^(\w+)\s*:\s*([\w\[\]\.\|\s]+?)(?:\s*=\s*(.*))?$', line_stripped)
                if match:
                    field_name = match.group(1).strip()
                    field_type = match.group(2).strip()
                    default_expr = match.group(3) if match.group(3) else None

                    # Determinar si es requerido
                    required = True
                    if default_expr:
                        if "..." in default_expr or "Field(..." in default_expr:
                            required = True
                        else:
                            required = False
                    elif "Optional[" in field_type or "| None" in field_type:
                        required = False

                    fields[field_name] = {
                        "name": field_name,
                        "type": field_type,
                        "required": required
                    }

        return fields
    
    @staticmethod
    def get_field_requirements(fields: Dict[str, Dict]) -> Tuple[List[str], List[str]]:
        """
        Separa campos en requeridos y opcionales.
        """
        required = []
        optional = []
        
        for field_name, field_info in fields.items():
            if field_info["required"]:
                required.append(field_name)
            else:
                optional.append(field_name)
        
        return required, optional
    
    @staticmethod
    def get_dto_description(dto_path: Path) -> Tuple[str, str]:
        """
        Obtiene la descripción de campos requeridos y opcionales de un DTO.
        
        Args:
            dto_path: Ruta al archivo DTO
            
        Returns:
            Tuple (required_str, optional_str)
        """
        fields = DTOFieldChecker.parse_dto_file(dto_path)
        required, optional = DTOFieldChecker.get_field_requirements(fields)
        
        # Formatear como strings
        required_str = ", ".join(required) if required else "None"
        optional_str = ", ".join(optional) if optional else "None"
        
        return required_str, optional_str
    
    @staticmethod
    def generate_description_from_dto(dto_path: Path) -> str:
        """
        Genera la descripción de campos para un endpoint a partir del DTO.
        
        Args:
            dto_path: Ruta al archivo DTO
            
        Returns:
            String con la descripción formateada
        """
        required_str, optional_str = DTOFieldChecker.get_dto_description(dto_path)
    
        return f"**Required fields**: {required_str}\n**Optional fields**: {optional_str}"