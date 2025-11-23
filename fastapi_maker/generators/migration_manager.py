# ---------------------------------------------------
# Proyecto: fastapi-maker (fam)
# Autor: Daryll Lorenzo Alfonso
# Año: 2025
# Licencia: MIT License
# ---------------------------------------------------

import subprocess
import sys
import typer


class MigrationManager:
    """Clase para manejar operaciones de migración de Alembic."""

    @staticmethod
    def run_migrations(message: str = None) -> None:
        """
        Ejecuta alembic revision --autogenerate (con mensaje opcional) y alembic upgrade head.

        Args:
            message: Mensaje opcional para la revisión de migración.

        Raises:
            typer.Exit: Si cualquiera de los comandos de alembic falla.
        """
        try:
            # Construir el comando de revision con autogenerate
            revision_cmd = [sys.executable, "-m", "alembic", "revision", "--autogenerate"]
            if message:
                revision_cmd.extend(["-m", message])

            typer.echo("Ejecutando alembic revision --autogenerate...")
            result = subprocess.run(revision_cmd, check=True, capture_output=True, text=True)
            typer.echo(result.stdout)
            if result.stderr:
                typer.echo(result.stderr, err=True)

            typer.echo("Ejecutando alembic upgrade head...")
            upgrade_cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
            result = subprocess.run(upgrade_cmd, check=True, capture_output=True, text=True)
            typer.echo(result.stdout)
            if result.stderr:
                typer.echo(result.stderr, err=True)

            typer.echo("Migraciones aplicadas exitosamente.")

        except subprocess.CalledProcessError as e:
            typer.echo(f"Error al ejecutar el comando de alembic: {e.cmd}", err=True)
            typer.echo(f"Salida estándar: {e.stdout}", err=True)
            typer.echo(f"Salida de error: {e.stderr}", err=True)
            raise typer.Exit(code=1) # Levanta la excepción para que el CLI maneje la salida
        except Exception as e:
            typer.echo(f"Error inesperado durante las migraciones: {str(e)}", err=True)
            raise typer.Exit(code=1) # Levanta la excepción para que el CLI maneje la salida
