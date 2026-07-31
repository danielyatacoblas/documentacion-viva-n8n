"""Tests del generador de fichas y del reporte semanal."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PORTAFOLIO = ROOT.parent
sys.path.insert(0, str(ROOT))

from src.fichas import analizar, describir_cron, generar_ficha  # noqa: E402
from src.reporte import (clasificar_kpis, puntos_de_atencion,  # noqa: E402
                         redactar)


# ═══════════════════════ FICHAS ═══════════════════════

WF = {
    "name": "Workflow de prueba",
    "nodes": [
        {"name": "Webhook", "type": "n8n-nodes-base.webhook",
         "parameters": {"httpMethod": "POST", "path": "lead"}},
        {"name": "Cada día", "type": "n8n-nodes-base.scheduleTrigger",
         "parameters": {"rule": {"interval": [
             {"field": "cronExpression", "expression": "0 8 * * *"}]}}},
        {"name": "Leer hoja", "type": "n8n-nodes-base.googleSheets",
         "parameters": {"documentId": {"value": "REEMPLAZAR_ID_HOJA"}},
         "notes": "Hoja CRM"},
        {"name": "Procesar", "type": "n8n-nodes-base.code",
         "parameters": {"jsCode": "return []"}},
        {"name": "Avisar", "type": "n8n-nodes-base.telegram",
         "parameters": {"chatId": "REEMPLAZAR_CHAT_ID"}, "onError": "continueErrorOutput"},
        {"name": "Huérfano", "type": "n8n-nodes-base.noOp", "parameters": {}},
    ],
    "connections": {
        "Webhook": {"main": [[{"node": "Leer hoja"}]]},
        "Leer hoja": {"main": [[{"node": "Procesar"}]]},
        "Cada día": {"main": [[{"node": "Avisar"}]]},
    },
    "tags": [{"name": "club-stem"}],
}


def test_detecta_los_disparadores_y_los_traduce():
    info = analizar(WF)
    detalles = " ".join(d["detalle"] for d in info["disparadores"])
    assert len(info["disparadores"]) == 2
    assert "POST /lead" in detalles
    assert "08:00" in detalles, "el cron debe traducirse a lenguaje humano"


def test_detecta_los_servicios_externos():
    info = analizar(WF)
    assert set(info["servicios"]) == {"Google Sheets", "Telegram"}


def test_detecta_los_parametros_pendientes_de_configurar():
    info = analizar(WF)
    assert info["pendientes"] == ["REEMPLAZAR_CHAT_ID", "REEMPLAZAR_ID_HOJA"]


def test_detecta_nodos_sin_manejo_de_error():
    info = analizar(WF)
    assert "Leer hoja" in info["sin_manejo_error"]
    assert "Avisar" not in info["sin_manejo_error"], "ese sí declara onError"


def test_el_orden_sigue_cada_cadena_completa_antes_de_la_siguiente():
    orden = analizar(WF)["orden"]
    # cadena del webhook completa, luego la del cron
    assert orden[:3] == ["Webhook", "Leer hoja", "Procesar"]
    assert orden[3:5] == ["Cada día", "Avisar"]


def test_los_nodos_huerfanos_aparecen_al_final():
    orden = analizar(WF)["orden"]
    assert orden[-1] == "Huérfano"
    assert len(orden) == len(WF["nodes"]), "ningún nodo se pierde"


@pytest.mark.parametrize("regla,esperado", [
    ({"interval": [{"field": "hours", "hoursInterval": 6}]}, "cada 6 horas"),
    ({"interval": [{"field": "minutes", "minutesInterval": 15}]}, "cada 15 minutos"),
    ({"interval": [{"field": "cronExpression", "expression": "0 8 * * *"}]},
     "todos los días a las 08:00"),
])
def test_traduce_las_reglas_de_programacion(regla, esperado):
    assert describir_cron({"rule": regla}) == esperado


def test_la_ficha_marca_lo_que_falta_escribir_a_mano():
    md = generar_ficha(analizar(WF))
    assert "pendiente de completar por una persona" in md
    assert "## 1. Qué hace" in md and "## 7. Qué hacer si falla" in md


def test_la_ficha_incluye_lo_extraido_automaticamente():
    md = generar_ficha(analizar(WF), que_hace="Hace X.", si_falla=["Revisar Y."])
    assert "Hace X." in md
    assert "Revisar Y." in md
    assert "Google Sheets" in md
    assert "REEMPLAZAR_ID_HOJA" in md
    assert "pendiente de completar" not in md, "ya no queda nada por escribir"


def test_las_fichas_del_portafolio_se_generan_de_workflows_reales():
    """Verifica contra los JSON reales de los proyectos 01 y 02."""
    import json
    ruta = PORTAFOLIO / "01_flujo_leads_n8n" / "workflows" / "workflow_leads.json"
    if not ruta.exists():
        pytest.skip("el proyecto 01 no está construido")
    info = analizar(json.loads(ruta.read_text(encoding="utf-8")))
    assert info["total_nodos"] >= 10
    assert "Google Sheets" in info["servicios"]
    assert info["disparadores"], "debe detectar al menos un disparador"


# ═══════════════════════ REPORTE ═══════════════════════

KPIS = [
    {"id": "leads", "etiqueta": "Leads generados", "valor": 226,
     "variacion": 3.7, "unidad": "", "mejor": "arriba"},
    {"id": "clics", "etiqueta": "Clics de email", "valor": 4.1,
     "variacion": -24.0, "unidad": "%", "mejor": "arriba"},
    {"id": "alcance", "etiqueta": "Alcance en redes", "valor": 79478,
     "variacion": 5.5, "unidad": "", "mejor": "arriba"},
    {"id": "respuesta", "etiqueta": "Días a primera respuesta", "valor": 0.9,
     "variacion": -20.0, "unidad": " días", "mejor": "abajo"},
]
DATOS = {"kpis": KPIS, "periodo": {"desde": "2026-05-02", "hasta": "2026-07-30",
                                   "dias_kpi": 30},
         "desgloses": {"conversion_por_canal": {"referido": 66.7, "facebook": 20.9}}}


def test_clasifica_mejoras_caidas_y_estables():
    g = clasificar_kpis(KPIS)
    ids = lambda xs: {k["id"] for k in xs}  # noqa: E731
    assert "clics" in ids(g["caidas"])
    assert "alcance" in ids(g["mejoras"])
    assert "leads" in ids(g["estables"]), "3.7 % está por debajo del umbral"


def test_una_baja_es_buena_cuando_menos_es_mejor():
    """El tiempo de respuesta bajando es una MEJORA, no una caída."""
    g = clasificar_kpis(KPIS)
    assert any(k["id"] == "respuesta" for k in g["mejoras"])
    assert not any(k["id"] == "respuesta" for k in g["caidas"])


def test_los_puntos_de_atencion_traen_recomendacion_concreta():
    p = puntos_de_atencion(KPIS)
    assert any("Clics de email" in x for x in p)
    assert any("llamado a la acción" in x for x in p), "debe decir qué hacer"


def test_no_marca_como_problema_una_mejora():
    p = puntos_de_atencion(KPIS)
    assert not any("Alcance" in x for x in p)
    assert not any("respuesta" in x.lower() for x in p)


def test_el_reporte_tiene_las_secciones_esperadas():
    md = redactar(DATOS, date(2026, 8, 3))
    for seccion in ("Lo que mejoró", "Lo que bajó", "Qué revisar esta semana",
                    "Dato de la semana"):
        assert seccion in md, f"falta la sección: {seccion}"


def test_el_reporte_no_inventa_numeros():
    md = redactar(DATOS, date(2026, 8, 3))
    assert "226" in md
    assert "79 478" in md or "79478" in md
    assert "-24.0 %" in md


def test_el_reporte_siempre_dice_algo_util_aunque_todo_este_bien():
    datos_ok = {**DATOS, "kpis": [k for k in KPIS if k["variacion"] > 0]}
    md = redactar(datos_ok, date(2026, 8, 3))
    assert "Qué revisar esta semana" in md
    assert "probar algo nuevo" in md, "sin problemas, debe proponer un experimento"
