// ==========================================================
// Pizzas & Animatronicos - Frontend (JS Vanilla)
// Consume la API REST de FastAPI mediante fetch()
// ==========================================================

const API_BASE = "/api";

// ---------- Referencias del DOM ----------
const form = document.getElementById("form-reserva");
const idInput = document.getElementById("reserva-id");
const nombreInput = document.getElementById("nombre_cliente");
const mesaInput = document.getElementById("mesa");
const fechaHoraInput = document.getElementById("fecha_hora");
const personasInput = document.getElementById("numero_personas");
const zonaInput = document.getElementById("zona");
const estadoInput = document.getElementById("estado");
const notasInput = document.getElementById("notas");
const formMensaje = document.getElementById("form-mensaje");
const btnCancelarEdicion = document.getElementById("btn-cancelar-edicion");

const tablaBody = document.getElementById("tabla-body");
const filtroZona = document.getElementById("filtro-zona");
const filtroEstado = document.getElementById("filtro-estado");
const filtroFecha = document.getElementById("filtro-fecha");

const reporteFecha = document.getElementById("reporte-fecha");
const reporteDuracion = document.getElementById("reporte-duracion");
const btnGenerarReporte = document.getElementById("btn-generar-reporte");
const reporteEstado = document.getElementById("reporte-estado");
const reporteResultado = document.getElementById("reporte-resultado");

const btnPingAuto = document.getElementById("btn-ping-auto");
const pingContadorEl = document.getElementById("ping-contador");
const pingLog = document.getElementById("ping-log");

let pingIntervalId = null;
let pingContador = 0;

// ---------- Utilidades ----------
function mostrarMensaje(el, texto, tipo) {
  el.textContent = texto;
  el.className = `mensaje ${tipo || ""}`;
}

function formatearFechaLocal(isoString) {
  const d = new Date(isoString);
  return d.toLocaleString("es-MX", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function badgeEstado(estado) {
  return `<span class="badge ${estado}">${estado}</span>`;
}

// ---------- CARGAR / LISTAR (GET) ----------
async function cargarReservaciones() {
  tablaBody.innerHTML = `<tr><td colspan="8" class="vacio">Cargando reservaciones...</td></tr>`;

  const params = new URLSearchParams();
  if (filtroZona.value) params.append("zona", filtroZona.value);
  if (filtroEstado.value) params.append("estado", filtroEstado.value);
  if (filtroFecha.value) params.append("fecha", filtroFecha.value);

  try {
    const resp = await fetch(`${API_BASE}/reservaciones?${params.toString()}`);
    if (!resp.ok) throw new Error("No se pudieron cargar las reservaciones.");
    const data = await resp.json();
    renderizarTabla(data);
  } catch (err) {
    tablaBody.innerHTML = `<tr><td colspan="8" class="vacio"> ${err.message}</td></tr>`;
  }
}

function renderizarTabla(reservas) {
  if (!reservas.length) {
    tablaBody.innerHTML = `<tr><td colspan="8" class="vacio">No hay reservaciones que coincidan. ¡Anímate a crear una! </td></tr>`;
    return;
  }

  tablaBody.innerHTML = reservas
    .map(
      (r) => `
      <tr>
        <td>${r.nombre_cliente}</td>
        <td>${r.mesa}</td>
        <td>${formatearFechaLocal(r.fecha_hora)}</td>
        <td>${r.numero_personas}</td>
        <td>${r.zona}</td>
        <td>${badgeEstado(r.estado)}</td>
        <td>${r.notas ? r.notas : "—"}</td>
        <td class="fila-acciones">
          <button class="btn-editar" onclick="editarReserva('${r._id}')"></button>
          <button class="btn-eliminar" onclick="eliminarReserva('${r._id}')"></button>
        </td>
      </tr>`
    )
    .join("");
}

// ---------- CREAR / ACTUALIZAR (POST / PUT) ----------
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    nombre_cliente: nombreInput.value.trim(),
    mesa: Number(mesaInput.value),
    fecha_hora: new Date(fechaHoraInput.value).toISOString(),
    numero_personas: Number(personasInput.value),
    zona: zonaInput.value,
    estado: estadoInput.value,
    notas: notasInput.value.trim() || null,
  };

  const idEditando = idInput.value;
  const esEdicion = Boolean(idEditando);
  const url = esEdicion
    ? `${API_BASE}/reservaciones/${idEditando}`
    : `${API_BASE}/reservaciones`;
  const metodo = esEdicion ? "PUT" : "POST";

  try {
    const resp = await fetch(url, {
      method: metodo,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail ? JSON.stringify(err.detail) : `Error HTTP ${resp.status}`);
    }

    mostrarMensaje(
      formMensaje,
      esEdicion ? " Reservación actualizada." : " ¡Mesa reservada con éxito!",
      "ok"
    );
    resetearFormulario();
    cargarReservaciones();
  } catch (err) {
    mostrarMensaje(formMensaje, ` ${err.message}`, "error");
  }
});

btnCancelarEdicion.addEventListener("click", resetearFormulario);

function resetearFormulario() {
  form.reset();
  idInput.value = "";
  document.getElementById("btn-guardar").textContent = " Reservar Mesa";
  btnCancelarEdicion.hidden = true;
}

// ---------- EDITAR (precargar formulario) ----------
async function editarReserva(id) {
  try {
    const resp = await fetch(`${API_BASE}/reservaciones/${id}`);
    if (!resp.ok) throw new Error("No se encontró la reservación.");
    const r = await resp.json();

    idInput.value = r._id;
    nombreInput.value = r.nombre_cliente;
    mesaInput.value = r.mesa;
    fechaHoraInput.value = new Date(r.fecha_hora).toISOString().slice(0, 16);
    personasInput.value = r.numero_personas;
    zonaInput.value = r.zona;
    estadoInput.value = r.estado;
    notasInput.value = r.notas || "";

    document.getElementById("btn-guardar").textContent = " Guardar Cambios";
    btnCancelarEdicion.hidden = false;
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (err) {
    mostrarMensaje(formMensaje, ` ${err.message}`, "error");
  }
}

// ---------- ELIMINAR (DELETE) ----------
async function eliminarReserva(id) {
  if (!confirm("¿Seguro que quieres cancelar y eliminar esta reservación?")) return;

  try {
    const resp = await fetch(`${API_BASE}/reservaciones/${id}`, { method: "DELETE" });
    if (!resp.ok) throw new Error("No se pudo eliminar la reservación.");
    cargarReservaciones();
  } catch (err) {
    alert(` ${err.message}`);
  }
}

// ---------- FILTROS ----------
document.getElementById("btn-filtrar").addEventListener("click", cargarReservaciones);
document.getElementById("btn-limpiar-filtros").addEventListener("click", () => {
  filtroZona.value = "";
  filtroEstado.value = "";
  filtroFecha.value = "";
  cargarReservaciones();
});

// ---------- REPORTE PESADO (asyncio.to_thread en el backend) ----------
btnGenerarReporte.addEventListener("click", async () => {
  const params = new URLSearchParams();
  if (reporteFecha.value) params.append("fecha", reporteFecha.value);
  params.append("duracion", reporteDuracion.value || "5");

  btnGenerarReporte.disabled = true;
  mostrarMensaje(reporteEstado, "Procesando reporte pesado en el servidor...", "");
  reporteResultado.hidden = true;

  const inicio = performance.now();

  try {
    const resp = await fetch(`${API_BASE}/reservaciones/reporte/dia?${params.toString()}`);
    if (!resp.ok) throw new Error("No se pudo generar el reporte.");
    const data = await resp.json();

    const segundos = ((performance.now() - inicio) / 1000).toFixed(2);
    mostrarMensaje(reporteEstado, ` Reporte generado en ${segundos}s (medido desde el navegador).`, "ok");

    document.getElementById("stat-total").textContent = data.total_reservaciones;
    document.getElementById("stat-mesas").textContent = data.mesas_ocupadas;
    document.getElementById("stat-ocupacion").textContent = `${data.ocupacion_porcentaje}%`;
    document.getElementById("stat-hora-pico").textContent = data.hora_pico || "N/A";
    document.getElementById("stat-zona-top").textContent = data.zona_mas_solicitada || "N/A";
    document.getElementById("stat-tiempo").textContent = `${data.tiempo_procesamiento_segundos}s`;
    reporteResultado.hidden = false;
  } catch (err) {
    mostrarMensaje(reporteEstado, ` ${err.message}`, "error");
  } finally {
    btnGenerarReporte.disabled = false;
  }
});

// ---------- PRUEBA DE CONCURRENCIA: auto-ping ----------
btnPingAuto.addEventListener("click", () => {
  if (pingIntervalId) {
    clearInterval(pingIntervalId);
    pingIntervalId = null;
    btnPingAuto.textContent = "▶ Iniciar auto-ping (cada 1s)";
    return;
  }

  btnPingAuto.textContent = "⏸ Detener auto-ping";
  pingIntervalId = setInterval(hacerPing, 1000);
  hacerPing();
});

async function hacerPing() {
  const hora = new Date().toLocaleTimeString("es-MX");
  try {
    const inicio = performance.now();
    const resp = await fetch(`${API_BASE}/ping`);
    const ms = (performance.now() - inicio).toFixed(0);
    if (!resp.ok) throw new Error("sin respuesta");

    pingContador++;
    pingContadorEl.textContent = pingContador;

    const li = document.createElement("li");
    li.textContent = ` ${hora} — respondió en ${ms}ms`;
    pingLog.prepend(li);
    while (pingLog.children.length > 15) pingLog.removeChild(pingLog.lastChild);
  } catch (err) {
    const li = document.createElement("li");
    li.textContent = ` ${hora} — sin respuesta`;
    pingLog.prepend(li);
  }
}

// ---------- Inicialización ----------
document.addEventListener("DOMContentLoaded", () => {
  const hoy = new Date().toISOString().slice(0, 10);
  filtroFecha.value = "";
  reporteFecha.value = hoy;
  cargarReservaciones();
});
