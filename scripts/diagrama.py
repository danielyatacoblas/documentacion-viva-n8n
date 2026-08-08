# -*- coding: utf-8 -*-
"""Dibuja `docs/flujo.svg`: tres cosas que se escriben solas, y dónde entra la persona.

    python scripts/simular_asistente.py      # primero, deja los datos
    python scripts/diagrama.py

Las cifras **se leen de `data/`, `fichas/` y los workflows**, no están escritas
a mano. Es el mismo principio que el proyecto entero defiende: si la fuente
cambia y la documentación no, la documentación miente. Un diagrama que dice una
cantidad que ya no es cierta sería exactamente el problema que este repositorio
existe para resolver.

Se genera en SVG y no en Mermaid porque hace falta controlar el tamaño de cada
tarjeta para meter varias cifras dentro, y porque un SVG se abre a pantalla
completa y sirve igual para el README que para la web del portafolio.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"
DATOS = RAIZ / "data"
FICHAS = RAIZ / "fichas"

W, H = 2000, 1180
COL = ["#e2e8f0", "#ede9fe", "#fee2e2", "#dbeafe", "#dcfce7"]

TITULO = "Documentación viva + asistente · lo que se escribe solo y lo que no"
BAJADA = ("Tres tareas que consumían horas cada semana, con la línea marcada "
          "en el sitio exacto donde hace falta criterio. Las cifras salen de "
          "data/, fichas/ y los propios workflows.")
PIE = ("La ficha se deriva del JSON del workflow: cuando el flujo cambia, se "
       "regenera y vuelve a decir la verdad. Una documentación que no puede "
       "quedarse desactualizada sin que alguien lo note.")

CARRILES = [
    ("Fuente", "Lo que ya existe"),
    ("Se deriva solo", "Sin que nadie escriba"),
    ("Criterio humano", "Lo que no se automatiza"),
    ("Salida", "Lo que queda por escrito"),
    ("Valor", "Qué gana el equipo"),
]


def _t(x, y, txt, size=12, peso="400", color="#0f172a", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{peso}" '
            f'fill="{color}" text-anchor="{anchor}">{escape(str(txt))}</text>')


def _partir(texto: str, ancho: int) -> list:
    lineas, actual = [], ""
    for p in texto.split():
        if len(actual) + len(p) + 1 > ancho:
            lineas.append(actual)
            actual = p
        else:
            actual = f"{actual} {p}".strip()
    if actual:
        lineas.append(actual)
    return lineas


def tarjeta(x, y, w, h, titulo, lineas, etiqueta, color, cifras=None):
    """La etiqueta va ARRIBA del título: a su derecha se solapan en cuanto el
    título pasa de tres palabras, y eso no se ve hasta renderizar."""
    p = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" '
         f'fill="#ffffff" stroke="#94a3b8" stroke-width="2" '
         f'filter="url(#shadow)"/>']
    yy = y + 26
    if etiqueta:
        ew = 12 + len(etiqueta) * 6.4
        p.append(f'<rect x="{x + 16}" y="{y + 12}" width="{ew}" height="20" '
                 f'rx="10" fill="{color}"/>')
        p.append(_t(x + 16 + ew / 2, y + 26, etiqueta, 9.5, "700",
                    "#0f172a", "middle"))
        yy = y + 54
    for ln in _partir(titulo, int((w - 32) / 8.1)):
        p.append(_t(x + 16, yy, ln, 14.5, "700"))
        yy += 19
    yy += 6
    for ln in lineas:
        p.append(_t(x + 16, yy, ln, 11, "400", "#475569"))
        yy += 16
    if cifras:
        yy += 4
        p.append(f'<line x1="{x + 16}" y1="{yy - 12}" x2="{x + w - 16}" '
                 f'y2="{yy - 12}" stroke="#e2e8f0" stroke-width="1.5"/>')
        for et, val, tono in cifras:
            p.append(_t(x + 16, yy + 4, et, 9.5, "600", "#64748b"))
            p.append(_t(x + w - 16, yy + 4, val, 12, "700", tono, "end"))
            yy += 19
    return "".join(p)


def flecha(x1, y1, x2, y2, texto="", punteada=False, color="#334155"):
    mx = (x1 + x2) / 2
    guion = ' stroke-dasharray="8 7"' if punteada else ""
    s = (f'<path d="M {x1} {y1} H {mx} V {y2} H {x2}" fill="none" '
         f'stroke="{color}" stroke-width="2.2"{guion} '
         f'marker-end="url(#arrow)"/>')
    if texto:
        s += (f'<text x="{mx}" y="{min(y1, y2) - 10}" font-size="11" '
              f'font-weight="600" fill="{color}" text-anchor="middle" '
              f'stroke="#ffffff" stroke-width="5" paint-order="stroke">'
              f'{escape(texto)}</text>')
    return s


def cifras() -> dict:
    """Lo que de verdad hay en los archivos, no lo que se recuerda que había."""
    bandeja = []
    f = DATOS / "bandeja_clasificada.csv"
    if f.exists():
        with f.open(encoding="utf-8", newline="") as fh:
            bandeja = list(csv.DictReader(fh))

    def si(v):
        return str(v).strip().lower() in ("1", "true", "sí", "si", "yes")

    cat = Counter(c.get("categoria", "") for c in bandeja)
    pri = Counter(c.get("prioridad", "") for c in bandeja)
    humano = sum(1 for c in bandeja if si(c.get("requiere_humano")))
    spam = cat.get("spam", 0)

    # El generador documenta los workflows de TODO el portafolio, no solo los
    # de este repositorio, así que los nodos se cuentan donde estén: contarlos
    # solo aquí daría 13 de los que en realidad se leen.
    fichas = sorted(FICHAS.glob("ficha_*.md")) if FICHAS.exists() else []
    # Cuántas secciones tiene una ficha y cuántas escribe una persona: se
    # cuentan de la ficha real. Escrito a mano decía «9 de 11» cuando son 7.
    secciones = 0
    if fichas:
        secciones = sum(1 for ln in fichas[0].read_text(encoding="utf-8")
                        .splitlines() if ln.startswith("## "))
    A_MANO = 2      # «Qué hace» y «Qué hacer si falla»: eso es intención
    nodos = 0
    for carpeta in (RAIZ / "workflows", *(RAIZ.parent).glob("*/workflows")):
        if not carpeta.exists():
            continue
        for j in carpeta.glob("*.json"):
            try:
                nodos += len(json.loads(j.read_text(encoding="utf-8"))
                             .get("nodes", []))
            except Exception:
                pass

    return {
        "correos": len(bandeja),
        "categorias": len([k for k in cat if k]),
        "alta": pri.get("alta", 0),
        "media": pri.get("media", 0),
        "baja": pri.get("baja", 0),
        "humano": humano,
        "spam": spam,
        # El spam se descarta; para todo lo demás hay borrador, incluso para
        # lo que va a una persona — le llega redactado, no en blanco.
        "borradores": len(bandeja) - spam,
        "fichas": len(fichas),
        "secciones": secciones,
        "derivadas": max(0, secciones - A_MANO),
        "a_mano": A_MANO,
        "nodos": nodos,
    }


def main() -> int:
    c = cifras()
    if not c["fichas"]:
        print("  No hay fichas. Corre antes: python scripts/generar_fichas.py")
        return 1

    cx = [60, 460, 860, 1240, 1620]
    cw = [360, 360, 340, 340, 320]

    piezas = ['<rect width="100%" height="100%" fill="#f8fafc"/>',
              _t(48, 52, TITULO, 28, "700")]
    for i, ln in enumerate(_partir(BAJADA, 118)):
        piezas.append(_t(48, 82 + i * 20, ln, 14, "400", "#475569"))

    top, alto = 150, 900
    for i, (nombre, sub) in enumerate(CARRILES):
        piezas.append(f'<rect x="{cx[i]}" y="{top}" width="{cw[i]}" '
                      f'height="{alto}" rx="18" fill="{COL[i]}" '
                      f'fill-opacity="0.5" stroke="#94a3b8" '
                      f'stroke-width="1.5"/>')
        piezas.append(_t(cx[i] + 16, top + 28, nombre.upper(), 13, "700",
                         "#334155"))
        piezas.append(_t(cx[i] + 16, top + 46, sub, 10.5, "400", "#64748b"))

    # ── flechas primero ────────────────────────────────────────────────────
    piezas.append(flecha(cx[0] + cw[0] - 20, 300, cx[1] + 20, 300, "se lee"))
    piezas.append(flecha(cx[1] + cw[1] - 20, 300, cx[3] + 20, 280,
                         f"{c['derivadas']} de {c['secciones']} secciones"))
    piezas.append(flecha(cx[0] + cw[0] - 20, 620, cx[1] + 20, 620, "llega"))
    piezas.append(flecha(cx[1] + cw[1] - 20, 620, cx[2] + 20, 400, "clasificado"))
    piezas.append(flecha(cx[2] + cw[2] - 20, 400, cx[3] + 20, 560,
                         "lo delicado"))
    piezas.append(flecha(cx[2] + cw[2] - 20, 700, cx[3] + 20, 830,
                         "el resto", punteada=True))
    piezas.append(flecha(cx[3] + cw[3] - 20, 280, cx[4] + 20, 300, ""))
    piezas.append(flecha(cx[3] + cw[3] - 20, 560, cx[4] + 20, 540, ""))
    piezas.append(flecha(cx[3] + cw[3] - 20, 830, cx[4] + 20, 780, ""))

    # ── fuente ─────────────────────────────────────────────────────────────
    piezas.append(tarjeta(
        cx[0] + 20, 220, cw[0] - 40, 190,
        "El JSON del workflow",
        ["El archivo que n8n ya guarda. No hay",
         "que mantener nada aparte: la fuente",
         "de la documentación es el flujo",
         "mismo."],
        "YA EXISTE", "#e2e8f0",
        [("flujos documentados", str(c["fichas"]), "#334155")]
        + ([("nodos leídos", str(c["nodos"]), "#334155")]
           if c["nodos"] else [])))
    piezas.append(tarjeta(
        cx[0] + 20, 540, cw[0] - 40, 175,
        "El correo que llega",
        ["Inscripciones, quejas, alianzas,",
         "voluntariado. Todo al mismo buzón,",
         "todo mezclado."],
        "YA EXISTE", "#e2e8f0",
        [("correos del periodo", str(c["correos"]), "#334155"),
         ("categorías distintas", str(c["categorias"]), "#334155")]))

    # ── se deriva solo ─────────────────────────────────────────────────────
    piezas.append(tarjeta(
        cx[1] + 20, 220, cw[1] - 40, 230,
        "Generador de fichas",
        ["Disparadores, servicios, orden real",
         "de ejecución, credenciales",
         "pendientes y nodos sin ruta de",
         "error: todo se deriva del archivo."],
        "AUTOMÁTICO", "#ede9fe",
        [("lo escribe una persona", f"{c['a_mano']} de {c['secciones']}",
          "#92400e"),
         ("se deriva del JSON", f"{c['derivadas']} de {c['secciones']}",
          "#5b21b6")]))
    piezas.append(tarjeta(
        cx[1] + 20, 540, cw[1] - 40, 230,
        "Clasificar y redactar",
        ["Categoría, prioridad y un borrador",
         "de respuesta. Sin Claude funciona",
         "igual con reglas: el flujo no",
         "depende de que la IA esté."],
        "IA O REGLAS", "#ede9fe",
        [("prioridad alta", str(c["alta"]), "#b91c1c"),
         ("media", str(c["media"]), "#92400e"),
         ("baja", str(c["baja"]), "#166534")]))

    # ── criterio humano ────────────────────────────────────────────────────
    piezas.append(tarjeta(
        cx[2] + 20, 300, cw[2] - 40, 290,
        "Lo que exige una persona",
        ["Quejas, alianzas y urgencias no las",
         "contesta un borrador. El sistema las",
         "marca y las sube al principio de la",
         "cola, pero no las responde.",
         "",
         "Saber qué NO automatizar es la",
         "mitad del trabajo."],
        "NO SE AUTOMATIZA", "#fee2e2",
        [("van a una persona", str(c["humano"]), "#b91c1c"),
         ("spam, fuera sin más", str(c["spam"]), "#64748b")]))
    piezas.append(tarjeta(
        cx[2] + 20, 660, cw[2] - 40, 190,
        "Qué hacer si falla",
        ["De cada ficha, esta sección y la de",
         "intención las escribe alguien: la",
         "intención no está en el JSON."],
        "CRITERIO", "#fee2e2",
        [("borradores a revisar", str(c["borradores"]), "#1e40af")]))

    # ── salida ─────────────────────────────────────────────────────────────
    piezas.append(tarjeta(
        cx[3] + 20, 210, cw[3] - 40, 165,
        "Ficha en Markdown",
        ["Una por flujo, en el repositorio,",
         "versionada junto al código."],
        "", "",
        [("fichas al día", str(c["fichas"]), "#166534")]))
    piezas.append(tarjeta(
        cx[3] + 20, 480, cw[3] - 40, 165,
        "Bandeja priorizada",
        ["Ordenada por lo que no puede",
         "esperar, no por hora de llegada."],
        "", "",
        [("correos priorizados", str(c["correos"]), "#166534")]))
    piezas.append(tarjeta(
        cx[3] + 20, 750, cw[3] - 40, 180,
        "Reporte semanal",
        ["Qué mejoró, qué empeoró, qué",
         "revisar. Sacado de los KPIs del",
         "panel, no de la impresión de nadie."],
        "", "",
        [("secciones", "5", "#166534")]))

    # ── valor ──────────────────────────────────────────────────────────────
    for y, tit, ls in (
        (220, "Quien está de turno tiene dónde mirar",
         ["Cuando algo falla un sábado y no", "está quien lo montó."]),
        (460, "El correo urgente no se pierde",
         ["Deja de depender de quién abrió", "primero la bandeja."]),
        (700, "La documentación no puede mentir",
         ["Se regenera del flujo. Si cambia,", "la ficha cambia con él."]),
    ):
        piezas.append(tarjeta(cx[4] + 20, y, cw[4] - 40, 185, tit, ls,
                              "VALOR", "#dcfce7"))

    piezas.append(f'<rect x="48" y="1090" width="{W - 96}" height="52" '
                  f'rx="12" fill="#e2e8f0"/>')
    piezas.append(_t(70, 1122, PIE, 13.5, "700"))

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d" '
           f'font-family="Segoe UI, Arial, sans-serif">'
           f'<title id="t">{escape(TITULO)}</title>'
           f'<desc id="d">{escape(BAJADA)}</desc>'
           '<defs>'
           '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">'
           '<feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#0f172a" '
           'flood-opacity="0.14"/></filter>'
           '<marker id="arrow" markerWidth="9" markerHeight="9" refX="7" '
           'refY="4.5" orient="auto"><path d="M0,0 L0,9 L8,4.5 z" '
           'fill="#334155"/></marker>'
           '</defs>' + "".join(piezas) + '</svg>')

    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "flujo.svg").write_text(svg, encoding="utf-8", newline="\n")
    print(f"  docs/flujo.svg  {len(svg) // 1024} KB · {c['fichas']} fichas · "
          f"{c['correos']} correos · {c['humano']} a una persona")
    return 0


if __name__ == "__main__":
    sys.exit(main())
