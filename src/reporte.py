"""Reporte semanal automático en lenguaje natural.

Toma los KPIs ya calculados (el `datos.json` del proyecto 03) y redacta el
resumen ejecutivo que el equipo recibe cada lunes: qué subió, qué bajó, qué
revisar esta semana.

Regla de redacción: **el reporte debe señalar problemas**. Un resumen que solo
felicita no se lee la segunda semana. Por eso ordena por magnitud del cambio y
siempre incluye una sección de "qué revisar".
"""
from __future__ import annotations

import os
from datetime import date

# Umbrales para decidir si un cambio merece mención
CAMBIO_RELEVANTE = 5.0      # % de variación
CAMBIO_FUERTE = 15.0        # % que pasa a "revisar"


def _formato(valor: float, unidad: str) -> str:
    if unidad == "%":
        return f"{valor:.1f} %"
    if "día" in unidad:
        return f"{valor:.2f} días"
    if valor >= 1000:
        return f"{valor:,.0f}".replace(",", " ")
    return f"{valor:.0f}"


def _es_bueno(kpi: dict) -> bool:
    return (kpi["variacion"] < 0) if kpi.get("mejor") == "abajo" else (kpi["variacion"] > 0)


def clasificar_kpis(kpis: list[dict]) -> dict[str, list[dict]]:
    """Separa en mejoras, caídas y estables según la variación."""
    mejoras, caidas, estables = [], [], []
    for k in kpis:
        v = abs(k.get("variacion", 0))
        if v < CAMBIO_RELEVANTE:
            estables.append(k)
        elif _es_bueno(k):
            mejoras.append(k)
        else:
            caidas.append(k)
    orden = lambda xs: sorted(xs, key=lambda k: -abs(k.get("variacion", 0)))  # noqa: E731
    return {"mejoras": orden(mejoras), "caidas": orden(caidas),
            "estables": orden(estables)}


def puntos_de_atencion(kpis: list[dict]) -> list[str]:
    """Qué revisar: caídas fuertes, con recomendación concreta por métrica."""
    recomendaciones = {
        "apertura": "revisar los asuntos, el horario de envío y limpiar la lista "
                    "de suscriptores inactivos",
        "clics": "revisar el contenido y la ubicación del llamado a la acción "
                 "dentro del correo",
        "conversion": "revisar el tiempo de respuesta a los leads y el mensaje "
                      "de primer contacto",
        "respuesta": "revisar la carga del equipo y quién está atendiendo la bandeja",
        "alcance": "revisar la frecuencia de publicación y los horarios",
        "interaccion": "revisar qué formatos funcionaron mejor el mes pasado",
        "asistencia": "contactar a los inscritos que faltaron y revisar horario y sede",
        "sesiones": "revisar si hubo caída de tráfico por campañas pausadas",
        "beneficiarios": "confirmar que la asistencia se está registrando completa",
        "leads": "revisar si se pausó alguna campaña o formulario",
    }
    salida = []
    for k in kpis:
        if abs(k.get("variacion", 0)) >= CAMBIO_FUERTE and not _es_bueno(k):
            que = recomendaciones.get(k["id"], "revisar la fuente de datos")
            # "cayó" solo si el número bajó; si la métrica es de las que
            # conviene reducir (días de respuesta), subir es la mala noticia.
            verbo = "subió" if k["variacion"] > 0 else "cayó"
            salida.append(
                f"**{k['etiqueta']}** {verbo} {abs(k['variacion']):.1f} % "
                f"(ahora {_formato(k['valor'], k['unidad'])}): {que}.")
    return salida


def redactar(datos: dict, hoy: date | None = None) -> str:
    """Genera el reporte en Markdown a partir del datos.json del dashboard."""
    hoy = hoy or date.today()
    kpis = datos.get("kpis", [])
    periodo = datos.get("periodo", {})
    grupos = clasificar_kpis(kpis)
    atencion = puntos_de_atencion(kpis)

    hero = next((k for k in kpis if k["id"] == "leads"), None)
    cabecera = (f"En los últimos {periodo.get('dias_kpi', 30)} días se generaron "
                f"**{_formato(hero['valor'], '')} leads** "
                f"({hero['variacion']:+.1f} % frente al período anterior)."
                if hero else "Resumen del período.")

    def bloque(titulo, items, signo=""):
        """El signo va delante del título solo si existe.

        Concatenarlo siempre dejaba un espacio de más cuando venía vacío, y el
        encabezado salía como '###  Lo que mejoró'. Se nota en el Markdown
        renderizado y en la salida de la terminal."""
        if not items:
            return ""
        filas = "\n".join(
            f"- **{k['etiqueta']}**: {_formato(k['valor'], k['unidad'])} "
            f"({k['variacion']:+.1f} %)" for k in items)
        encabezado = f"{signo} {titulo}".strip()
        return f"\n### {encabezado}\n\n{filas}\n"

    # Los encabezados hablan de "mejoró/empeoró", no de "subió/bajó": en
    # métricas como los días de respuesta, subir ES empeorar.

    cuerpo = [
        f"# Reporte semanal · Club STEM\n",
        f"**Semana del {hoy.isoformat()}** · "
        f"período analizado: {periodo.get('desde', '?')} al {periodo.get('hasta', '?')}\n",
        f"\n{cabecera}\n",
        bloque("Lo que mejoró", grupos["mejoras"], ""),
        bloque("Lo que empeoró", grupos["caidas"], ""),
    ]

    if atencion:
        cuerpo.append("\n### Qué revisar esta semana\n\n"
                      + "\n".join(f"{i}. {p}" for i, p in enumerate(atencion, 1)) + "\n")
    else:
        cuerpo.append("\n### Qué revisar esta semana\n\n"
                      "Sin caídas relevantes. Buen momento para probar algo nuevo "
                      "(un formato, un horario de envío) y medir el efecto.\n")

    if grupos["estables"]:
        nombres = ", ".join(k["etiqueta"].lower() for k in grupos["estables"])
        cuerpo.append(f"\n### Sin cambios relevantes\n\n{nombres}.\n")

    desg = datos.get("desgloses", {})
    if desg.get("conversion_por_canal"):
        mejor = max(desg["conversion_por_canal"].items(), key=lambda kv: kv[1])
        peor = min(desg["conversion_por_canal"].items(), key=lambda kv: kv[1])
        cuerpo.append(
            f"\n### Dato de la semana\n\n"
            f"El canal que mejor convierte es **{mejor[0]}** ({mejor[1]:.1f} %) y "
            f"el que menos, **{peor[0]}** ({peor[1]:.1f} %). "
            f"La diferencia es de {mejor[1] - peor[1]:.1f} puntos: vale la pena "
            f"revisar qué se está haciendo distinto en cada uno.\n")

    cuerpo.append(
        f"\n---\n\n*Reporte generado automáticamente el {hoy.isoformat()} "
        f"a partir del dashboard de KPIs. Los números salen del warehouse; "
        f"las recomendaciones son sugerencias para revisar con el equipo.*\n")

    return "".join(cuerpo)


# ── versión redactada con Claude (opcional) ─────────────────────────────────

def redactar_con_claude(datos: dict, hoy: date | None = None,
                        modelo: str = "claude-sonnet-5") -> str:
    """Misma información, redactada por Claude con tono más natural.

    Se le entrega el reporte determinista como base para que **no invente
    números**: solo reescribe. Si falla, devuelve la versión determinista.
    """
    base = redactar(datos, hoy)
    try:
        from anthropic import Anthropic
        cliente = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        resp = cliente.messages.create(
            model=modelo, max_tokens=1500,
            messages=[{"role": "user", "content":
                       "Reescribe este reporte semanal para el equipo de una ONG "
                       "educativa peruana. Mantén EXACTAMENTE los mismos números y "
                       "conclusiones: solo mejora la redacción y el orden. No "
                       "agregues datos que no estén. Devuelve Markdown.\n\n" + base}])
        return "".join(b.text for b in resp.content
                       if getattr(b, "type", "") == "text").strip()
    except Exception:               # noqa: BLE001
        return base
