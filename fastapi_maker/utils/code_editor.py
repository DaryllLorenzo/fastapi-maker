# ---------------------------------------------------
# Proyecto: fastapi-maker (fam)
# Autor: Daryll Lorenzo Alfonso
# Año: 2025
# Licencia: MIT License
# ---------------------------------------------------

from pathlib import Path
from typing import List, Optional, Tuple
from .line_locator import LineLocator

class CodeEditor:
    """Editor de código que usa LineLocator internamente."""
    
    def __init__(self, encoding: str = 'utf-8'):
        self.locator = LineLocator(encoding)
        self.encoding = encoding
    
    def read_lines(self, file_path: Path) -> List[str]:
        """Lee un archivo y retorna sus líneas."""
        return file_path.read_text(encoding=self.encoding).splitlines()
    
    ### TODO REVISAR QUE SE INSERTE UN SALTO DE LINEA AL FINAL
    def write_lines(self, file_path: Path, lines: List[str]):
        """Escribe líneas en un archivo con newline al final."""
        # Unir líneas y agregar newline al final
        content = "\n".join(lines) + "\n"
        file_path.write_text(content, encoding=self.encoding)
    
    def find_line(self, file_path: Path, content: str, 
                 function_name: Optional[str] = None) -> Optional[Tuple[int, int]]:
        """Encuentra una línea (1-indexed) y su indentación. Retorna None si no la encuentra."""
        try:
            return self.locator.locate(str(file_path), content, function_name)
        except (ValueError, FileNotFoundError):
            return None
    
    def insert_line(self, lines: List[str], content: str, 
                   position: Optional[int] = None, indent: int = 0) -> List[str]:
        """Inserta una línea en la posición dada con indentación."""
        if indent > 0:
            content = f'{" " * indent}{content}'
        
        if position is None or position < 0 or position > len(lines):
            lines.append(content)
        else:
            lines.insert(position, content)
        
        return lines
    
    def insert_after(self, lines: List[str], content: str, 
                    search_content: str, function_name: Optional[str] = None) -> List[str]:
        """Inserta una línea después de encontrar search_content."""
        # Crear archivo temporal para usar LineLocator
        temp_file = Path("__temp__.py")
        temp_file.write_text("\n".join(lines), encoding=self.encoding)
        
        try:
            result = self.find_line(temp_file, search_content, function_name)
            if result:
                line_num, _ = result
                # Insertar después de la línea encontrada
                return self.insert_line(lines, content, line_num)
        finally:
            if temp_file.exists():
                temp_file.unlink()
        
        return self.insert_line(lines, content)
    
    def insert_before(
        self,
        lines: List[str],
        content: str,
        search_content: str,
        function_name: Optional[str] = None,
        maintain_indent: bool = True,
        ensure_blank_line: bool = False
    ) -> List[str]:
        """
        Inserta una línea antes de encontrar search_content.
        
        Si `ensure_blank_line=True`, se asegura de que haya una línea vacía
        inmediatamente antes de `search_content`, e inserta `content` antes de esa línea vacía.
        """
        temp_file = Path("__temp__.py")
        temp_file.write_text("\n".join(lines), encoding=self.encoding)
    
        try:
            result = self.find_line(temp_file, search_content, function_name)
            if result:
                line_num, search_indent = result  # line_num es 1-indexed
                insert_pos = line_num - 1  # posición 0-indexed de la línea con search_content
    
                if ensure_blank_line:
                    # Verificar si ya hay una línea vacía justo antes
                    if insert_pos == 0 or lines[insert_pos - 1].strip() != "":
                        # Insertar línea vacía antes de search_content
                        lines.insert(insert_pos, "")
                        # Ahora el contenido debe ir antes de la línea vacía
                        insert_pos_for_content = insert_pos
                    else:
                        # Ya hay una línea vacía → insertar antes de ella
                        insert_pos_for_content = insert_pos - 1
                else:
                    # Comportamiento original: insertar inmediatamente antes
                    insert_pos_for_content = insert_pos
    
                # Determinar indentación
                indent = search_indent if maintain_indent else 0
    
                # Insertar contenido en la posición correcta
                if indent > 0:
                    content = f'{" " * indent}{content}'
    
                lines.insert(insert_pos_for_content, content)
                return lines
    
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
        # Si no se encuentra, insertar al final (comportamiento original)
        return self.insert_line(lines, content)
    
    def find_insert_position_in_class(self, file_path: Path, class_name: str) -> Tuple[int, int]:
        """Encuentra dónde insertar en una clase (antes del primer método o al final)."""
        lines = self.read_lines(file_path)
        
        # Buscar la clase
        class_line = self.find_line(file_path, f"class {class_name}")
        if not class_line:
            return len(lines), 0  # Insertar al final sin indentación extra
        
        class_line_num, class_indent = class_line
        
        # Buscar el primer método después de la clase
        method_line = self.find_line(file_path, "def ", class_name)
        if method_line:
            method_line_num, method_indent = method_line
            return method_line_num - 1, method_indent  # Insertar antes del método
        
        # Buscar el cierre de la clase
        closing_line = self.find_line(file_path, "}", class_name)
        if closing_line:
            closing_line_num, _ = closing_line
            return closing_line_num - 1, class_indent + 4  # Insertar antes del cierre con indentación de clase
        
        return len(lines), class_indent + 4
    
    def ensure_import(self, lines: List[str], import_statement: str) -> List[str]:
        """Asegura que un import esté presente."""
        if any(import_statement in line for line in lines):
            return lines
        
        # Buscar última importación
        last_import = -1
        for i, line in enumerate(lines):
            if line.startswith(("import ", "from ")):
                last_import = i
        
        if last_import >= 0:
            lines.insert(last_import + 1, import_statement)
        else:
            # Buscar dónde insertar (después de docstring si existe)
            for i, line in enumerate(lines):
                if not line.startswith(('"""', "'''")):
                    lines.insert(i, import_statement)
                    break
            else:
                lines.insert(0, import_statement)
        
        return lines
    
    def ensure_content(self, lines: List[str], content: str) -> bool:
        """Verifica si contenido existe en las líneas."""
        return any(content in line for line in lines)