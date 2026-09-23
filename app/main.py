"""
Pizzas & Animatronicos - API de Reservaciones
Proyecto Modular I - API Concurrente con Base de Datos

Punto de entrada de la aplicación. Administra el ciclo de vida global
(conexión/desconexión de MongoDB Atlas) con @asynccontextmanager y sirve
el frontend estático (HTML/CSS/JS) desde la carpeta /static.
"""
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

load_dotenv()  # Carga variables desde .env antes de leer nada de os.getenv

from app.database import close_mongo_connection, connect_to_mongo
from app.routers import reservations


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    await connect_to_mongo()
    print("Conectado a MongoDB Atlas.")
    yield
    # --- Shutdown ---
    await close_mongo_connection()
    print("Conexión a MongoDB cerrada.")


app = FastAPI(
    title="Pizzas & Animatronicos - API de Reservaciones",
    description="API REST concurrente para gestionar reservaciones en un "
                 "restaurante temático de animatronicos.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(reservations.router, prefix="/api")

# Sirve el frontend (index.html, css, js) de forma estática.
# Debe montarse al final para no tapar las rutas /api/*.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
