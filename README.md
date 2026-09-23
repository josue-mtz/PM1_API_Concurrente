# Pizzas & Animatronicos

Proyecto Modular I — **API Concurrente con Base de Datos**

Aplicación web para gestionar reservaciones de un restaurante temático de
animatrónicos, construida con **FastAPI**, **MongoDB Atlas (Motor)**,
concurrencia no bloqueante con **`asyncio.to_thread()`** y un frontend en
**HTML5 / CSS3 / JS Vanilla**.


## Stack técnico

| Requisito | Implementación |
|---|---|
| API REST | FastAPI + Pydantic (validación estricta, 6 endpoints) |
| Base de datos | MongoDB Atlas, conexión asíncrona con **Motor** |
| Ciclo de vida | `@asynccontextmanager` (`lifespan`) en `app/main.py` |
| Concurrencia | `asyncio.to_thread()` en el endpoint de reporte pesado |
| Frontend | HTML/CSS/JS vanilla servidos con `StaticFiles`, consumo vía `fetch()` |


## Estructura del proyecto

```
PM1_API_Concurrente/
├── app/
│   ├── main.py                 # App FastAPI + lifespan + montaje de estáticos
│   ├── database.py             # Conexión asíncrona a MongoDB (Motor)
│   ├── models.py                # Modelos y schemas Pydantic
│   ├── routers/
│   │   └── reservations.py     # Endpoints CRUD + endpoint de concurrencia
│   └── services/
│       └── reports.py          # Lógica de reporte (tarea CPU-bound)
├── static/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```


## Instalación

### 1. Clonar el repositorio y crear entorno virtual

```bash
git clone <https://github.com/josue-mtz/PM1_API_Concurrente.git>
cd PM1_API_Concurrente
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Copia el archivo de ejemplo y coloca tu cadena de conexión de **MongoDB Atlas**:

```bash
cp .env.example .env
```

Edita `.env`:

```
MONGO_URI=mongodb+srv://usuario:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DB_NAME=pizzas_animatronicos
```

### 4. Ejecutar la aplicación

```bash
uvicorn app.main:app --reload
```

- **Frontend:** http://127.0.0.1:8000
- **Documentación interactiva (Swagger):** http://127.0.0.1:8000/docs

La app quedará disponible en:


No se necesita crear colecciones manualmente: MongoDB las crea
automáticamente al insertar el primer documento.


## Endpoints

Todos los endpoints de datos viven bajo el prefijo `/api`.

| Método | Ruta | Descripción | Éxito | Errores |
|---|---|---|---|---|
| `POST` | `/api/reservaciones` | Crea una nueva reservación | `201 Created` | `422` (validación) |
| `GET` | `/api/reservaciones` | Lista reservaciones. Filtros opcionales: `zona`, `estado`, `fecha` (YYYY-MM-DD) | `200 OK` | `400` (fecha inválida) |
| `GET` | `/api/reservaciones/{id}` | Obtiene una reservación por id | `200 OK` | `400` (id inválido), `404` (no existe) |
| `PUT` | `/api/reservaciones/{id}` | Actualiza campos de una reservación | `200 OK` | `400`, `404` |
| `DELETE` | `/api/reservaciones/{id}` | Elimina una reservación | `200 OK` | `400`, `404` |
| `GET` | `/api/reservaciones/reporte/dia` | **Reporte de ocupación** del día (CPU-bound, delegado a hilo con `asyncio.to_thread`). Query params: `fecha` (opcional), `duracion` (segundos de simulación, 1-15) | `200 OK` | `400` |
| `GET` | `/api/ping` | Endpoint liviano para comprobar que el servidor sigue vivo mientras corre una tarea pesada | `200 OK` | — |

### Modelo de reservación

```json
{
  "nombre_cliente": "Mike Schmidt",
  "mesa": 7,
  "fecha_hora": "2026-10-15T19:30:00",
  "numero_personas": 4,
  "zona": "VIP",
  "estado": "pendiente",
  "notas": "Cumpleaños del niño"
}
```

Zonas válidas: `VIP`, `Escenario`, `Cueva del Pirata`, `Arcade`, `Pelotero`.
Estados válidos: `pendiente`, `confirmada`, `cancelada`, `completada`.


## Prueba de concurrencia

El endpoint `GET /api/reservaciones/reporte/dia` simula un procesamiento
pesado de CPU (por defecto ~4-5 segundos) usando un cálculo intensivo real
(hashing en bucle), y lo ejecuta con:

```python
reporte = await asyncio.to_thread(generar_reporte_pesado, reservaciones, duracion)
```

Esto libera el event loop de FastAPI mientras el hilo secundario trabaja,
por lo que **el servidor sigue atendiendo otras peticiones sin esperar a
que el reporte termine**.

### Cómo comprobarlo desde el frontend

1. Abre la app en el navegador.
2. Ve a la sección **"Reporte del Día"**.
3. Selecciona **"Iniciar auto-ping"** para consultar `/api/ping` cada segundo.
4. Sin detener el ping, selecciona **"Generar Reporte Pesado"**.
5. Verás que el contador de pings **sigue subiendo con normalidad** mientras
   el reporte se procesa en segundo plano — eso es la prueba de que el
   servidor no se bloqueó.

### Cómo comprobarlo por línea de comandos (alternativa)

En una terminal, dispara el reporte pesado:

```bash
curl "http://127.0.0.1:8000/api/reservaciones/reporte/dia?duracion=8"
```

En otra terminal, mientras el comando anterior sigue corriendo, dispara varias
peticiones normales:

```bash
curl "http://127.0.0.1:8000/api/ping"
curl "http://127.0.0.1:8000/api/reservaciones"
```

Estas últimas deben responder de inmediato, sin esperar los 8 segundos del
reporte.


## Notas de diseño

El frontend usa una paleta neón (rosa, cian, amarillo) sobre morado oscuro,
tipografías estilo arcade (`Press Start 2P`, `Bangers`) y una barra de
"luces de escenario" en la parte superior, buscando la estética de una
pizzería/arcade familiar de los años 80.


## Autoría

Proyecto Modular I — API Concurrente con Base de Datos.