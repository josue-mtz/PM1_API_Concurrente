"""
Modelos y esquemas Pydantic para el sistema de reservaciones
de Pizzas & Animatronicos.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ZonaEnum(str, Enum):
    vip = "VIP"
    escenario = "Escenario"
    cueva_pirata = "Cueva del Pirata"
    arcade = "Arcade"
    pelotero = "Pelotero"


class EstadoEnum(str, Enum):
    pendiente = "pendiente"
    confirmada = "confirmada"
    cancelada = "cancelada"
    completada = "completada"


class ReservationBase(BaseModel):
    """Campos compartidos por creación y actualización."""
    nombre_cliente: str = Field(
        ..., min_length=2, max_length=100,
        description="Nombre completo del cliente que reserva"
    )
    mesa: int = Field(..., ge=1, le=50, description="Número de mesa asignada")
    fecha_hora: datetime = Field(..., description="Fecha y hora de la reservación")
    numero_personas: int = Field(..., ge=1, le=20, description="Cantidad de comensales")
    zona: ZonaEnum
    estado: EstadoEnum = EstadoEnum.pendiente
    notas: Optional[str] = Field(None, max_length=300)


class ReservationCreate(ReservationBase):
    """Payload para crear una reservación (POST)."""
    pass


class ReservationUpdate(BaseModel):
    """Payload para actualizar una reservación (PUT). Todo opcional."""
    nombre_cliente: Optional[str] = Field(None, min_length=2, max_length=100)
    mesa: Optional[int] = Field(None, ge=1, le=50)
    fecha_hora: Optional[datetime] = None
    numero_personas: Optional[int] = Field(None, ge=1, le=20)
    zona: Optional[ZonaEnum] = None
    estado: Optional[EstadoEnum] = None
    notas: Optional[str] = Field(None, max_length=300)


class ReservationOut(ReservationBase):
    """Modelo de salida, incluye el id generado por Mongo."""
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")


def reservation_helper(doc: dict) -> dict:
    """Convierte un documento de Mongo (con ObjectId) a un dict serializable."""
    return {
        "_id": str(doc["_id"]),
        "nombre_cliente": doc["nombre_cliente"],
        "mesa": doc["mesa"],
        "fecha_hora": doc["fecha_hora"],
        "numero_personas": doc["numero_personas"],
        "zona": doc["zona"],
        "estado": doc["estado"],
        "notas": doc.get("notas"),
    }
