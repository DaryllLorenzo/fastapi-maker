"""
Módulo para actualizar automáticamente las descripciones de los routers
después de crear relaciones.
"""

import typer
from pathlib import Path
from typing import List, Optional
from fastapi_maker.utils.code_editor import CodeEditor
from fastapi_maker.utils.dto_checker import DTOFieldChecker
import re


class RouterUpdater:
    def __init__(self):
        self.base_path = Path("app/api")
        self.editor = CodeEditor()
    
    def update_all_routers_descriptions(self):
        """Actualiza las descripciones de todos los routers en el proyecto."""
        typer.echo("\n🔄 Actualizando descripciones de routers...")
        
        entities = []
        for entity_dir in self.base_path.iterdir():
            if entity_dir.is_dir():
                router_path = entity_dir / f"{entity_dir.name}_router.py"
                in_dto_path = entity_dir / "dto" / f"{entity_dir.name}_in_dto.py"
                update_dto_path = entity_dir / "dto" / f"{entity_dir.name}_update_dto.py"
                
                if router_path.exists() and in_dto_path.exists():
                    entities.append({
                        "name": entity_dir.name,
                        "router_path": router_path,
                        "in_dto_path": in_dto_path,
                        "update_dto_path": update_dto_path if update_dto_path.exists() else None
                    })
        
        for entity_info in entities:
            self._update_router_descriptions(entity_info)
        
        typer.echo("\n✅ Todas las descripciones de routers han sido actualizadas!")
    
    def _update_router_descriptions(self, entity_info: dict):
        """Actualiza las descripciones del router de una entidad específica."""
        entity_name = entity_info["name"]
        router_path = entity_info["router_path"]
        
        try:
            # Leer el router
            lines = self.editor.read_lines(router_path)
            
            # Obtener descripción del DTO de creación
            create_desc = DTOFieldChecker.generate_description_from_dto(entity_info["in_dto_path"])
            lines = self._update_description_in_decorator(lines, "create", entity_name, create_desc)
            
            # Obtener descripción del DTO de actualización (si existe)
            if entity_info["update_dto_path"] and entity_info["update_dto_path"].exists():
                update_desc = DTOFieldChecker.generate_description_from_dto(entity_info["update_dto_path"])
                lines = self._update_description_in_decorator(lines, "update", entity_name, update_desc)
            
            # Guardar cambios
            self.editor.write_lines(router_path, lines)
            typer.echo(f"  ✅ Router actualizado para {entity_name}")
            
        except Exception as e:
            typer.echo(f"  ⚠️  Error actualizando router de {entity_name}: {e}")
    
    def _update_description_in_decorator(
        self,
        lines: List[str],
        endpoint_type: str,
        entity_name: str,
        new_description: str
    ) -> List[str]:
        i = 0
        while i < len(lines):
            # Buscar decorador correcto
            is_create = endpoint_type == "create" and "@router.post(" in lines[i]
            is_update = endpoint_type == "update" and "@router.patch(" in lines[i]

            if not (is_create or is_update):
                i += 1
                continue

            # Encontrar función objetivo
            func_name = f"def {endpoint_type}_{entity_name}"
            j = i + 1
            while j < len(lines) and func_name not in lines[j]:
                j += 1

            if j >= len(lines):
                i += 1
                continue

            # Buscar bloque completo del decorador (desde @router hasta el paréntesis de cierre)
            block_start = i
            block_end = -1
            paren_count = 0

            for k in range(i, j + 1):
                line = lines[k]
                paren_count += line.count('(') - line.count(')')

                if paren_count == 0 and ')' in line and '@router' not in line:
                    block_end = k
                    break
                
            if block_end == -1:
                i += 1
                continue

            # Extraer y modificar el bloque
            decorator_block = lines[block_start:block_end + 1]
            new_block = []
            in_description = False

            for line in decorator_block:
                stripped = line.strip()
                # Eliminar descripción antigua (soporta multi-line)
                if stripped.startswith("description=") or in_description:
                    if '"""' in line or "'''" in line:
                        if in_description:
                            in_description = False
                        else:
                            in_description = True
                    continue
                
                new_block.append(line)

            # Insertar nueva descripción (con formato multi-line seguro)
            indent = " " * 4
            formatted_desc = "\n".join([f"{indent}{part}" for part in new_description.splitlines()])
            new_block.insert(-1, f'{indent}description="""\n{formatted_desc}\n{indent}""",')

            # Reemplazar bloque original
            lines = lines[:block_start] + new_block + lines[block_end + 1:]
            i = block_end + 1

        return lines