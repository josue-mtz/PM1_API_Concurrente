"""
Lógica de generación de reportes de ocupación.

La función `generar_reporte_pesado` es SÍNCRONA y bloqueante a propósito:
simula un procesamiento intensivo de CPU (por ejemplo, un análisis pesado
de ocupación / generación de reporte). Se ejecuta desde el router mediante
`asyncio.to_thread()` para que NO bloquee el event loop de FastAPI mientras
corre, cumpliendo con el requisito de concurrencia no bloqueante.
"""
import hashlib
import time
from collections import Counter
from typing import List, Dict, Any


def _simular_procesamiento_pesado(duracion_segundos: float) -> int:
    """
    Trabajo intensivo de CPU simulado (bloqueante).

    Se usa un límite de tiempo (en vez de un número fijo de iteraciones)
    para que la duración sea consistente sin importar la velocidad de la
    máquina donde se corra la prueba de concurrencia.
    """
    fin = time.time() + duracion_segundos
    contador = 0
    while time.time() < fin:
        contador += 1
        # Trabajo real de CPU (no I/O), para que sí bloquearía el event loop
        # si se ejecutara directamente en una corrutina sin to_thread().
        hashlib.sha256(str(contador).encode()).hexdigest()
    return contador


def generar_reporte_pesado(
    reservaciones: List[Dict[str, Any]],
    duracion_segundos: float = 4.0,
) -> Dict[str, Any]:
    """
    Genera el reporte de ocupación del día a partir de una lista de
    reservaciones (ya obtenidas de Mongo de forma async) y simula un
    procesamiento pesado de CPU antes de devolver el resultado.
    """
    inicio = time.time()

    # 1. "Procesamiento pesado" simulado (analítica, generación de PDF, etc.)
    iteraciones = _simular_procesamiento_pesado(duracion_segundos)

    # 2. Cálculo real de estadísticas a partir de las reservaciones
    total = len(reservaciones)
    capacidad_total_mesas = 50  # mismo límite usado en la validación de "mesa"

    por_zona = Counter(r["zona"] for r in reservaciones)
    por_estado = Counter(r["estado"] for r in reservaciones)
    por_hora = Counter(r["fecha_hora"].strftime("%H:00") for r in reservaciones)

    zona_top = por_zona.most_common(1)[0][0] if por_zona else None
    hora_pico = por_hora.most_common(1)[0][0] if por_hora else None
    mesas_ocupadas = len({r["mesa"] for r in reservaciones})
    ocupacion_pct = round((mesas_ocupadas / capacidad_total_mesas) * 100, 2)

    tiempo_total = round(time.time() - inicio, 2)

    return {
        "total_reservaciones": total,
        "mesas_ocupadas": mesas_ocupadas,
        "ocupacion_porcentaje": ocupacion_pct,
        "hora_pico": hora_pico,
        "zona_mas_solicitada": zona_top,
        "reservaciones_por_zona": dict(por_zona),
        "reservaciones_por_estado": dict(por_estado),
        "reservaciones_por_hora": dict(por_hora),
        "tiempo_procesamiento_segundos": tiempo_total,
        "iteraciones_procesadas": iteraciones,
    }
