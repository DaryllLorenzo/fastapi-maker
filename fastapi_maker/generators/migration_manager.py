# ---------------------------------------------------
# Proyecto: fastapi-maker (fam)
# Autor: Daryll Lorenzo Alfonso
# Año: 2025
# Licencia: MIT License
# ---------------------------------------------------

import subprocess
import sys
import typer
import os
from pathlib import Path
import sqlite3
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class MigrationManager:
    """Clase para manejar operaciones de migración de Alembic."""

    @staticmethod
    def _get_database_url() -> str:
        """
        Obtiene la URL de la base de datos desde las variables de entorno.
        
        Returns:
            str: URL de la base de datos
        """

        return os.getenv("DATABASE_URL", "sqlite:///./app.db")

    @staticmethod
    def _create_sqlite_database(db_url: str) -> bool:
        """
        Crea la base de datos SQLite si no existe.
        
        Args:
            db_url: URL de la base de datos SQLite
            
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            # Extraer la ruta del archivo de la URL
            if db_url.startswith("sqlite:///"):
                db_path = db_url.replace("sqlite:///", "")
            else:
                db_path = db_url.replace("sqlite://", "")
            
            # Convertir a Path y crear directorios padres si es necesario
            db_file = Path(db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Solo crear la base de datos si no existe
            if not db_file.exists():
                conn = sqlite3.connect(db_file)
                conn.close()
                typer.echo(f" Base de datos SQLite creada: {db_file}")
            else:
                typer.echo(f" Base de datos SQLite ya existe: {db_file}")
                
            return True
            
        except Exception as e:
            typer.echo(f" Error creando base de datos SQLite: {str(e)}", err=True)
            return False

    @staticmethod
    def _create_postgres_database(db_url: str) -> bool:
        """
        Crea la base de datos PostgreSQL si no existe.
        
        Args:
            db_url: URL de conexión a PostgreSQL
            
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            # Importar psycopg2 solo cuando sea necesario
            import psycopg2
            from urllib.parse import urlparse
            
            parsed = urlparse(db_url)
            db_name = parsed.path[1:]  # Remover el '/' inicial
            
            # Conectar a la base de datos por defecto (postgres) para crear la nueva
            default_url = db_url.replace(f"/{db_name}", "/postgres")
            
            conn = psycopg2.connect(default_url)
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Verificar si la base de datos ya existe
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                typer.echo(f" Base de datos PostgreSQL creada: {db_name}")
            else:
                typer.echo(f" Base de datos PostgreSQL ya existe: {db_name}")
            
            cursor.close()
            conn.close()
            return True
            
        except ImportError:
            typer.echo(" psycopg2-binary no está instalado. Instala con: pip install psycopg2-binary", err=True)
            return False
        except Exception as e:
            typer.echo(f" Error creando base de datos PostgreSQL: {str(e)}", err=True)
            return False

    @staticmethod
    def _create_mysql_database(db_url: str) -> bool:
        """
        Crea la base de datos MySQL si no existe.
        
        Args:
            db_url: URL de conexión a MySQL
            
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            # Importar MySQLdb (mysqlclient) solo cuando sea necesario
            import MySQLdb
            from urllib.parse import urlparse
            
            parsed = urlparse(db_url)
            db_name = parsed.path[1:]  # Remover el '/' inicial
            
            # Extraer credenciales
            username = parsed.username or "root"
            password = parsed.password or ""
            host = parsed.hostname or "localhost"
            port = parsed.port or 3306
            
            # Conectar sin especificar base de datos para crear la nueva
            conn = MySQLdb.connect(
                host=host,
                user=username,
                password=password,
                port=port
            )
            cursor = conn.cursor()
            
            # Verificar si la base de datos ya existe
            cursor.execute("SHOW DATABASES LIKE %s", (db_name,))
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(f"CREATE DATABASE `{db_name}`")
                typer.echo(f" Base de datos MySQL creada: {db_name}")
            else:
                typer.echo(f" Base de datos MySQL ya existe: {db_name}")
            
            cursor.close()
            conn.close()
            return True
            
        except ImportError:
            typer.echo(" mysqlclient no está instalado. Instala con: pip install mysqlclient", err=True)
            return False
        except Exception as e:
            typer.echo(f" Error creando base de datos MySQL: {str(e)}", err=True)
            return False

    @staticmethod
    def _ensure_database_exists() -> bool:
        """
        Verifica si la base de datos existe y la crea si es necesario.
        
        Returns:
            bool: True si la base de datos existe o fue creada exitosamente
        """
        try:
            db_url = MigrationManager._get_database_url()
            
            if not db_url:
                typer.echo(" DATABASE_URL no está configurada", err=True)
                return False
            
            typer.echo(f" URL de base de datos: {db_url}")
            
            if db_url.startswith("sqlite://"):
                return MigrationManager._create_sqlite_database(db_url)
            elif db_url.startswith("postgresql://"):
                return MigrationManager._create_postgres_database(db_url)
            elif db_url.startswith("mysql://"):
                return MigrationManager._create_mysql_database(db_url)
            else:
                typer.echo(f" Tipo de base de datos no reconocido: {db_url}")
                typer.echo("  Continuando sin crear la base de datos...")
                return True
                
        except Exception as e:
            typer.echo(f" Error verificando base de datos: {str(e)}", err=True)
            typer.echo("  Continuando sin crear la base de datos...")
            return True

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
            # Verificar y crear la base de datos si es necesario
            typer.echo(" Verificando base de datos...")
            database_ready = MigrationManager._ensure_database_exists()
            
            if not database_ready:
                typer.echo(" No se pudo crear/verificar la base de datos", err=True)
                if not typer.confirm("¿Continuar con las migraciones de todos modos?"):
                    typer.echo("Migraciones canceladas.")
                    raise typer.Exit(code=1)

            # Construir el comando de revision con autogenerate
            revision_cmd = [sys.executable, "-m", "alembic", "revision", "--autogenerate"]
            if message:
                revision_cmd.extend(["-m", message])

            typer.echo(" Ejecutando alembic revision --autogenerate...")
            result = subprocess.run(revision_cmd, check=True, capture_output=True, text=True)
            if result.stdout:
                typer.echo(result.stdout)
            if result.stderr:
                typer.echo(result.stderr, err=True)

            typer.echo(" Ejecutando alembic upgrade head...")
            upgrade_cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
            result = subprocess.run(upgrade_cmd, check=True, capture_output=True, text=True)
            if result.stdout:
                typer.echo(result.stdout)
            if result.stderr:
                typer.echo(result.stderr, err=True)

            typer.echo(" Migraciones aplicadas exitosamente.")

        except subprocess.CalledProcessError as e:
            typer.echo(f" Error al ejecutar el comando de alembic: {e.cmd}", err=True)
            if e.stdout:
                typer.echo(f"Salida estándar: {e.stdout}", err=True)
            if e.stderr:
                typer.echo(f"Salida de error: {e.stderr}", err=True)
            raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(f" Error inesperado durante las migraciones: {str(e)}", err=True)
            raise typer.Exit(code=1)