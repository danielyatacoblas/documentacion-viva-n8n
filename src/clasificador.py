"""Bandeja de entrada inteligente: clasifica correos y propone respuesta.

Dos motores intercambiables (igual que el proyecto 02):
  - "reglas" (por defecto): 100 % offline y determinista. Palabras clave +
    señales de urgencia. Permite evaluar todo sin API key.
  - "claude": usa la API de Anthropic si hay ANTHROPIC_API_KEY.

La IA **propone**; la persona decide. Ningún correo se responde solo: el
resultado es siempre un borrador con su categoría y prioridad.
"""
from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass, field

CATEGORIAS = ("inscripcion", "voluntariado", "alianza", "queja",
              "administrativo", "spam", "otro")

PRIORIDADES = ("alta", "media", "baja")


def _sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


# ── señales por categoría (orden = prioridad de match) ──────────────────────

_SENALES = {
    "queja": ("queja", "reclamo", "molest", "pesim", "mal servicio", "denunc",
              "inaceptable", "devolucion", "reembolso"),
    "alianza": ("alianza", "auspicio", "sponsor", "convenio", "rse",
                "responsabilidad social", "donacion", "donar", "empresa"),
    "voluntariado": ("voluntari", "ser mentor", "quiero ayudar", "colaborar",
                     "apoyar como"),
    "inscripcion": ("inscri", "matricul", "vacante", "cupo", "taller",
                    "horario", "clase", "curso", "costo", "precio", "mi hijo",
                    "mi hija"),
    "administrativo": ("factura", "boleta", "ruc", "comprobante", "pago",
                       "transferencia", "cotizacion", "proveedor"),
    "spam": ("posicionamiento web", "seo garantizado", "prestamo", "casino",
             "criptomoneda", "gane dinero", "haga clic aqui", "oferta unica"),
}

_URGENTES = ("urgente", "hoy mismo", "manana", "cuanto antes", "de inmediato",
             "ya paso", "sigo esperando", "es la tercera vez", "nadie responde")

_RESPUESTAS = {
    "inscripcion": ("¡Hola {nombre}! Gracias por escribirnos. Te comparto la "
                    "información de nuestros talleres: fechas, horarios y el "
                    "enlace de inscripción. Cualquier duda quedo atenta."),
    "voluntariado": ("¡Hola {nombre}! Nos alegra mucho tu interés en ser "
                     "voluntario/a. Te cuento cómo funciona el programa y "
                     "cuándo es el próximo onboarding."),
    "alianza": ("Estimado/a {nombre}, gracias por su interés en apoyar al "
                "Club STEM. Le comparto nuestra presentación institucional y "
                "las modalidades de colaboración disponibles."),
    "queja": ("Estimado/a {nombre}, lamento mucho la situación. Quiero "
              "entender bien qué ocurrió para poder resolverlo: ¿podría "
              "contarme en qué taller y fecha sucedió?"),
    "administrativo": ("Hola {nombre}, recibimos su solicitud. La derivo al "
                       "área administrativa y le respondemos con el documento "
                       "solicitado."),
    "spam": "",
    "otro": ("¡Hola {nombre}! Gracias por escribirnos al Club STEM. Un miembro "
             "del equipo revisará tu mensaje y te responderá pronto."),
}


@dataclass
class Clasificacion:
    id: str
    remitente: str
    asunto: str
    categoria: str
    prioridad: str
    urgente: bool
    requiere_humano: bool
    borrador: str
    senales: list[str] = field(default_factory=list)
    motor: str = "reglas"


# ── motor de reglas ─────────────────────────────────────────────────────────

def clasificar_con_reglas(correo: dict) -> Clasificacion:
    texto = _sin_tildes(f"{correo.get('asunto', '')} {correo.get('cuerpo', '')}")
    nombre = (correo.get("nombre") or
              (correo.get("remitente", "").split("@")[0].split(".")[0].title()) or
              "hola")

    categoria, senales = "otro", []
    for cat, claves in _SENALES.items():          # dict ordenado = prioridad
        encontradas = [k for k in claves if k in texto]
        if encontradas:
            categoria, senales = cat, encontradas
            break

    urgente = any(u in texto for u in _URGENTES)

    # prioridad: quejas y urgencias arriba; spam abajo
    if categoria == "spam":
        prioridad = "baja"
    elif categoria == "queja" or urgente:
        prioridad = "alta"
    elif categoria in ("inscripcion", "alianza"):
        prioridad = "media"
    else:
        prioridad = "baja"

    # una queja o una alianza SIEMPRE la contesta una persona
    requiere_humano = categoria in ("queja", "alianza") or urgente

    plantilla = _RESPUESTAS.get(categoria, _RESPUESTAS["otro"])
    borrador = plantilla.format(nombre=nombre) if plantilla else ""

    return Clasificacion(
        id=correo.get("id", ""), remitente=correo.get("remitente", ""),
        asunto=correo.get("asunto", ""), categoria=categoria,
        prioridad=prioridad, urgente=urgente, requiere_humano=requiere_humano,
        borrador=borrador, senales=senales, motor="reglas")


# ── motor Claude (opcional) ─────────────────────────────────────────────────

PROMPT = """Eres asistente del Club STEM, una organización peruana de educación
en ciencia y tecnología para niñas y niños.

Clasifica este correo entrante y redacta un borrador de respuesta.

De: {remitente}
Asunto: {asunto}
Mensaje:
\"\"\"
{cuerpo}
\"\"\"

Categorías posibles: inscripcion, voluntariado, alianza, queja, administrativo,
spam, otro.

Reglas:
- Si es una queja o una propuesta de alianza, marca requiere_humano = true.
- No inventes fechas, precios ni cupos: si el correo los pide, redacta el
  borrador dejando esos datos como [COMPLETAR].
- El borrador va en español de Perú, cordial y breve (máximo 6 líneas).

Responde SOLO con un JSON válido con estas claves exactas:
{{"categoria": "...", "prioridad": "alta|media|baja", "urgente": true|false,
  "requiere_humano": true|false, "borrador": "..."}}"""


def clasificar_con_claude(correo: dict, modelo: str = "claude-sonnet-5") -> Clasificacion:
    import json as _json

    from anthropic import Anthropic

    cliente = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = cliente.messages.create(
        model=modelo, max_tokens=700,
        messages=[{"role": "user", "content": PROMPT.format(
            remitente=correo.get("remitente", ""),
            asunto=correo.get("asunto", ""),
            cuerpo=correo.get("cuerpo", ""))}])
    texto = "".join(b.text for b in resp.content
                    if getattr(b, "type", "") == "text").strip()
    bloque = re.search(r"\{.*\}", texto, re.S)
    datos = _json.loads(bloque.group(0)) if bloque else {}

    cat = datos.get("categoria", "otro")
    return Clasificacion(
        id=correo.get("id", ""), remitente=correo.get("remitente", ""),
        asunto=correo.get("asunto", ""),
        categoria=cat if cat in CATEGORIAS else "otro",
        prioridad=datos.get("prioridad", "media"),
        urgente=bool(datos.get("urgente")),
        requiere_humano=bool(datos.get("requiere_humano")),
        borrador=datos.get("borrador", ""), senales=[], motor="claude")


# ── API pública ─────────────────────────────────────────────────────────────

def clasificar(correo: dict, motor: str = "reglas") -> Clasificacion:
    if motor == "claude":
        try:
            return clasificar_con_claude(correo)
        except Exception as e:      # noqa: BLE001 — si la IA falla, no se pierde el correo
            c = clasificar_con_reglas(correo)
            c.motor = f"reglas (respaldo: {type(e).__name__})"
            return c
    return clasificar_con_reglas(correo)


def clasificar_lote(correos: list[dict], motor: str = "reglas") -> list[Clasificacion]:
    return [clasificar(c, motor) for c in correos]


def ordenar_bandeja(clasificados: list[Clasificacion]) -> list[Clasificacion]:
    """Orden de atención: prioridad, luego los que exigen persona, luego spam al final."""
    peso = {"alta": 0, "media": 1, "baja": 2}
    return sorted(clasificados,
                  key=lambda c: (c.categoria == "spam", peso.get(c.prioridad, 3),
                                 not c.requiere_humano))
