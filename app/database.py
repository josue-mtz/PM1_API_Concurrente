"""
Manejo de la conexión asíncrona a MongoDB Atlas usando Motor.
La conexión se abre/cierra dentro del ciclo de vida (lifespan) de FastAPI,
definido en main.py.
"""
import os

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import OperationFailure


class _DataBase:
    client: AsyncIOMotorClient | None = None
    db = None


_database = _DataBase()


async def connect_to_mongo() -> None:
    """Abre la conexión con MongoDB Atlas. Se llama al iniciar la app (lifespan)."""
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME", "pizzas_animatronicos")

    if not mongo_uri:
        raise RuntimeError(
            "MONGO_URI no está definida. Crea un archivo .env a partir de "
            ".env.example y agrega tu cadena de conexión de MongoDB Atlas."
        )

    _database.client = AsyncIOMotorClient(mongo_uri)
    _database.db = _database.client[db_name]

    try:
        # Verifica las credenciales antes de aceptar solicitudes.
        await _database.client.admin.command("ping")
    except OperationFailure as exc:
        _database.client.close()
        _database.client = None
        _database.db = None
        raise RuntimeError(
            "MongoDB rechazó la autenticación. Revisa en MongoDB Atlas el "
            "usuario de Database Access, su contraseña y la IP autorizada; "
            "después actualiza MONGO_URI en .env."
        ) from exc


async def close_mongo_connection() -> None:
    """Cierra la conexión con MongoDB. Se llama al apagar la app (lifespan)."""
    if _database.client is not None:
        _database.client.close()


def get_database():
    """Devuelve la instancia de la base de datos para usar en los routers."""
    if _database.db is None:
        raise RuntimeError("La base de datos aún no ha sido inicializada.")
    return _database.db
