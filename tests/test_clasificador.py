"""Tests del clasificador de correos.

El test crítico es `test_quejas_y_alianzas_siempre_requieren_persona`:
convierte en garantía verificable la regla de que la IA propone pero no
responde sola los casos sensibles.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.clasificador import (CATEGORIAS, clasificar,  # noqa: E402
                              clasificar_lote, ordenar_bandeja)


def correo(asunto, cuerpo, remitente="persona@correo.com"):
    return {"id": "M1", "asunto": asunto, "cuerpo": cuerpo,
            "remitente": remitente, "nombre": "Ana"}


# ── categorización ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("asunto,cuerpo,esperado", [
    ("Consulta", "Quiero inscribir a mi hija en el taller de robótica", "inscripcion"),
    ("Vacantes", "¿Quedan cupos para el curso de agosto?", "inscripcion"),
    ("Hola", "Me gustaría ser voluntario los sábados", "voluntariado"),
    ("Propuesta", "Represento una empresa y queremos auspiciar sus programas", "alianza"),
    ("Donación", "Quisiera donar equipos de cómputo", "alianza"),
    ("Reclamo", "Es inaceptable, nadie responde mis correos", "queja"),
    ("Factura", "Necesito la boleta del pago, mi RUC es 20123", "administrativo"),
    ("Oferta", "SEO garantizado, haga clic aquí para una oferta única", "spam"),
    ("Hola", "Buenas tardes, ¿dónde están ubicados?", "otro"),
])
def test_categoriza_correctamente(asunto, cuerpo, esperado):
    c = clasificar(correo(asunto, cuerpo))
    assert c.categoria == esperado


def test_la_categoria_siempre_es_del_catalogo():
    c = clasificar(correo("xyz", "texto sin señales reconocibles"))
    assert c.categoria in CATEGORIAS


def test_ignora_tildes_y_mayusculas():
    c = clasificar(correo("INSCRIPCIÓN", "QUIERO INSCRIBIR A MI HIJO"))
    assert c.categoria == "inscripcion"


# ── la regla crítica ────────────────────────────────────────────────────────

def test_quejas_y_alianzas_siempre_requieren_persona():
    queja = clasificar(correo("Reclamo", "Esto es inaceptable, muy mal servicio"))
    alianza = clasificar(correo("Alianza", "Queremos auspiciar como empresa"))
    assert queja.requiere_humano is True
    assert alianza.requiere_humano is True


def test_lo_urgente_requiere_persona_aunque_sea_una_consulta_simple():
    c = clasificar(correo("Consulta", "Necesito saber urgente si hay vacante"))
    assert c.urgente is True
    assert c.requiere_humano is True


def test_una_consulta_normal_no_requiere_persona():
    c = clasificar(correo("Consulta", "¿Cuáles son los horarios del taller?"))
    assert c.requiere_humano is False
    assert c.borrador, "debe traer un borrador listo para revisar"


def test_el_spam_no_genera_borrador_de_respuesta():
    c = clasificar(correo("Oferta", "Gane dinero con criptomonedas, haga clic aquí"))
    assert c.categoria == "spam"
    assert c.borrador == "", "no se responde spam"


# ── prioridad ───────────────────────────────────────────────────────────────

def test_las_quejas_son_prioridad_alta():
    assert clasificar(correo("Reclamo", "pésimo servicio, quiero un reembolso")).prioridad == "alta"


def test_el_spam_es_prioridad_baja():
    assert clasificar(correo("Oferta", "préstamo sin aval, gane dinero")).prioridad == "baja"


def test_las_inscripciones_son_prioridad_media():
    assert clasificar(correo("Consulta", "quiero inscribir a mi hijo")).prioridad == "media"


# ── borradores ──────────────────────────────────────────────────────────────

def test_el_borrador_usa_el_nombre_del_remitente():
    c = clasificar({"id": "M1", "asunto": "Consulta", "nombre": "María",
                    "cuerpo": "quiero inscribir a mi hija", "remitente": "m@x.com"})
    assert "María" in c.borrador


def test_el_borrador_de_queja_pide_detalles_y_no_promete_nada():
    c = clasificar(correo("Reclamo", "esto es inaceptable"))
    assert "?" in c.borrador, "debe preguntar para entender qué pasó"


# ── bandeja ordenada ────────────────────────────────────────────────────────

def test_ordenar_bandeja_pone_lo_urgente_arriba_y_el_spam_abajo():
    correos = [
        correo("Consulta", "¿dónde están ubicados?"),
        correo("Oferta", "SEO garantizado, haga clic aquí"),
        correo("Reclamo", "es inaceptable, nadie responde"),
    ]
    for i, c in enumerate(correos):
        c["id"] = f"M{i}"
    orden = ordenar_bandeja(clasificar_lote(correos))
    assert orden[0].categoria == "queja", "la queja va primero"
    assert orden[-1].categoria == "spam", "el spam va al final"


def test_lote_procesa_toda_la_bandeja_ficticia():
    import json
    p = ROOT / "data" / "correos.json"
    if not p.exists():
        pytest.skip("corre antes: python scripts/generar_correos.py")
    correos = json.loads(p.read_text(encoding="utf-8"))
    res = clasificar_lote(correos)
    assert len(res) == len(correos)
    assert all(c.categoria in CATEGORIAS for c in res)
    assert any(c.categoria == "queja" for c in res), "la data trae quejas"
    assert any(c.categoria == "spam" for c in res), "la data trae spam"
    assert any(c.requiere_humano for c in res)
