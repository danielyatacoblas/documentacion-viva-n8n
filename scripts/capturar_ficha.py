#!/usr/bin/env python3
"""Genera la captura de una ficha para el README.

Por qué existe: lo que impresiona de este proyecto es una ficha generada, y una
ficha es texto. Un video de texto no aporta nada sobre una imagen, así que se
captura.

Y por qué se renderiza aquí en vez de capturar la pantalla a mano: una captura
manual arrastra la barra de tareas, los marcadores del navegador y el tamaño
que tuviera la ventana ese día. Esta sale siempre igual, con el mismo ancho y
sin nada alrededor, y se puede regenerar cuando la ficha cambie.

Uso:  python scripts/capturar_ficha.py [ficha_leads.md]
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"

CHROME = [
    r"C:/Program Files/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

# Estilo sobrio, cercano al de GitHub: la captura debe parecerse a lo que ve
# quien abra el archivo en el repositorio.
PLANTILLA = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;
       background:#0d1117;color:#e6edf3;line-height:1.62;padding:34px 40px;
       -webkit-font-smoothing:antialiased}}
  .marco{{max-width:840px;margin:0 auto}}
  h1{{font-size:25px;font-weight:700;letter-spacing:-.02em;
     padding-bottom:9px;border-bottom:1px solid #30363d;margin-bottom:16px}}
  h2{{font-size:18px;font-weight:700;margin:26px 0 10px;
     padding-bottom:6px;border-bottom:1px solid #21262d}}
  h3{{font-size:15px;font-weight:700;margin:20px 0 8px}}
  p{{margin:9px 0;font-size:14.5px;color:#c9d1d9}}
  ul,ol{{margin:9px 0 9px 26px}}
  li{{margin:4px 0;font-size:14.5px;color:#c9d1d9}}
  strong{{color:#e6edf3;font-weight:700}}
  code{{background:#161b22;border:1px solid #30363d;border-radius:6px;
       padding:1px 6px;font-size:12.8px;
       font-family:ui-monospace,"Cascadia Mono",Consolas,monospace;color:#a5d6ff}}
  blockquote{{border-left:3px solid #3d444d;padding:2px 0 2px 15px;
       margin:12px 0;color:#8b949e}}
  blockquote p{{color:#8b949e;font-size:13.8px;margin:3px 0}}
  table{{border-collapse:collapse;margin:12px 0;font-size:13.8px;width:100%}}
  th,td{{border:1px solid #30363d;padding:7px 11px;text-align:left}}
  th{{background:#161b22;font-weight:700}}
  hr{{border:0;border-top:1px solid #30363d;margin:22px 0}}
  .pie{{margin-top:26px;padding-top:14px;border-top:1px solid #21262d;
       font-size:12px;color:#6e7681}}
</style></head><body><div class="marco">
{cuerpo}
<p class="pie">{pie}</p>
</div></body></html>
"""


def buscar_chrome() -> str | None:
    for c in CHROME:
        if Path(c).exists():
            return c
    return None


def main() -> int:
    nombre = sys.argv[1] if len(sys.argv) > 1 else "ficha_leads.md"
    origen = RAIZ / "fichas" / nombre
    if not origen.exists():
        print(f"No existe {origen}. Genera las fichas primero:")
        print("  python scripts/generar_fichas.py")
        return 1

    try:
        import mistune
    except ImportError:
        print("Falta mistune:  pip install mistune")
        return 1

    md = origen.read_text(encoding="utf-8")
    # escape=False porque las fichas usan <br> para separar las líneas de la
    # cabecera, igual que hace GitHub. Con el escapado por defecto la etiqueta
    # saldría como texto y la captura no se parecería al archivo del repo.
    html = mistune.create_markdown(escape=False, plugins=["table"])(md)
    pie = (f"Generada por scripts/generar_fichas.py leyendo el JSON del "
           f"workflow. Fuente: fichas/{nombre}")

    DOCS.mkdir(parents=True, exist_ok=True)
    temporal = DOCS / "_ficha.html"
    pagina = PLANTILLA.format(cuerpo=html, pie=pie)

    chrome = buscar_chrome()
    if not chrome:
        temporal.write_text(pagina, encoding="utf-8", newline="\n")
        print("No se encontró Chrome. El HTML quedó en", temporal)
        return 1

    # La altura se mide antes de capturar. Con una altura fija, una ficha algo
    # más larga sale cortada a media frase, y eso no se nota hasta verla ya
    # publicada en el README.
    sonda = ("<script>setTimeout(function(){document.title='ALTO'"
             "+document.body.scrollHeight},250)</script>")
    temporal.write_text(pagina + sonda, encoding="utf-8", newline="\n")
    medida = subprocess.run([
        chrome, "--headless=new", "--disable-gpu", "--window-size=1000,800",
        "--virtual-time-budget=4000", "--dump-dom", temporal.as_uri(),
    ], capture_output=True, text=True, timeout=120)
    encontrado = re.search(r"<title>ALTO(\d+)", medida.stdout)
    alto = int(encontrado.group(1)) + 24 if encontrado else 2200

    temporal.write_text(pagina, encoding="utf-8", newline="\n")
    salida = DOCS / f"{origen.stem}.png"
    subprocess.run([
        chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--window-size=1000,{alto}", "--force-prefers-reduced-motion",
        "--virtual-time-budget=4000",
        f"--screenshot={salida}", temporal.as_uri(),
    ], capture_output=True, timeout=120)

    temporal.unlink(missing_ok=True)
    if not salida.exists():
        print("Chrome no produjo la imagen.")
        return 1
    print(f"  {salida.relative_to(RAIZ)}  {salida.stat().st_size/1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
