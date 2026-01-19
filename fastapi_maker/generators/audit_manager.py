"""
Auditor de dependencias para FastAPI Maker.
Usa pip-audit internamente para detectar vulnerabilidades.
"""

import sys
from pathlib import Path
import typer

class AuditManager:
    """Manager minimalista para auditoría de dependencias."""
    
    def __init__(self, fix_mode: bool = False):
        self.fix_mode = fix_mode
    
    def run_audit(self) -> bool:
        """
        Ejecuta la auditoría usando pip-audit.
        Retorna True si hay vulnerabilidades encontradas.
        """
        typer.echo("Ejecutando auditoría de dependencias...")
        
        # Verificar que requirements.txt existe
        if not Path("requirements.txt").exists():
            typer.echo(" Error: No se encontró requirements.txt")
            typer.echo("   Ejecuta: fam init para crear la estructura del proyecto")
            return True
        
        # Construir comando para pip-audit
        cmd = [sys.executable, "-m", "pip_audit", "-r", "requirements.txt"]
        
        # Agregar --fix si se solicitó
        if self.fix_mode:
            cmd.append("--fix")
            typer.echo(" Modo corrección activado")
        
        # Ejecutar pip-audit
        try:
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Mostrar salida
            if result.stdout:
                typer.echo(result.stdout)
            
            # Mostrar errores si los hay
            if result.stderr and "error" in result.stderr.lower():
                typer.echo(f" {result.stderr}")
            
            # pip-audit retorna 1 si encuentra vulnerabilidades
            # retorna 0 si no hay vulnerabilidades o si corrigió exitosamente
            if result.returncode == 1:
                typer.echo("\n Se encontraron vulnerabilidades.")
                if not self.fix_mode:
                    typer.echo("  Ejecuta 'fam audit --fix' para intentar corregirlas.")
                return True
            elif result.returncode == 0:
                if self.fix_mode:
                    typer.echo("\n Vulnerabilidades corregidas exitosamente.")
                    typer.echo("   Recuerda ejecutar: pip install -r requirements.txt --upgrade")
                else:
                    typer.echo("\n No se encontraron vulnerabilidades.")
                return False
            else:
                # Otro código de error
                typer.echo(f"\n pip-audit terminó con código: {result.returncode}")
                return True
                
        except Exception as e:
            typer.echo(f" Error inesperado: {e}")
            return True