#!/usr/bin/env python3
"""Genera la documentación viva de los workflows de TODO el portafolio.

    python scripts/generar_fichas.py

Lee los JSON reales de los proyectos 01 y 02, extrae del artefacto lo que se
puede saber solo (disparador, servicios, pendientes, riesgos, orden de nodos)
y escribe una ficha por workflow en `fichas/`.

Los campos que sí requieren criterio humano ("qué hace", "qué hacer si falla")
se declaran aquí abajo, en un solo lugar y versionados en git.
"""
from __future__ import annotations

import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PORTAFOLIO = ROOT.parent
sys.path.insert(0, str(ROOT))

from src.fichas import ficha_desde_archivo  # noqa: E402

SALIDA = ROOT / "fichas"

# ── Registro de workflows del portafolio + los campos humanos de cada uno ───

WORKFLOWS = [
    {
        "archivo": PORTAFOLIO / "01_flujo_leads_n8n" / "workflows" / "workflow_leads.json",
        "salida": "ficha_leads.md",
        "responsable": "Comunicaciones",
        "que_hace": (
            "Recibe los leads del formulario web y de Podium, los limpia "
            "(normaliza teléfono y correo), descarta duplicados contra el CRM, "
            "los clasifica en talleres / voluntariado / donación / general y "
            "dispara tres acciones: registrar en la hoja CRM, suscribir al "
            "newsletter con la etiqueta del segmento y avisar al equipo por "
            "Telegram. Si nadie contacta al lead en 48 horas, envía un "
            "recordatorio automático.\n\n"
            "**Por qué existe:** antes cada lead se copiaba a mano a la hoja y "
            "a la lista de correo; se perdían leads y se duplicaban registros."),
        "si_falla": [
            "**No llegan avisos de leads nuevos:** revisar en n8n → Executions "
            "si el webhook está recibiendo. Si no hay ejecuciones, el "
            "formulario dejó de apuntar a la URL correcta.",
            "**Error 403 de Google Sheets:** la credencial expiró. Reconectarla "
            "en n8n → Credentials → Google Sheets.",
            "**Los leads llegan pero no se suscriben al newsletter:** revisar "
            "que el ID de lista de Mailchimp siga vigente.",
            "**Llegan duplicados:** verificar que la hoja CRM conserve las "
            "columnas `email` y `telefono` con esos nombres exactos.",
            "**Reproceso manual:** se puede reejecutar una ejecución fallida "
            "desde n8n → Executions → Retry.",
        ],
    },
    {
        "archivo": PORTAFOLIO / "02_publicador_redes_ia" / "workflows" / "workflow_1_generar.json",
        "salida": "ficha_generar_contenido.md",
        "responsable": "Comunicaciones",
        "que_hace": (
            "Cada mañana revisa el calendario de contenido y, para cada pieza "
            "pendiente, genera con Claude un borrador adaptado a cada red "
            "social (largo, tono, emojis y hashtags propios de cada una). Deja "
            "los borradores en la hoja de aprobación y avisa al equipo.\n\n"
            "**Importante:** este workflow NO publica nada. Solo redacta y "
            "encola para revisión humana."),
        "si_falla": [
            "**No se generaron borradores:** revisar que las filas del "
            "calendario tengan la columna `generado` vacía y la fecha correcta.",
            "**Error 401 de la API de Claude:** la API key venció o se agotó el "
            "crédito. Actualizar la credencial Header Auth en n8n.",
            "**Los textos salen cortados:** subir `max_tokens` en el nodo de "
            "Claude o revisar que el prompt no pida más de lo que cabe.",
            "**Mientras se arregla:** se puede generar con el motor de "
            "plantillas del repo (`python scripts/simular_publicacion.py`) y "
            "pegar los textos a mano en la hoja.",
        ],
    },
    {
        "archivo": PORTAFOLIO / "02_publicador_redes_ia" / "workflows" / "workflow_2_publicar.json",
        "salida": "ficha_publicar_redes.md",
        "responsable": "Comunicaciones",
        "que_hace": (
            "Cada hora revisa la cola de aprobación y publica en Instagram, "
            "Facebook y LinkedIn **solo** los posts que una persona aprobó y "
            "cuya fecha programada ya llegó. Marca cada publicación como "
            "publicada; si la API de una red falla, marca el post como fallido, "
            "avisa al equipo y lo deja disponible para reintento.\n\n"
            "**Regla de oro:** el filtro exige estado `aprobado` **y** un "
            "revisor registrado. Sin ambos, no publica. Está cubierto por tests."),
        "si_falla": [
            "**No publica nada:** revisar en la hoja que los posts tengan "
            "estado `aprobado` Y la columna `revisor` con un nombre.",
            "**Error de token de Meta:** los tokens de página caducan cada 60 "
            "días. Regenerar en Meta for Developers y actualizar la credencial.",
            "**Publicó a destiempo:** revisar la zona horaria de la instancia "
            "de n8n (`GENERIC_TIMEZONE=America/Lima`).",
            "**Un post quedó en `fallido`:** corregir la causa y cambiar el "
            "estado de vuelta a `aprobado`; el workflow lo tomará en la "
            "siguiente corrida.",
            "**Nunca** cambiar el estado directamente a `publicado` a mano: se "
            "pierde el registro de qué se publicó realmente.",
        ],
    },
    {
        # El sistema de documentación se documenta a sí mismo.
        "archivo": ROOT / "workflows" / "workflow_bandeja.json",
        "salida": "ficha_bandeja_ia.md",
        "responsable": "Coordinación",
        "que_hace": (
            "Lee la bandeja de contacto del Club, pide a Claude que clasifique "
            "cada correo (inscripción, voluntariado, alianza, queja, "
            "administrativo, spam) y redacte un borrador de respuesta, y deja "
            "todo en una hoja priorizada. Si el correo es una queja, una "
            "propuesta de alianza o trae señales de urgencia, avisa al equipo "
            "por Telegram para que lo conteste una persona.\n\n"
            "**Ningún correo se responde solo:** el borrador siempre espera "
            "revisión. Si la API de Claude falla, un nodo de respaldo clasifica "
            "por reglas para que ningún correo se quede sin procesar."),
        "si_falla": [
            "**No entran correos:** revisar la credencial IMAP en n8n y que la "
            "casilla no haya cambiado de contraseña.",
            "**Todos los correos salen como `otro`:** probablemente Claude está "
            "fallando y entró el respaldo por reglas. Revisar la API key.",
            "**No llegan avisos de quejas:** revisar el chat ID de Telegram; el "
            "bot debe estar agregado al grupo.",
            "**Procesar la bandeja a mano mientras tanto:** "
            "`python scripts/simular_asistente.py` clasifica el lote sin n8n.",
        ],
    },
    {
        "archivo": ROOT / "workflows" / "workflow_reporte_semanal.json",
        "salida": "ficha_reporte_semanal.md",
        "responsable": "Coordinación",
        "que_hace": (
            "Cada lunes a las 08:00 lee los KPIs publicados por el dashboard, "
            "separa lo que mejoró de lo que bajó, arma la lista de qué revisar "
            "esa semana y envía el resumen por correo al equipo.\n\n"
            "**Por qué existe:** antes el resumen se armaba a mano los lunes y, "
            "cuando había mucho trabajo, simplemente no se hacía."),
        "si_falla": [
            "**No llegó el reporte del lunes:** revisar en n8n → Executions si "
            "el schedule corrió; si no, verificar que el workflow esté activo.",
            "**Error al leer los KPIs:** confirmar que la URL del dashboard "
            "responde y que `datos.json` se generó (workflow de GitHub Actions).",
            "**El reporte llegó vacío:** el `datos.json` existe pero sin KPIs; "
            "revisar el pipeline del proyecto 03.",
            "**Generarlo a mano:** `python scripts/simular_asistente.py` deja el "
            "reporte en `reportes/reporte_semanal.md`.",
        ],
    },
]


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    generadas, faltantes = [], []

    for wf in WORKFLOWS:
        ruta = Path(wf["archivo"])
        if not ruta.exists():
            faltantes.append(ruta)
            continue
        md = ficha_desde_archivo(
            ruta, que_hace=wf["que_hace"], si_falla=wf["si_falla"],
            responsable=wf["responsable"],
            ubicacion=f"n8n · instancia del Club STEM  \nWorkflow: `{ruta.name}`")
        destino = SALIDA / wf["salida"]
        destino.write_text(md, encoding="utf-8")
        generadas.append(destino)
        print(f"  ✓ {destino.relative_to(ROOT)}")

    print(f"\n✓ {len(generadas)} fichas generadas desde los workflows reales")
    if faltantes:
        print("\n No se encontraron estos workflows (¿ya construiste ese proyecto?):")
        for f in faltantes:
            print(f"   · {f}")
    print("\nRegenera las fichas cada vez que cambies un workflow:")
    print("  python scripts/generar_fichas.py")


if __name__ == "__main__":
    main()
