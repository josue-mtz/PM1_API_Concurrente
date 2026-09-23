"""
Endpoints de reservaciones.

CRUD:
  POST   /api/reservaciones                -> crear
  GET    /api/reservaciones                -> listar (con filtros)
  GET    /api/reservaciones/{id}           -> obtener una
  PUT    /api/reservaciones/{id}           -> actualizar
  DELETE /api/reservaciones/{id}           -> eliminar

Concurrencia:
  GET    /api/reservaciones/reporte/dia    -> reporte de ocupación (usa asyncio.to_thread)
  GET    /api/ping                         -> endpoint liviano para probar que el
                                               servidor sigue respondiendo mientras
                                               corre el reporte pesado
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query, status

from app.database import get_database
from app.models import (
    EstadoEnum,
    ReservationCreate,
    ReservationOut,
    ReservationUpdate,
    ZonaEnum,
    reservation_helper,
)
from app.services.reports import generar_reporte_pesado

router = APIRouter(tags=["reservaciones"])


def _validar_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El id '{id_str}' no es un ObjectId válido de MongoDB.",
        )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
@router.post(
    "/reservaciones",
    response_model=ReservationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva reservación",
)
async def crear_reservacion(payload: ReservationCreate):
    db = get_database()
    doc = payload.model_dump()
    result = await db.reservaciones.insert_one(doc)
    nuevo = await db.reservaciones.find_one({"_id": result.inserted_id})
    return reservation_helper(nuevo)


# ---------------------------------------------------------------------------
# READ (list + filtros)
# ---------------------------------------------------------------------------
@router.get(
    "/reservaciones",
    response_model=List[ReservationOut],
    summary="Listar reservaciones (con filtros opcionales)",
)
async def listar_reservaciones(
    zona: Optional[ZonaEnum] = Query(None, description="Filtrar por zona"),
    estado: Optional[EstadoEnum] = Query(None, description="Filtrar por estado"),
    fecha: Optional[str] = Query(
        None, description="Filtrar por fecha exacta, formato YYYY-MM-DD"
    ),
):
    db = get_database()
    query: dict = {}

    if zona:
        query["zona"] = zona.value
    if estado:
        query["estado"] = estado.value
    if fecha:
        try:
            dia = datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha inválido. Usa YYYY-MM-DD.",
            )
        query["fecha_hora"] = {"$gte": dia, "$lt": dia + timedelta(days=1)}

    cursor = db.reservaciones.find(query).sort("fecha_hora", 1)
    reservaciones = [reservation_helper(doc) async for doc in cursor]
    return reservaciones


# ---------------------------------------------------------------------------
# READ (uno)
# ---------------------------------------------------------------------------
@router.get(
    "/reservaciones/{reservacion_id}",
    response_model=ReservationOut,
    summary="Obtener una reservación por id",
)
async def obtener_reservacion(reservacion_id: str):
    db = get_database()
    oid = _validar_object_id(reservacion_id)
    doc = await db.reservaciones.find_one({"_id": oid})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservación no encontrada.",
        )
    return reservation_helper(doc)


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
@router.put(
    "/reservaciones/{reservacion_id}",
    response_model=ReservationOut,
    summary="Actualizar una reservación",
)
async def actualizar_reservacion(reservacion_id: str, payload: ReservationUpdate):
    db = get_database()
    oid = _validar_object_id(reservacion_id)

    cambios = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not cambios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron campos para actualizar.",
        )

    resultado = await db.reservaciones.update_one({"_id": oid}, {"$set": cambios})
    if resultado.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservación no encontrada.",
        )

    doc = await db.reservaciones.find_one({"_id": oid})
    return reservation_helper(doc)


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
@router.delete(
    "/reservaciones/{reservacion_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar una reservación",
)
async def eliminar_reservacion(reservacion_id: str):
    db = get_database()
    oid = _validar_object_id(reservacion_id)

    resultado = await db.reservaciones.delete_one({"_id": oid})
    if resultado.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservación no encontrada.",
        )
    return {"mensaje": "Reservación eliminada correctamente.", "id": reservacion_id}


# ---------------------------------------------------------------------------
# CONCURRENCIA: reporte pesado delegado a un hilo secundario
# ---------------------------------------------------------------------------
@router.get(
    "/reservaciones/reporte/dia",
    summary="Generar reporte de ocupación del día (tarea intensiva de CPU, no bloqueante)",
)
async def reporte_del_dia(
    fecha: Optional[str] = Query(
        None, description="Fecha a reportar, formato YYYY-MM-DD. Por defecto: hoy."
    ),
    duracion: float = Query(
        4.0, ge=0.5, le=15.0,
        description="Segundos de procesamiento pesado simulado (para la prueba de concurrencia).",
    ),
):
    db = get_database()

    if fecha:
        try:
            dia = datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha inválido. Usa YYYY-MM-DD.",
            )
    else:
        hoy = datetime.utcnow()
        dia = datetime(hoy.year, hoy.month, hoy.day)

    query = {"fecha_hora": {"$gte": dia, "$lt": dia + timedelta(days=1)}}

    # 1. Obtenemos los datos de forma async (no bloqueante, I/O de red)
    cursor = db.reservaciones.find(query)
    reservaciones = [reservation_helper(doc) async for doc in cursor]

    # Motor devuelve fecha_hora como datetime; lo dejamos así para el cálculo
    for r in reservaciones:
        if isinstance(r["fecha_hora"], str):
            r["fecha_hora"] = datetime.fromisoformat(r["fecha_hora"])

    # 2. Delegamos el cómputo PESADO (CPU-bound) a un hilo secundario.
    #    Esto es lo que evita que el event loop se bloquee: mientras este
    #    reporte corre, el servidor sigue atendiendo otras peticiones
    #    (por ejemplo GET /api/ping) sin esperar a que termine.
    inicio_request = time.time()
    reporte = await asyncio.to_thread(generar_reporte_pesado, reservaciones, duracion)
    tiempo_total_request = round(time.time() - inicio_request, 2)

    return {
        "fecha_reportada": dia.strftime("%Y-%m-%d"),
        "tiempo_total_request_segundos": tiempo_total_request,
        **reporte,
    }


# ---------------------------------------------------------------------------
# Endpoint auxiliar para la prueba de concurrencia
# ---------------------------------------------------------------------------
@router.get("/ping", summary="Endpoint liviano para probar que el servidor no se bloquea")
async def ping():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
