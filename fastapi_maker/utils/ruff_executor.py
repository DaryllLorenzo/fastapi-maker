"""
Ejecutor de Ruff para FastAPI Maker.
Maneja toda la lógica de ejecución del linter/formatter.
"""
import subprocess
import sys
from pathlib import Path
import typer

class RuffExecutor:
    """Ejecuta comandos de Ruff con diferentes opciones."""
    
    @staticmethod
    def check_ruff_installed():
        """Verifica si ruff está instalado."""
        try:
            import ruff
            return True
        except ImportError:
            return False
    
    @staticmethod
    def ensure_config_exists():
        """Asegura que la configuración de Ruff existe."""
        ruff_config = Path("pyproject.toml")
        if not ruff_config.exists():
            typer.echo("⚠️  No se encontró pyproject.toml. Generando configuración de Ruff...")
            from fastapi_maker.generators.ruff_config import RuffConfigGenerator
            RuffConfigGenerator.generate_ruff_config()
    
    @staticmethod
    def run_command(cmd_parts, description):
        """Ejecuta un comando y maneja la salida."""
        typer.echo(f"▶️  {description}: {' '.join(cmd_parts)}")
        result = subprocess.run(cmd_parts)
        return result
    
    @staticmethod
    def execute_all():
        """Ejecuta todas las operaciones: lint con fix y format."""
        typer.echo("🔍 Ejecutando lint y format completo...")
        
        # Primero lint con fix
        lint_result = RuffExecutor.run_command(
            ["ruff", "check", "--fix"],
            "Intentando arreglar problemas automáticamente"
        )
        
        if lint_result.returncode != 0:
            typer.echo("⚠️  Algunos problemas de linting no se pudieron arreglar automáticamente")
        
        # Luego format
        RuffExecutor.run_command(
            ["ruff", "format"],
            "Aplicando formato al código"
        )
        
        typer.echo("✅ Lint y format completados!")
    
    @staticmethod
    def execute_check_only():
        """Solo verifica sin cambios."""
        RuffExecutor.run_command(
            ["ruff", "check"],
            "Verificando código (modo check)"
        )
    
    @staticmethod
    def execute_fix():
        """Intenta arreglar problemas automáticamente."""
        RuffExecutor.run_command(
            ["ruff", "check", "--fix"],
            "Intentando arreglar problemas automáticamente"
        )
    
    @staticmethod
    def execute_format():
        """Aplica formato al código."""
        RuffExecutor.run_command(
            ["ruff", "format"],
            "Aplicando formato al código"
        )
    
    @staticmethod
    def execute_default():
        """Ejecuta el modo por defecto: check + format."""
        typer.echo("🔍 Ejecutando lint y format...")
        
        # Primero lint (solo check)
        lint_result = RuffExecutor.run_command(
            ["ruff", "check"],
            "Verificando código"
        )
        
        # Luego format
        format_result = RuffExecutor.run_command(
            ["ruff", "format"],
            "Aplicando formato"
        )
        
        if lint_result.returncode == 0 and format_result.returncode == 0:
            typer.echo("✅ Lint y format completados exitosamente!")
        else:
            typer.echo("⚠️  Completado con advertencias o errores")
    
    @staticmethod
    def execute(check=False, fix=False, format_cmd=False, all_ops=False):
        """
        Punto de entrada principal para ejecutar Ruff.
        
        Args:
            check: Solo verifica sin cambios
            fix: Intenta arreglar problemas automáticamente
            format_cmd: Aplica formato al código
            all_ops: Ejecuta todas las operaciones
        """
        # Verificar instalación
        if not RuffExecutor.check_ruff_installed():
            typer.echo("❌ Ruff no está instalado.")
            typer.echo("💡 Instala ruff: pip install ruff")
            typer.echo("   o usa: pip install 'fastapi-maker[lint]' si configuras extras")
            raise typer.Exit(1)
        
        # Asegurar configuración
        RuffExecutor.ensure_config_exists()
        
        # Ejecutar según opciones
        if all_ops:
            RuffExecutor.execute_all()
        elif check:
            RuffExecutor.execute_check_only()
        elif fix:
            RuffExecutor.execute_fix()
        elif format_cmd:
            RuffExecutor.execute_format()
        else:
            RuffExecutor.execute_default()