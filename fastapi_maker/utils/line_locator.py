# ---------------------------------------------------
# Proyecto: fastapi-maker (fam)
# Autor: Daryll Lorenzo Alfonso
# Año: 2025
# Licencia: MIT License
# ---------------------------------------------------

from pathlib import Path
from typing import Optional, Tuple
import re


class LineLocator:
    """
    Clase para localizar líneas específicas en archivos de código.
    Puede buscar globalmente o dentro de funciones específicas.
    """
    
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding
    
    def locate(self, file_path: str, content: str, function_name: Optional[str] = None) -> Tuple[int, int]:
        """
        Localiza una línea que contiene el texto especificado.
        
        Args:
            file_path: Ruta al archivo
            content: Texto a buscar en la línea
            function_name: Nombre de la función donde buscar (None para búsqueda global)
            
        Returns:
            Tupla (número_de_línea, indentación)
        """
        if function_name is None:
            return self._locate_global(file_path, content)
        else:
            return self._locate_in_function(file_path, content, function_name)
    
    def _locate_global(self, file_path: str, content: str) -> Tuple[int, int]:
        """
        Busca globalmente la primera línea que contenga el texto.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        lines = path.read_text(encoding=self.encoding).splitlines()
        
        for i, line in enumerate(lines, 1):
            if content in line:
                indent = len(line) - len(line.lstrip())
                return i, indent
        
        raise ValueError(f"No se encontró '{content}' en {file_path}")
    
    def _locate_in_function(self, file_path: str, content: str, function_name: str) -> Tuple[int, int]:
        """
        Busca la línea que contenga el texto dentro de una función específica.
        
        1. Primero localiza la función por su nombre.
        2. Luego busca el contenido dentro del cuerpo de esa función.
        """
        path = Path(file_path)
        lines = path.read_text(encoding=self.encoding).splitlines()
        
        # 1. Localizar la función
        func_line = None
        func_indent = None
        
        func_pattern = re.compile(r'^\s*def\s+' + re.escape(function_name) + r'\s*\(')
        
        for i, line in enumerate(lines):
            if func_pattern.match(line):
                func_line = i  # Índice basado en 0
                func_indent = len(line) - len(line.lstrip())
                break
        
        if func_line is None:
            raise ValueError(f"No se encontró la función '{function_name}' en {file_path}")
        
        # 2. Buscar dentro del cuerpo de la función
        in_function = False
        
        for i in range(func_line + 1, len(lines)):
            line = lines[i]
            current_indent = len(line) - len(line.lstrip())
            
            # Si encontramos una línea con igual o menor indentación (y no está vacía),
            # hemos salido de la función
            if line.strip() and current_indent <= func_indent:
                # Pero solo si no estamos todavía en la primera línea después de 'def'
                if in_function:
                    break
            
            # Estamos dentro del cuerpo de la función
            in_function = True
            
            # Buscar el contenido
            if content in line:
                return i + 1, current_indent  # +1 porque los usuarios esperan línea 1-indexada
        
        raise ValueError(f"No se encontró '{content}' en el cuerpo de la función '{function_name}'")
    
    # Método para uso rápido
    @staticmethod
    def quick_locate(file_path: str, content: str, function_name: Optional[str] = None) -> Tuple[int, int]:
        """
        Método estático para uso rápido sin instanciar la clase.
        
        Ejemplo:
            line, indent = LineLocator.quick_locate("mi_archivo.py", "mi_variable =", "mi_funcion")
        """
        locator = LineLocator()
        return locator.locate(file_path, content, function_name)