#!/usr/bin/env python3
"""Corre las tres automatizaciones de IA sobre la data ficticia.

    python scripts/generar_correos.py
    python scripts/simular_asistente.py                # motor de reglas (offline)
    python scripts/simular_asistente.py --motor claude # usa ANTHROPIC_API_KEY

Salidas:
    data/bandeja_clasificada.csv   ← la bandeja priorizada con borradores
    reportes/reporte_semanal.md    ← el resumen ejecutivo del lunes
    fichas/                        ← documentación viva (script aparte)
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PORTAFOLIO = ROOT.parent
sys.path.insert(0, str(ROOT))

from src.clasificador import clasificar_lote, ordenar_bandeja  # noqa: E402
from src.reporte import redactar  # noqa: E402

CORREOS = ROOT / "data" / "correos.json"
DATOS_KPI = PORTAFOLIO / "03_dashboard_kpis" / "public" / "datos.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--motor", default="reglas", choices=["reglas", "claude"])
    args = ap.parse_args()

    print("=== Asistente IA del Club STEM (simulación local) ===\n")

    # ── 1. Bandeja de entrada ──
    if not CORREOS.exists():
        raise SystemExit("Primero corre: python scripts/generar_correos.py")
    correos = json.loads(CORREOS.read_text(encoding="utf-8"))
    clasificados = ordenar_bandeja(clasificar_lote(correos, motor=args.motor))

    cats = Counter(c.categoria for c in clasificados)
    prios = Counter(c.prioridad for c in clasificados)
    humanos = sum(1 for c in clasificados if c.requiere_humano)
    spam = cats.get("spam", 0)
    con_borrador = sum(1 for c in clasificados if c.borrador)

    print(f"1) BANDEJA DE ENTRADA · motor: {args.motor}")
    print(f"   Correos procesados: {len(clasificados)}")
    print(f"   Por categoría: " + ", ".join(f"{k}={v}" for k, v in cats.most_common()))
    print(f"   Prioridad alta: {prios.get('alta', 0)} · media: {prios.get('media', 0)}"
          f" · baja: {prios.get('baja', 0)}")
    print(f"   Requieren persona sí o sí: {humanos} (quejas, alianzas y urgencias)")
    print(f"   Spam filtrado: {spam}")
    print(f"   Borradores listos para revisar: {con_borrador}")

    print("\n   Primeros 3 de la cola (así los vería el equipo):")
    for c in clasificados[:3]:
        marca = "👤 requiere persona" if c.requiere_humano else "🤖 borrador listo"
        print(f"     [{c.prioridad.upper():<5}] {c.categoria:<14} {marca}")
        print(f"             «{c.asunto}»")

    filas = [{"id": c.id, "prioridad": c.prioridad, "categoria": c.categoria,
              "urgente": int(c.urgente), "requiere_humano": int(c.requiere_humano),
              "remitente": c.remitente, "asunto": c.asunto,
              "borrador": c.borrador.replace("\n", " "), "motor": c.motor}
             for c in clasificados]
    salida_bandeja = ROOT / "data" / "bandeja_clasificada.csv"
    with salida_bandeja.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        wr.writeheader(); wr.writerows(filas)

    # ── 2. Reporte semanal ──
    print(f"\n2) REPORTE SEMANAL")
    if DATOS_KPI.exists():
        datos = json.loads(DATOS_KPI.read_text(encoding="utf-8"))
        md = redactar(datos, date(2026, 8, 3))
        destino = ROOT / "reportes" / "reporte_semanal.md"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(md, encoding="utf-8")
        lineas = [l for l in md.splitlines() if l.startswith("###")]
        print(f"   Generado desde el dashboard del proyecto 03")
        print(f"   Secciones: {', '.join(l.replace('### ', '') for l in lineas)}")
        print(f"   ✓ {destino.relative_to(ROOT)}")
    else:
        print("   ⚠ No se encontró el datos.json del proyecto 03.")
        print("     Corre primero: cd ../03_dashboard_kpis && "
              "python scripts/construir_dashboard.py")

    # ── 3. Documentación viva ──
    print(f"\n3) DOCUMENTACIÓN VIVA")
    fichas = sorted((ROOT / "fichas").glob("*.md")) if (ROOT / "fichas").exists() else []
    if fichas:
        print(f"   {len(fichas)} fichas generadas desde los workflows reales:")
        for f in fichas:
            print(f"     · {f.name}")
    else:
        print("   Corre: python scripts/generar_fichas.py")

    print(f"\n✓ {salida_bandeja.relative_to(ROOT)} ({len(filas)} correos priorizados)")


if __name__ == "__main__":
    main()
