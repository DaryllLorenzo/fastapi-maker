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
from urllib.parse import urlparse
from dotenv import load_dotenv

class MigrationManager:
    """Clase para manejar operaciones de migración de Alembic."""

    @staticmethod
    def _load_env_from_project_root():
        """Busca y carga el archivo .env desde el directorio actual o padres."""
        current_path = Path.cwd()
        
        # Buscar .env en el directorio actual y padres
        while current_path != current_path.parent:
            env_file = current_path / ".env"
            if env_file.exists():
                load_dotenv(dotenv_path=env_file)
                #typer.echo(f" Cargando variables de entorno desde: {env_file}")
                return True
            current_path = current_path.parent
        
        # Si no se encuentra, buscar en el directorio actual del script
        script_env = Path(__file__).parent.parent / ".env"
        if script_env.exists():
            load_dotenv(dotenv_path=script_env)
            #typer.echo(f" Cargando variables de entorno desde: {script_env}")
            return True
            
        return False

    @staticmethod
    def _get_database_url() -> str:
        """
        Obtiene la URL de la base de datos desde las variables de entorno.
        
        Returns:
            str: URL de la base de datos
        """
        # Primero cargar el .env si existe
        MigrationManager._load_env_from_project_root()
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            typer.echo("   DATABASE_URL no está configurada en el archivo .env")
            typer.echo("   Usando base de datos SQLite por defecto...")
            db_url = "sqlite:///./app.db"
        
        return db_url

    @staticmethod
    def _get_database_type(db_url: str) -> str:
        """
        Determina el tipo de base de datos a partir de la URL.
        
        Args:
            db_url: URL de conexión
            
        Returns:
            str: 'sqlite', 'postgresql', 'mysql' o 'desconocido'
        """
        db_url = db_url.lower()
        if db_url.startswith("sqlite://"):
            return "sqlite"
        elif db_url.startswith("postgresql://") or db_url.startswith("postgres://"):
            return "postgresql"
        elif db_url.startswith("mysql://") or db_url.startswith("mysql+pymysql://"):
            return "mysql"
        else:
            return "desconocido"

    @staticmethod
    def _create_sqlite_database(db_path: str) -> bool:
        """
        Crea la base de datos SQLite si no existe.
        
        Args:
            db_path: Ruta al archivo de la base de datos
            
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            db_file = Path(db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
            
            if not db_file.exists():
                conn = sqlite3.connect(str(db_file))
                conn.close()
                typer.echo(f"  Base de datos SQLite creada: {db_file}")
            else:
                typer.echo(f"   Base de datos SQLite ya existe: {db_file}")
                
            return True
            
        except Exception as e:
            typer.echo(f"  Error creando base de datos SQLite: {str(e)}", err=True)
            return False

    @staticmethod
    def _check_postgres_dependencies() -> bool:
        """Verifica que las dependencias para PostgreSQL estén instaladas."""
        try:
            import psycopg2
            return True
        except ImportError:
            typer.echo("  psycopg2-binary no está instalado", err=True)
            typer.echo("   Para usar PostgreSQL, instala: pip install psycopg2-binary", err=True)
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
        if not MigrationManager._check_postgres_dependencies():
            return False

        try:
            import psycopg2
            
            parsed = urlparse(db_url)
            db_name = parsed.path[1:]  # Remover el '/' inicial
            if not db_name:
                typer.echo("  No se especificó el nombre de la base de datos en la URL", err=True)
                return False

            # Conectar a la base de datos por defecto (postgres) para crear la nueva
            default_url = db_url.split('/' + db_name)[0] + '/postgres'
            
            try:
                conn = psycopg2.connect(default_url)
            except psycopg2.OperationalError as e:
                # Intentar con la base de datos template1 como fallback
                default_url = db_url.split('/' + db_name)[0] + '/template1'
                try:
                    conn = psycopg2.connect(default_url)
                except psycopg2.OperationalError as e2:
                    typer.echo(f"  No se pudo conectar a PostgreSQL: {str(e2)}", err=True)
                    typer.echo("   Verifica que el servidor PostgreSQL esté ejecutándose", err=True)
                    return False
            
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Verificar si la base de datos ya existe
            cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                typer.echo(f"  Base de datos PostgreSQL creada: {db_name}")
            else:
                typer.echo(f"   Base de datos PostgreSQL ya existe: {db_name}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            typer.echo(f"  Error creando base de datos PostgreSQL: {str(e)}", err=True)
            return False

    @staticmethod
    def _check_mysql_dependencies() -> bool:
        """Verifica que las dependencias para MySQL estén instaladas."""
        try:
            import MySQLdb
            return True
        except ImportError:
            typer.echo("  mysqlclient no está instalado", err=True)
            typer.echo("   Para usar MySQL, instala: pip install mysqlclient", err=True)
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
        if not MigrationManager._check_mysql_dependencies():
            return False

        try:
            import MySQLdb
            
            parsed = urlparse(db_url)
            db_name = parsed.path[1:]  # Remover el '/' inicial
            if not db_name:
                typer.echo("  No se especificó el nombre de la base de datos en la URL", err=True)
                return False
            
            # Extraer credenciales
            username = parsed.username or "root"
            password = parsed.password or ""
            host = parsed.hostname or "localhost"
            port = parsed.port or 3306
            
            # Conectar sin especificar base de datos para crear la nueva
            try:
                conn = MySQLdb.connect(
                    host=host,
                    user=username,
                    password=password,
                    port=port
                )
            except MySQLdb._exceptions.OperationalError as e:
                typer.echo(f"  No se pudo conectar a MySQL: {str(e)}", err=True)
                typer.echo("   Verifica que el servidor MySQL esté ejecutándose", err=True)
                return False
            
            cursor = conn.cursor()
            
            # Verificar si la base de datos ya existe
            cursor.execute("SHOW DATABASES LIKE %s", (db_name,))
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                typer.echo(f"  Base de datos MySQL creada: {db_name}")
            else:
                typer.echo(f"   Base de datos MySQL ya existe: {db_name}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            typer.echo(f"  Error creando base de datos MySQL: {str(e)}", err=True)
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
            db_type = MigrationManager._get_database_type(db_url)
            
            if db_type == "sqlite":
                # Extraer la ruta del archivo de la URL
                if db_url.startswith("sqlite:///"):
                    db_path = db_url.replace("sqlite:///", "")
                else:
                    db_path = db_url.replace("sqlite://", "")
                return MigrationManager._create_sqlite_database(db_path)
                
            elif db_type == "postgresql":
                return MigrationManager._create_postgres_database(db_url)
                
            elif db_type == "mysql":
                return MigrationManager._create_mysql_database(db_url)
                
            else:
                typer.echo(f"   Tipo de base de datos no reconocido: {db_type}", err=True)
                typer.echo("   Continuando sin crear la base de datos...", err=True)
                return True
                
        except Exception as e:
            typer.echo(f"  Error verificando base de datos: {str(e)}", err=True)
            typer.echo("   Continuando sin crear la base de datos...", err=True)
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
            typer.echo("🔍 Verificando base de datos...")
            database_ready = MigrationManager._ensure_database_exists()
            
            if not database_ready:
                typer.echo("  No se pudo crear/verificar la base de datos", err=True)
                if not typer.confirm("¿Continuar con las migraciones de todos modos?", default=False):
                    typer.echo("  Migraciones canceladas.")
                    raise typer.Exit(code=1)

            # Construir el comando de revision con autogenerate
            revision_cmd = [sys.executable, "-m", "alembic", "revision", "--autogenerate"]
            if message:
                revision_cmd.extend(["-m", message])

            typer.echo("\n  Ejecutando alembic revision --autogenerate...")
            result = subprocess.run(revision_cmd, check=True, capture_output=True, text=True)
            if result.stdout:
                typer.echo(result.stdout)
            if result.stderr:
                typer.echo(result.stderr, err=True)

            typer.echo("\n  Ejecutando alembic upgrade head...")
            upgrade_cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
            result = subprocess.run(upgrade_cmd, check=True, capture_output=True, text=True)
            if result.stdout:
                typer.echo(result.stdout)
            if result.stderr:
                typer.echo(result.stderr, err=True)

            typer.echo("\n  Migraciones aplicadas exitosamente.")

        except subprocess.CalledProcessError as e:
            typer.echo(f"\n  Error al ejecutar el comando de alembic: {e.cmd}", err=True)
            if e.stdout:
                typer.echo(f"Salida estándar:\n{e.stdout}", err=True)
            if e.stderr:
                typer.echo(f"Salida de error:\n{e.stderr}", err=True)
            raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(f"\n  Error inesperado durante las migraciones: {str(e)}", err=True)
            raise typer.Exit(code=1)