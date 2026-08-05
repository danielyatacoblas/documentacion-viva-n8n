"""Documentación viva: genera la ficha de un workflow leyendo su JSON.

El problema real: la documentación se escribe una vez, el workflow cambia diez
veces, y a los tres meses la documentación miente. La solución de este módulo
es **derivar la ficha del artefacto real** (el JSON exportado de n8n), de modo
que regenerarla sea un comando y no una tarea de escritura.

Lo que se extrae automáticamente del JSON:
  · disparador y frecuencia (cron, webhook, manual)
  · servicios que toca (Sheets, Mailchimp, Telegram, HTTP…)
  · credenciales/parámetros pendientes de configurar (REEMPLAZAR_*)
  · rutas de error y nodos sin manejo de fallos
  · mapa de nodos en orden de ejecución

Lo que sigue siendo humano: para qué sirve y qué hacer si falla. El módulo
deja esos campos marcados para completar (o los redacta con Claude si hay
API key).
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

# ── catálogo de nodos → lenguaje humano ─────────────────────────────────────

SERVICIOS = {
    "n8n-nodes-base.googleSheets": "Google Sheets",
    "n8n-nodes-base.mailchimp": "Mailchimp",
    "n8n-nodes-base.telegram": "Telegram",
    "n8n-nodes-base.linkedIn": "LinkedIn",
    "n8n-nodes-base.gmail": "Gmail",
    "n8n-nodes-base.slack": "Slack",
    "n8n-nodes-base.httpRequest": "HTTP (API externa)",
    "n8n-nodes-base.postgres": "PostgreSQL",
}

DISPARADORES = {
    "n8n-nodes-base.webhook": "Webhook (lo dispara un sistema externo)",
    "n8n-nodes-base.scheduleTrigger": "Programado",
    "n8n-nodes-base.cron": "Programado",
    "n8n-nodes-base.manualTrigger": "Manual (se ejecuta a mano)",
    "n8n-nodes-base.emailReadImap": "Correo entrante (IMAP)",
    "n8n-nodes-base.formTrigger": "Formulario de n8n",
}

LOGICA = {
    "n8n-nodes-base.code": "Código",
    "n8n-nodes-base.if": "Condición",
    "n8n-nodes-base.switch": "Bifurcación",
    "n8n-nodes-base.set": "Asignación de campos",
    "n8n-nodes-base.noOp": "Sin operación",
    "n8n-nodes-base.respondToWebhook": "Respuesta al webhook",
    "n8n-nodes-base.merge": "Unión de ramas",
}

# Ojo con el orden: en cron el día de la semana empieza en DOMINGO (0),
# no en lunes. Confundirlos hace que "0 8 * * 1" se lea como martes.
DIAS_CRON = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes",
             "sábado"]


# ── lectura del workflow ────────────────────────────────────────────────────

def cargar(ruta: str | Path) -> dict:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def _tipo_corto(t: str) -> str:
    return t.rsplit(".", 1)[-1]


def describir_cron(params: dict) -> str:
    """Traduce la regla de un Schedule Trigger a lenguaje humano."""
    regla = (params.get("rule") or {}).get("interval") or []
    if not regla:
        return "programado (sin regla definida)"
    partes = []
    for r in regla:
        campo = r.get("field")
        if campo == "hours":
            n = r.get("hoursInterval", 1)
            partes.append(f"cada {n} hora{'s' if n != 1 else ''}")
        elif campo == "minutes":
            n = r.get("minutesInterval", 1)
            partes.append(f"cada {n} minuto{'s' if n != 1 else ''}")
        elif campo == "days":
            n = r.get("daysInterval", 1)
            partes.append(f"cada {n} día{'s' if n != 1 else ''}")
        elif campo == "cronExpression":
            partes.append(_traducir_cron(r.get("expression", "")))
        else:
            partes.append(str(campo or "programado"))
    return ", ".join(partes)


def _traducir_cron(expr: str) -> str:
    """'0 8 * * *' → 'todos los días a las 08:00'."""
    campos = expr.split()
    if len(campos) != 5:
        return f"cron `{expr}`"
    minuto, hora, _, _, dia_sem = campos
    hhmm = (f"{int(hora):02d}:{int(minuto):02d}"
            if hora.isdigit() and minuto.isdigit() else expr)
    if dia_sem == "*":
        return f"todos los días a las {hhmm}"
    if dia_sem.isdigit():
        return f"cada {DIAS_CRON[int(dia_sem) % 7]} a las {hhmm}"
    return f"cron `{expr}` (aprox. {hhmm})"


def analizar(wf: dict) -> dict:
    """Extrae del JSON todo lo que se puede saber sin intervención humana."""
    nodos = wf.get("nodes", [])
    conexiones = wf.get("connections", {})

    disparadores, servicios, pendientes, sin_error, pasos = [], set(), set(), [], []

    for n in nodos:
        tipo, nombre = n.get("type", ""), n.get("name", "")
        params = n.get("parameters", {}) or {}

        if tipo in DISPARADORES:
            detalle = DISPARADORES[tipo]
            if "schedule" in tipo.lower() or "cron" in tipo.lower():
                detalle += f" — {describir_cron(params)}"
            elif "webhook" in tipo.lower():
                metodo = params.get("httpMethod", "POST")
                ruta = params.get("path", "")
                detalle += f" — `{metodo} /{ruta}`"
            disparadores.append({"nodo": nombre, "detalle": detalle})

        if tipo in SERVICIOS:
            servicios.add(SERVICIOS[tipo])

        # parámetros pendientes de configurar
        for m in re.findall(r"REEMPLAZAR_[A-Z_]+", json.dumps(params, ensure_ascii=False)):
            pendientes.add(m)

        # nodos que llaman a servicios externos sin ruta de error declarada
        if tipo in SERVICIOS and not n.get("onError"):
            sin_error.append(nombre)

        pasos.append({
            "nombre": nombre,
            "tipo": SERVICIOS.get(tipo) or DISPARADORES.get(tipo)
                    or LOGICA.get(tipo) or _tipo_corto(tipo),
            "notas": n.get("notes", ""),
        })

    # orden de ejecución siguiendo las conexiones desde cada disparador
    orden = _ordenar(nodos, conexiones, [d["nodo"] for d in disparadores])

    return {
        "nombre": wf.get("name", "(sin nombre)"),
        "total_nodos": len(nodos),
        "disparadores": disparadores,
        "servicios": sorted(servicios),
        "pendientes": sorted(pendientes),
        "sin_manejo_error": sin_error,
        "pasos": pasos,
        "orden": orden,
        "etiquetas": [t.get("name") for t in wf.get("tags", []) if t.get("name")],
    }


def _ordenar(nodos, conexiones, raices) -> list[str]:
    """Orden de ejecución real, recorriendo una cadena completa por disparador.

    Un workflow puede tener varios disparadores independientes (ej. un webhook
    y un cron). Se recorre cada cadena entera antes de pasar a la siguiente
    para que la ficha se lea como el proceso ocurre, no intercalado.
    """
    nombres = [n.get("name") for n in nodos]
    vistos, orden = set(), []

    for raiz in raices:
        cola = [raiz]
        while cola:                       # BFS dentro de esta cadena
            actual = cola.pop(0)
            if actual in vistos:
                continue
            vistos.add(actual)
            orden.append(actual)
            for salida in (conexiones.get(actual, {}).get("main") or []):
                for enlace in salida or []:
                    destino = enlace.get("node")
                    if destino and destino not in vistos:
                        cola.append(destino)

    # nodos huérfanos al final (no alcanzables desde ningún disparador)
    orden += [n for n in nombres if n not in vistos]
    return orden


# ── generación de la ficha ──────────────────────────────────────────────────

PENDIENTE = "_(pendiente de completar por una persona)_"


def generar_ficha(info: dict, *, que_hace: str = "", si_falla: list[str] | None = None,
                  responsable: str = "Equipo de automatización",
                  ubicacion: str = "n8n · instancia del Club STEM",
                  fecha_revision: str | None = None) -> str:
    """Arma la ficha en Markdown a partir del análisis + los campos humanos."""
    f = fecha_revision or date.today().isoformat()
    si_falla = si_falla or []

    disp = ("\n".join(f"- **{d['nodo']}** — {d['detalle']}" for d in info["disparadores"])
            or "- _Sin disparador automático: se ejecuta manualmente._")
    serv = ("\n".join(f"- {s}" for s in info["servicios"])
            or "- _No usa servicios externos._")

    if info["pendientes"]:
        pend = "\n".join(f"- `{p}`" for p in info["pendientes"])
        pend_bloque = (f"\n> **Antes de activarlo hay que configurar:**\n\n{pend}\n")
    else:
        pend_bloque = "\n>  No hay parámetros pendientes de configurar.\n"

    pasos = "\n".join(
        f"{i}. **{nombre}** · {next((p['tipo'] for p in info['pasos'] if p['nombre'] == nombre), '')}"
        + (f"  \n   _{next((p['notas'] for p in info['pasos'] if p['nombre'] == nombre), '')}_"
           if next((p["notas"] for p in info["pasos"] if p["nombre"] == nombre), "") else "")
        for i, nombre in enumerate(info["orden"], 1))

    if info["sin_manejo_error"]:
        riesgo = ("Estos nodos llaman a servicios externos y **no declaran ruta de "
                  "error**; si la API falla, la ejecución se detiene:\n\n"
                  + "\n".join(f"- {n}" for n in info["sin_manejo_error"]))
    else:
        riesgo = "Todos los nodos que llaman a servicios externos tienen ruta de error."

    falla = ("\n".join(f"{i}. {p}" for i, p in enumerate(si_falla, 1))
             if si_falla else PENDIENTE)

    return f"""# Ficha · {info['nombre']}

> Generada automáticamente desde el JSON del workflow.
> Regenerar con: `python scripts/generar_fichas.py`
> Responsable: **{responsable}**
> Última generación: **{f}**

## 1. Qué hace

{que_hace or PENDIENTE}

## 2. Dónde corre

{ubicacion}
{f"Etiquetas: {', '.join(info['etiquetas'])}" if info['etiquetas'] else ""}

## 3. Cuándo se dispara

{disp}

## 4. Servicios que toca

{serv}
{pend_bloque}
## 5. Pasos (orden de ejecución)

{pasos}

## 6. Riesgos detectados automáticamente

{riesgo}

## 7. Qué hacer si falla

{falla}

---

*Ficha derivada de {info['total_nodos']} nodos. Los campos 1 y 7 los escribe una
persona: el resto se regenera solo cuando el workflow cambia.*
"""


def ficha_desde_archivo(ruta: str | Path, **campos_humanos) -> str:
    return generar_ficha(analizar(cargar(ruta)), **campos_humanos)
